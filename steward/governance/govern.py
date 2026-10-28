#!/usr/bin/env python3
"""Lucii Sovereignty Council: policy checks and non-executing approval receipts."""
import argparse,datetime as dt,hashlib,json,os,pathlib,re,sqlite3,tempfile
ROOT=pathlib.Path(os.environ.get("LUCII_GOV_HOME","/root/lucii/governance"))
SAFE={"inspect","measure","hash","catalog","simulate","test_readonly"}
SENSITIVE={"install","upgrade","restart","deploy","push","merge","delete","privileged_exec"}
def evaluate(request):
 if not isinstance(request,dict) or set(request)-{"id","action","target","approved","evidence","resource_mb"}:return {"allowed":False,"reason":"invalid fields","votes":{}}
 action=request.get("action");target=request.get("target","")
 if action not in SAFE|SENSITIVE or not isinstance(target,str) or len(target)>200:return {"allowed":False,"reason":"unknown operation","votes":{}}
 memory=request.get("resource_mb",32)
 votes={"scope":bool(re.fullmatch(r"[a-zA-Z0-9_./:-]{1,200}",target)) and ".." not in pathlib.PurePosixPath(target).parts,
 "risk":action in SAFE,"capability":action in SAFE,
 "evidence":action in SAFE or bool(request.get("evidence")),
 "resource":type(memory) is int and 0<memory<=96}
 return {"allowed":all(votes.values()),"votes":votes,"action":action,"target":target,
 "reason":"all checks passed" if all(votes.values()) else "controller veto; no sensitive executor configured"}
def persist(req,decision):
 ROOT.mkdir(parents=True,exist_ok=True)
 con=sqlite3.connect(ROOT/"council.sqlite3")
 con.execute("CREATE TABLE IF NOT EXISTS decisions(id INTEGER PRIMARY KEY,at TEXT,request_hash TEXT,allowed INT,detail TEXT)")
 raw=json.dumps(req,sort_keys=True).encode();ts=dt.datetime.now(dt.timezone.utc).isoformat()
 with con:con.execute("INSERT INTO decisions(at,request_hash,allowed,detail) VALUES(?,?,?,?)",(ts,hashlib.sha256(raw).hexdigest(),int(decision["allowed"]),json.dumps(decision)))
 con.close()
 result={"at":ts,"request_sha256":hashlib.sha256(raw).hexdigest(),"decision":decision,"executed":False}
 fd,name=tempfile.mkstemp(dir=ROOT,prefix=".pending-")
 with os.fdopen(fd,"w") as f:json.dump(result,f,indent=2);f.write("\n")
 os.replace(name,ROOT/"latest.json")
def main():
 p=argparse.ArgumentParser();p.add_argument("mode",choices=["demo","check","status"]);p.add_argument("path",nargs="?");a=p.parse_args()
 if a.mode=="status":
  if not (ROOT/"council.sqlite3").exists():print("LUCII-GOVERNANCE-STATUS decisions=0");return
  with sqlite3.connect(ROOT/"council.sqlite3") as c:print("LUCII-GOVERNANCE-STATUS decisions="+str(c.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]));return
 if a.mode=="demo":req={"action":"catalog","target":"city-01","resource_mb":32}
 else:
  if not a.path:raise SystemExit("provide JSON proposal file")
  req=json.loads(pathlib.Path(a.path).read_text())
 decision=evaluate(req);persist(req,decision)
 print("LUCII-GOVERNANCE-"+("APPROVED" if decision["allowed"] else "DENIED"),json.dumps(decision,sort_keys=True))
if __name__=="__main__":main()
