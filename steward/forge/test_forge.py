import importlib.util, pathlib, tempfile, unittest
p=pathlib.Path(__file__).with_name("forge.py")
spec=importlib.util.spec_from_file_location("forge",p)
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();f.ROOT=pathlib.Path(self.tmp.name);self.db=f.con()
 def tearDown(self):self.db.close();self.tmp.cleanup()
 def test_create_map(self):
  f.add(self.db,"sample-site","site","unit-test")
  f.add(self.db,"sample-card","component","unit-test")
  f.link(self.db,"sample-site","sample-card","contains")
  f.token_init(self.db);f.build_map(self.db)
  self.assertTrue((f.ROOT/"maps"/"index.html").exists())
  self.assertIn("sample-card",(f.ROOT/"maps"/"TOC.md").read_text())
 def test_quality_not_execution(self):
  f.add(self.db,"sample-card","component","unit-test")
  result=f.check(self.db,"sample-card")
  self.assertFalse(result["execution_verified"])
  self.assertEqual(result["verdict"],"NEEDS_EVIDENCE")
 def test_cycle_rejected(self):
  for name in ("sample-a","sample-b"):f.add(self.db,name,"component")
  f.link(self.db,"sample-a","sample-b","uses")
  with self.assertRaises(ValueError):f.link(self.db,"sample-b","sample-a","uses")
 def test_duplicate_rejected(self):
  f.add(self.db,"sample-a","token")
  with self.assertRaises(Exception):f.add(self.db,"sample-a","token")
if __name__=="__main__":unittest.main()
