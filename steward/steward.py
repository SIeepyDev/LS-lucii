#!/usr/bin/env python3
"""Lucii evidence steward: read-only host audits, local SHA-256 receipts, repair proposals."""
import datetime,hashlib,json,os,pathlib,shutil,socket,subprocess,tempfile,time,sys
ROOT=pathlib.Path(os.environ.get("LUCII_STEWARD_HOME","/root/lucii/steward"))
UNITS=("lucii-a100.service","lucii-rotor.timer","lucii-multifactory.timer","lucii-devline.timer","lucii-microcrew.timer","lucii-gapcrew.timer","lucii-command.timer")
def run(argv):
 if not shutil.which(argv[0]):return {"state":"MISSING_TOOL"}
 try:
  p=subprocess.run(argv,timeout=3,capture_output=True,text=True)
  return {"state":"OK" if p.returncode==0 else "EXIT_"+str(p.returncode),"output":p.stdout.strip()[:300],"error":p.stderr.strip()[:100]}
 except (OSError,subprocess.TimeoutExpired) as e:return {"state":type(e).__name__}
def atomic(path,record):
 path.parent.mkdir(parents=True,exist_ok=True)
 fd,tmp=tempfile.mkstemp(dir=path.parent,prefix=".pending-")
 try:
  with os.fdopen(fd,"w") as f:
   json.dump(record,f,indent=2,sort_keys=True);f.write("\n");f.flush();os.fsync(f.fileno())
  os.replace(tmp,path)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
def ports():
 found=set()
 for name in ("tcp","tcp6"):
  try:
   for line in pathlib.Path("/proc/net/"+name).read_text().splitlines()[1:]:
    cols=line.split()
    if len(cols)>3 and cols[3]=="0A":found.add(int(cols[1].split(":")[-1],16))
  except OSError:pass
 return sorted(found)
def digest(r):return hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest()
def audit():
 start=time.monotonic();service={}
 for unit in UNITS:
  result=run(["systemctl","is-active",unit])
  service[unit]=result.get("output") or result["state"]
 proposals=[{"action":"inspect","unit":u,"state":s} for u,s in service.items() if s not in ("active","inactive")]
 if service.get("lucii-rotor.timer")=="inactive":proposals.append({"action":"review-only","unit":"lucii-rotor.timer","reason":"inactive timer"})
 host={"name":socket.gethostname(),"services":service,"ports_local_tcp":ports(),
       "memory":run(["free","-m"]),"disk":run(["df","-Pk","/"]),
       "tools":{t:bool(shutil.which(t)) for t in ("apt","apt-get","sudo","systemctl","git","python3","jq","rg","fd","pct","ss")},
       "garden_exists":pathlib.Path("/root/lucii/garden").is_dir()}
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
 record={"schema":"lucii.steward.v1","timestamp":stamp,"state":"OBSERVED",
         "source":"local read-only probes","host":host,"proposals":proposals,
         "privileged_changes":False,"elapsed_ms":round((time.monotonic()-start)*1000,2)}
 record["sha256_payload"]=digest(record)
 atomic(ROOT/"receipts"/(stamp+".json"),record);atomic(ROOT/"latest.json",record)
 print("LUCII-STEWARD-OK",json.dumps({"services":service,"proposals":len(proposals),
       "ports":len(host["ports_local_tcp"]),"elapsed_ms":record["elapsed_ms"],"receipt":str(ROOT/"latest.json")}))
def verify():
 record=json.loads((ROOT/"latest.json").read_text());stored=record.pop("sha256_payload")
 ok=stored==digest(record)
 print("LUCII-STEWARD-VERIFY",json.dumps({"hash_match":ok}))
 return ok
if __name__=="__main__":
 if len(sys.argv)>1 and sys.argv[1]=="verify":sys.exit(0 if verify() else 1)
 audit()
