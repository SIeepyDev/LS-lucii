#!/usr/bin/env python3
"""Lucii guild registry: lightweight hierarchical records and non-executing work orders."""
import argparse,datetime,hashlib,json,os,pathlib,re,sqlite3
ROOT=pathlib.Path(os.getenv("LUCII_REGISTRY_HOME","/root/lucii/registry"))
KINDS={"empire":None,"world":"empire","city":"world","guild":"city","site":"guild","wrapper":"site","project":"guild","sandbox":"guild"}
ACTIONS={"inspect","measure","catalog","build-plan","test-plan","deploy-plan","upgrade-plan","merge-plan"}
def database():
 ROOT.mkdir(parents=True,exist_ok=True);c=sqlite3.connect(ROOT/"registry.sqlite3")
 c.execute("PRAGMA foreign_keys=ON")
 c.executescript("CREATE TABLE IF NOT EXISTS objects(id TEXT PRIMARY KEY,kind TEXT,parent TEXT REFERENCES objects(id),created TEXT);CREATE TABLE IF NOT EXISTS budgets(id TEXT PRIMARY KEY REFERENCES objects(id),units INT CHECK(units>=0));CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY,subject TEXT,action TEXT,status TEXT,stamp TEXT,sha256 TEXT)")
 return c
def create(c,kind,name,parent):
 if kind not in KINDS or not re.fullmatch("[a-z][a-z0-9-]{1,47}",name):raise ValueError("invalid kind/name")
 expected=KINDS[kind]
 if expected is None and parent is not None:raise ValueError("root required")
 if expected is not None and (not parent or c.execute("SELECT kind FROM objects WHERE id=?",(parent,)).fetchone()!=(expected,)):raise ValueError("invalid parent")
 at=datetime.datetime.now(datetime.timezone.utc).isoformat()
 with c:c.execute("INSERT INTO objects VALUES(?,?,?,?)",(name,kind,parent,at))
 return {"created":name,"kind":kind,"parent":parent}
def order(c,subject,action):
 if action not in ACTIONS:raise ValueError("not an allowlisted planning operation")
 if not c.execute("SELECT 1 FROM objects WHERE id=?",(subject,)).fetchone():raise ValueError("missing subject")
 now=datetime.datetime.now(datetime.timezone.utc).isoformat();digest=hashlib.sha256((subject+action+now).encode()).hexdigest()
 with c:c.execute("INSERT INTO orders(subject,action,status,stamp,sha256) VALUES(?,?,?,?,?)",(subject,action,"PLANNED",now,digest))
 return {"work_order":digest,"status":"PLANNED","executed":False}
def main():
 p=argparse.ArgumentParser();s=p.add_subparsers(dest="cmd",required=True)
 a=s.add_parser("create");a.add_argument("kind");a.add_argument("name");a.add_argument("--parent")
 b=s.add_parser("budget");b.add_argument("name");b.add_argument("units",type=int)
 d=s.add_parser("order");d.add_argument("name");d.add_argument("action")
 s.add_parser("status")
 v=p.parse_args()
 with database() as c:
  if v.cmd=="create":result=create(c,v.kind,v.name,v.parent)
  elif v.cmd=="budget":
   if v.units<0 or v.units>1000000:raise ValueError("invalid allocation")
   with c:c.execute("INSERT INTO budgets(id,units) VALUES(?,?) ON CONFLICT(id) DO UPDATE SET units=excluded.units",(v.name,v.units))
   result={"budget":v.name,"planning_units":v.units,"real_money":False}
  elif v.cmd=="order":result=order(c,v.name,v.action)
  else:result={"entities":dict(c.execute("SELECT kind,count(*) FROM objects GROUP BY kind")),"orders":dict(c.execute("SELECT status,count(*) FROM orders GROUP BY status")),"budgets":c.execute("SELECT count(*) FROM budgets").fetchone()[0]}
 print("LUCII-REGISTRY-OK",json.dumps(result,sort_keys=True))
if __name__=="__main__":main()
