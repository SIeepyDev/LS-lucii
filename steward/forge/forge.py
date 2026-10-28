#!/usr/bin/env python3
"""Lucii Asset Forge: reuse map, design tokens, quality gates, upgrade backlog and signals."""
import argparse, datetime as dt, hashlib, html, json, os, pathlib, re, sqlite3, tempfile
ROOT=pathlib.Path(os.environ.get("LUCII_FORGE_HOME","/root/lucii/forge")).resolve()
KINDS={"token","term","component","template","site","route","game","concept","asset","workflow","backend","frontend"}
LEVELS={"PLACEHOLDER":0,"SCAFFOLD":1,"TESTED":2,"HARDENED":3}
DEFAULT_TOKENS={"color.background":"#101b2c","color.text":"#eff6ff","space.1":"4px","space.2":"8px","radius.card":"12px"}
def con():
 ROOT.mkdir(parents=True,exist_ok=True)
 c=sqlite3.connect(ROOT/"forge.sqlite3")
 c.execute("PRAGMA foreign_keys=ON")
 c.executescript("""
 CREATE TABLE IF NOT EXISTS assets(id TEXT PRIMARY KEY,kind TEXT,state TEXT,quality INT CHECK(quality BETWEEN 0 AND 100),source TEXT,created TEXT);
 CREATE TABLE IF NOT EXISTS links(parent TEXT REFERENCES assets(id),child TEXT REFERENCES assets(id),relation TEXT,PRIMARY KEY(parent,child,relation));
 CREATE TABLE IF NOT EXISTS checks(id INTEGER PRIMARY KEY,asset TEXT REFERENCES assets(id),stamp TEXT,status TEXT,reason TEXT);
 CREATE TABLE IF NOT EXISTS signals(id INTEGER PRIMARY KEY,asset TEXT,stamp TEXT,event TEXT,detail TEXT);
 CREATE TABLE IF NOT EXISTS upgrades(asset TEXT PRIMARY KEY REFERENCES assets(id),reason TEXT,status TEXT);
 CREATE TABLE IF NOT EXISTS tokens(key TEXT PRIMARY KEY,value TEXT);
 """)
 return c
def signal(c,a,event,detail):
 c.execute("INSERT INTO signals(asset,stamp,event,detail) VALUES(?,?,?,?)",(a,dt.datetime.now(dt.timezone.utc).isoformat(),event,detail))
def add(c,name,kind,source):
 if not re.fullmatch(r"[a-z][a-z0-9-]{1,63}",name) or kind not in KINDS:raise ValueError("invalid asset")
 if source and (len(source)>300 or "\n" in source):raise ValueError("invalid source")
 with c:
  c.execute("INSERT INTO assets VALUES(?,?,?,?,?,?)",(name,kind,"PLACEHOLDER",0,source or "",dt.datetime.now(dt.timezone.utc).isoformat()))
  signal(c,name,"CREATED","registered; no runtime proof")
 return {"asset":name,"state":"PLACEHOLDER","verified":False}
def link(c,parent,child,relation):
 if parent==child or relation not in ("uses","wraps","depends-on","extends","contains","maps-to"):raise ValueError("bad relationship")
 rows=c.execute("SELECT parent,child FROM links").fetchall()+[(parent,child)]
 graph={}
 for p,ch in rows:graph.setdefault(p,[]).append(ch)
 def reachable(n,target,seen):
  if n==target:return True
  if n in seen:return False
  seen.add(n)
  return any(reachable(v,target,seen) for v in graph.get(n,[]))
 if reachable(child,parent,set()):raise ValueError("cycle")
 with c:
  c.execute("INSERT INTO links VALUES(?,?,?)",(parent,child,relation))
  signal(c,child,"LINKED",parent+":"+relation)
def check(c,name):
 row=c.execute("SELECT kind,state,quality,source FROM assets WHERE id=?",(name,)).fetchone()
 if not row:raise ValueError("unknown asset")
 kind,state,quality,source=row
 checks={"has_source":bool(source),"has_links":bool(c.execute("SELECT 1 FROM links WHERE child=? OR parent=?",(name,name)).fetchone()),
         "has_real_tests":bool(c.execute("SELECT 1 FROM checks WHERE asset=? AND status='RUNTIME_PASS'",(name,)).fetchone())}
 score=20*checks["has_source"]+20*checks["has_links"]+60*checks["has_real_tests"]
 # Metadata scores never become proof of runtime execution.
 verdict="NEEDS_EVIDENCE" if score<80 else "READY_FOR_REVIEW"
 with c:
  c.execute("UPDATE assets SET quality=? WHERE id=?",(score,name))
  c.execute("INSERT INTO checks(asset,stamp,status,reason) VALUES(?,?,?,?)",(name,dt.datetime.now(dt.timezone.utc).isoformat(),verdict,json.dumps(checks)))
  if score<80:c.execute("INSERT INTO upgrades VALUES(?,?,?) ON CONFLICT(asset) DO UPDATE SET reason=excluded.reason,status='OPEN'",(name,"quality="+str(score),"OPEN"))
  signal(c,name,"QUALITY_CHECK",verdict+" score="+str(score))
 return {"asset":name,"score":score,"verdict":verdict,"checks":checks,"execution_verified":False}
