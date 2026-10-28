#!/usr/bin/env python3
"""Lucii Action Directorate: scoped target discovery, safe checks, policy-gated plans."""
import argparse, datetime, hashlib, json, os, pathlib, re, sqlite3, subprocess, time
ROOT=pathlib.Path(os.getenv("LUCII_ACTION_HOME","/root/lucii/action"))
TYPES={"file","directory","git","site"}
OPERATIONS={"inspect","hash","git-status","publish-plan","repair-plan"}
def database():
 ROOT.mkdir(parents=True,exist_ok=True)
 c=sqlite3.connect(ROOT/"directorate.sqlite3")
 c.execute("CREATE TABLE IF NOT EXISTS targets(id TEXT PRIMARY KEY, kind TEXT, path TEXT, exposure TEXT, created TEXT)")
 c.execute("CREATE TABLE IF NOT EXISTS receipts(id INTEGER PRIMARY KEY, stamp TEXT, target TEXT, operation TEXT, verdict TEXT, detail TEXT)")
 return c
def name_ok(x):return bool(re.fullmatch("[a-z][a-z0-9-]{1,48}",x))
def register(c,name,kind,path,exposure):
 if not name_ok(name) or kind not in TYPES or exposure not in ("private","public"):raise ValueError("invalid target")
 if exposure=="public":raise ValueError("public registration requires separate review")
 if kind=="site":raise ValueError("remote sites require separate explicit allowlist")
 p=pathlib.Path(path).resolve(strict=True)
 if not p.exists() or (kind=="file" and not p.is_file()) or (kind in ("directory","git") and not p.is_dir()):raise ValueError("invalid local path")
 if kind=="git" and not (p/".git").exists():raise ValueError("not a git worktree")
 if p.is_symlink():raise ValueError("symlinks not admitted")
 with c:c.execute("INSERT INTO targets VALUES(?,?,?,?,?)",(name,kind,str(p),"private",datetime.datetime.now(datetime.timezone.utc).isoformat()))
 return {"registered":name,"kind":kind,"exposure":"private"}
def sha_file(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(65536),b""):h.update(b)
 return h.hexdigest()
def evaluate(c,name,operation):
 row=c.execute("SELECT kind,path,exposure FROM targets WHERE id=?",(name,)).fetchone()
 if not row:raise ValueError("unknown target")
 if operation not in OPERATIONS:raise ValueError("operation not allowed")
 kind,path,exposure=row;p=pathlib.Path(path)
 if not p.exists():return "FAILED",{"reason":"target missing"}
 if operation=="inspect":
  return "PASS",{"kind":kind,"exists":True,"is_dir":p.is_dir(),"size_bytes":p.stat().st_size if p.is_file() else None}
 if operation=="hash":
  if not p.is_file() or p.stat().st_size>16*1024*1024:return "BLOCKED",{"reason":"hash only files up to 16 MiB"}
  return "PASS",{"sha256":sha_file(p),"size_bytes":p.stat().st_size}
 if operation=="git-status":
  if kind!="git":return "BLOCKED",{"reason":"requires git target"}
  try:
   q=subprocess.run(["git","-C",str(p),"status","--short"],text=True,capture_output=True,timeout=5,check=False)
   return ("PASS" if q.returncode==0 else "FAILED"),{"exit":q.returncode,"output":q.stdout[:2000]}
  except (OSError,subprocess.TimeoutExpired) as e:return "FAILED",{"reason":type(e).__name__}
 return "PLAN_ONLY",{"operation":operation,"requires_approval":True,"published":False,"changed_files":False}
def perform(c,name,operation):
 stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
 verdict,detail=evaluate(c,name,operation)
 with c:c.execute("INSERT INTO receipts(stamp,target,operation,verdict,detail) VALUES(?,?,?,?,?)",(stamp,name,operation,verdict,json.dumps(detail,sort_keys=True)))
 return {"target":name,"operation":operation,"verdict":verdict,"detail":detail,"timestamp":stamp}
def main():
 p=argparse.ArgumentParser();s=p.add_subparsers(dest="cmd",required=True)
 a=s.add_parser("register");a.add_argument("name");a.add_argument("kind",choices=sorted(TYPES));a.add_argument("path");a.add_argument("--exposure",choices=("private","public"),default="private")
 b=s.add_parser("check");b.add_argument("name");b.add_argument("operation",choices=sorted(OPERATIONS))
 s.add_parser("status")
 a=p.parse_args()
 with database() as c:
  if a.cmd=="register":out=register(c,a.name,a.kind,a.path,a.exposure)
  elif a.cmd=="check":out=perform(c,a.name,a.operation)
  else:out={"targets":c.execute("SELECT count(*) FROM targets").fetchone()[0],"receipts":c.execute("SELECT count(*) FROM receipts").fetchone()[0],"by_verdict":dict(c.execute("SELECT verdict,count(*) FROM receipts GROUP BY verdict"))}
 print("LUCII-ACTION-OK",json.dumps(out,sort_keys=True))
if __name__=="__main__":main()
