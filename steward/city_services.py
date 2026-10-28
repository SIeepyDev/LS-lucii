#!/usr/bin/env python3
"""Lucii City Services: light read-only supervisors, forensic receipts, workorders."""
import datetime as dt, hashlib, json, os, pathlib, sqlite3, subprocess, tempfile, time
ROOT=pathlib.Path(os.environ.get("LUCII_STEWARD_HOME","/root/lucii/steward"))
UNITS=("lucii-a100.service","lucii-rotor.timer","lucii-multifactory.timer","lucii-devline.timer","lucii-microcrew.timer","lucii-gapcrew.timer","lucii-command.timer")
CREWS={"hospital":"health","police":"policy","laboratory":"diagnosis","garage":"maintenance","dispatcher":"schedules","courier":"status sync","forensics":"receipt hash","warehouse":"storage","vehicle":"transport"}
def probe(unit):
 try:
  p=subprocess.run(["systemctl","is-active",unit],capture_output=True,text=True,timeout=3)
  return p.stdout.strip() or "unknown"
 except (OSError,subprocess.TimeoutExpired):return "unavailable"
def atomic(path,data):
 path.parent.mkdir(parents=True,exist_ok=True)
 fd,tmp=tempfile.mkstemp(dir=str(path.parent),prefix=".pending-")
 try:
  with os.fdopen(fd,"w") as f:
   json.dump(data,f,indent=2,sort_keys=True);f.write("\n");f.flush();os.fsync(f.fileno())
  os.replace(tmp,path)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
def evaluate(states,receipt):
 tasks=[]
 for unit,state in states.items():
  if state not in ("active","inactive"):
   tasks.append(("hospital",unit,"status-"+state,"inspect; no automatic restart"))
 if states.get("lucii-rotor.timer")=="inactive":
  tasks.append(("dispatcher","lucii-rotor.timer","inactive","review schedule only"))
 if receipt is None:
  tasks.append(("forensics","steward/latest.json","missing","capture fresh evidence"))
 else:
  copy=dict(receipt);got=copy.pop("sha256_payload",None)
  actual=hashlib.sha256(json.dumps(copy,sort_keys=True).encode()).hexdigest()
  if actual!=got:tasks.append(("forensics","steward/latest.json","hash-mismatch","recapture; do not edit original"))
 return tasks
def main():
 start=time.monotonic();states={u:probe(u) for u in UNITS}
 try:receipt=json.loads((ROOT/"latest.json").read_text())
 except (OSError,ValueError):receipt=None
 tasks=evaluate(states,receipt)
 path=ROOT/"city-services";path.mkdir(parents=True,exist_ok=True)
 stamp=dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
 db=sqlite3.connect(path/"workorders.sqlite3")
 db.execute("CREATE TABLE IF NOT EXISTS orders (crew TEXT,target TEXT,issue TEXT,action TEXT,observations INTEGER DEFAULT 1,last_seen TEXT,PRIMARY KEY(crew,target,issue))")
 with db:
  for crew,target,issue,action in tasks:
   db.execute("INSERT INTO orders(crew,target,issue,action,last_seen) VALUES(?,?,?,?,?) ON CONFLICT(crew,target,issue) DO UPDATE SET observations=observations+1,last_seen=excluded.last_seen",(crew,target,issue,action,stamp))
 backlog=db.execute("SELECT count(*) FROM orders").fetchone()[0];db.close()
 output={"timestamp":stamp,"states":states,"crews":CREWS,"observations":[{"crew":a,"target":b,"issue":c,"action":d} for a,b,c,d in tasks],"total_workorders":backlog,"no_privileged_mutations":True,"source":"read-only systemctl + steward local receipt","elapsed_ms":round((time.monotonic()-start)*1000,2)}
 atomic(path/"receipts"/(stamp+".json"),output);atomic(path/"latest.json",output)
 print("LUCII-CITY-SERVICES-OK",json.dumps({"crews":len(CREWS),"units":len(states),"new_observations":len(tasks),"workorders":backlog,"elapsed_ms":output["elapsed_ms"]}))
if __name__=="__main__":main()