def token_init(c):
 with c:
  for k,v in DEFAULT_TOKENS.items():c.execute("INSERT OR IGNORE INTO tokens VALUES(?,?)",(k,v))
 return {"tokens":c.execute("SELECT count(*) FROM tokens").fetchone()[0]}
def atomic(path,content):
 path.parent.mkdir(parents=True,exist_ok=True)
 fd,tmp=tempfile.mkstemp(dir=path.parent,prefix=".partial-")
 try:
  with os.fdopen(fd,"w") as f:f.write(content);f.flush();os.fsync(f.fileno())
  os.replace(tmp,path)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
def build_map(c):
 assets=[dict(id=a,kind=k,state=s,score=q,source=src) for a,k,s,q,src in c.execute("SELECT id,kind,state,quality,source FROM assets ORDER BY id")]
 links=[dict(from_=p,to=ch,relation=r) for p,ch,r in c.execute("SELECT parent,child,relation FROM links ORDER BY parent,child")]
 tokens=dict(c.execute("SELECT key,value FROM tokens ORDER BY key"))
 payload={"schema":"lucii.forge.map.v1","assets":assets,"links":links,"tokens":tokens,
          "backlog":dict(c.execute("SELECT status,count(*) FROM upgrades GROUP BY status"))}
 atomic(ROOT/"maps"/"index.json",json.dumps(payload,indent=2)+"\n")
 cards="".join("<article><strong>"+html.escape(a["id"])+"</strong><p>"+html.escape(a["kind"])+" · "+html.escape(a["state"])+" · quality "+str(a["score"])+"</p></article>" for a in assets)
 styles="body{background:#101b2c;color:#eff6ff;font:16px system-ui;margin:2rem}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}article{padding:14px;border:1px solid #617489;border-radius:12px}small{opacity:.7}"
 page='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Lucii Forge Map</title><style>'+styles+'</style><h1>Lucii Forge · Assets</h1><p>Registered, not necessarily deployed</p><main>'+cards+'</main></html>'
 atomic(ROOT/"maps"/"index.html",page)
 terms=[a["id"]+" — "+a["kind"]+" — "+a["state"] for a in assets]
 atomic(ROOT/"maps"/"TOC.md","# Lucii Forge Contents\n\n"+"\n".join("- "+t for t in terms)+"\n")
 print("LUCII-FORGE-MAP",json.dumps({"assets":len(assets),"links":len(links),"tokens":len(tokens),"open_upgrades":payload["backlog"].get("OPEN",0)}))
def main():
 p=argparse.ArgumentParser();s=p.add_subparsers(dest="action",required=True)
 x=s.add_parser("add");x.add_argument("name");x.add_argument("kind",choices=sorted(KINDS));x.add_argument("--source",default="")
 x=s.add_parser("link");x.add_argument("parent");x.add_argument("child");x.add_argument("relation")
 x=s.add_parser("check");x.add_argument("name")
 for a in ("tokens","map","status","demo"):s.add_parser(a)
 a=p.parse_args()
 with con() as c:
  if a.action=="add":out=add(c,a.name,a.kind,a.source)
  elif a.action=="link":link(c,a.parent,a.child,a.relation);out={"linked":True}
  elif a.action=="check":out=check(c,a.name)
  elif a.action=="tokens":out=token_init(c)
  elif a.action=="map":build_map(c);return
  elif a.action=="demo":
   token_init(c)
   for name,kind in (("sample-site","site"),("sample-card","component")):
    c.execute("INSERT OR IGNORE INTO assets VALUES(?,?,?,?,?,?)",(name,kind,"PLACEHOLDER",0,"demo:local",""))
   c.execute("INSERT OR IGNORE INTO links VALUES(?,?,?)",("sample-site","sample-card","contains"))
   out=check(c,"sample-card")
  else:out={"assets":c.execute("SELECT count(*) FROM assets").fetchone()[0],
            "open_upgrades":c.execute("SELECT count(*) FROM upgrades WHERE status='OPEN'").fetchone()[0],
            "signals":c.execute("SELECT count(*) FROM signals").fetchone()[0]}
 print("LUCII-FORGE-OK",json.dumps(out,sort_keys=True))
if __name__=="__main__":main()
