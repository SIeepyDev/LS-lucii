#!/usr/bin/env python3
"""Lucii multi-speed scheduler: bounded, local, non-AI, evidence-backed."""
import argparse, datetime as dt, fcntl, json, os, pathlib, random, sqlite3, time
ROOT=pathlib.Path(os.getenv("LUCII_PULSE_HOME","/root/lucii/pulse"))
PERIODS={"second":1,"minute":60,"hour":3600,"day":86400,"night":86400}
ROLES={"millisecond":["counter","idea-seed"],"second":["heartbeat","queue-scout"],"minute":["gap-finder","asset-sizer"],"hour":["resource-surveyor","failure-challenger"],"day":["standards-auditor","evidence-curator"],"night":["nightly-review","recovery-planner"]}
def atomic_json(path,obj):
 tmp=path.with_suffix(".tmp");tmp.write_text(json.dumps(obj,sort_keys=True,indent=2)+"\n");os.replace(tmp,path)
def db_open():
 ROOT.mkdir(parents=True,exist_ok=True)
 con=sqlite3.connect(ROOT/"pulse.sqlite3")
 con.execute("CREATE TABLE IF NOT EXISTS executions (id INTEGER PRIMARY KEY, at TEXT, lane TEXT, worker TEXT, outcome TEXT, duration_ms REAL, detail TEXT)")
 con.execute("CREATE TABLE IF NOT EXISTS cadence (lane TEXT PRIMARY KEY, last REAL)")
 return con
def micro(seed):
 rng=random.Random(seed)
 return {"proposals":[{"kind":rng.choice(["test","measure","catalog","verify","repair-plan","prototype"]),"status":"IDEA_ONLY"} for _ in range(3)]}
def perform(lane,seed):
 if lane=="millisecond":return micro(seed)
 if lane=="second":return {"pending_receipts":sum(1 for p in (ROOT/"receipts").glob("*.json")) if (ROOT/"receipts").exists() else 0}
 if lane=="minute":
  base=pathlib.Path("/var/tmp/ls-worlds/worlds")
  return {"worlds":sum(1 for p in base.glob("world-*") if p.is_dir()),"cities":sum(1 for p in base.glob("world-*/*") if p.is_dir())}
 if lane=="hour":
  try:
   with open("/proc/loadavg") as f:load=f.read().split()[:3]
  except OSError:load=[]
  return {"load":load,"action":"OBSERVE_ONLY"}
 if lane=="day":
  return {"evidence":str(pathlib.Path("/root/lucii/garden").exists()),"review":"NO_AUTOMATIC_PROMOTION"}
 return {"night_review":"PLANNED","execute_deployment":False}
def tick(con,force=False):
 now=time.time();hour=dt.datetime.now().hour
 due=[]
 for lane,period in PERIODS.items():
  if lane=="night" and not (0<=hour<6):continue
  row=con.execute("SELECT last FROM cadence WHERE lane=?",(lane,)).fetchone()
  if force or row is None or now-row[0]>=period:due.append(lane)
 for lane in due:
  started=time.perf_counter();seed=int(now)//PERIODS[lane]
  try:detail=perform(lane,seed);status="PASS"
  except Exception as e:detail={"error":type(e).__name__};status="FAIL"
  elapsed=round((time.perf_counter()-started)*1000,3)
  with con:
   for worker in ROLES[lane]:
    con.execute("INSERT INTO executions(at,lane,worker,outcome,duration_ms,detail) VALUES(?,?,?,?,?,?)",
     (dt.datetime.now(dt.timezone.utc).isoformat(),lane,worker,status,elapsed,json.dumps(detail)))
   if status=="PASS":con.execute("INSERT INTO cadence(lane,last) VALUES(?,?) ON CONFLICT(lane) DO UPDATE SET last=excluded.last",(lane,now))
 return due
def run():
 p=argparse.ArgumentParser();p.add_argument("mode",choices=["once","loop","status","demo"]);p.add_argument("--seconds",type=int,default=30);a=p.parse_args()
 con=db_open()
 if a.mode=="status":
  print("LUCII-PULSE-STATUS",json.dumps({"runs":con.execute("SELECT count(*) FROM executions").fetchone()[0],"cadences":dict(con.execute("SELECT lane,last FROM cadence"))}));return
 if a.mode=="demo":
  stamp=int(time.time()*1000);print("LUCII-PULSE-DEMO",json.dumps(micro(stamp)));return
 with (ROOT/"lock").open("a") as lock:
  try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:print("LUCII-PULSE-BUSY");return
  until=time.monotonic()+max(1,min(a.seconds,60))
  while True:
   lanes=tick(con)
   receipt={"timestamp":dt.datetime.now(dt.timezone.utc).isoformat(),"lanes":lanes,"source":"LOCAL_RUNTIME","automation":"READ_ONLY","workers_registered":sum(map(len,ROLES.values()))}
   atomic_json(ROOT/"latest.json",receipt)
   if a.mode=="once" or time.monotonic()>=until:break
   time.sleep(1)
  print("LUCII-PULSE-OK",json.dumps(receipt))
if __name__=="__main__":run()
