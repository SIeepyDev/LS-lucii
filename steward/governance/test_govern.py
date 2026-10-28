import importlib.util,pathlib,tempfile,unittest
s=importlib.util.spec_from_file_location("gov",pathlib.Path(__file__).with_name("govern.py"));g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
class PolicyTests(unittest.TestCase):
 def test_readonly(self):self.assertTrue(g.evaluate({"action":"catalog","target":"city-01"})["allowed"])
 def test_delete(self):self.assertFalse(g.evaluate({"action":"delete","target":"city-01","approved":True})["allowed"])
 def test_traversal(self):self.assertFalse(g.evaluate({"action":"inspect","target":"../secrets"})["allowed"])
 def test_resource(self):self.assertFalse(g.evaluate({"action":"inspect","target":"city-01","resource_mb":1000})["allowed"])
 def test_unknown(self):self.assertFalse(g.evaluate({"action":"shell","target":"city-01"})["allowed"])
 def test_receipt(self):
  with tempfile.TemporaryDirectory() as p:
   g.ROOT=pathlib.Path(p);req={"action":"catalog","target":"city-01"};g.persist(req,g.evaluate(req))
   self.assertTrue((g.ROOT/"latest.json").is_file())
if __name__=="__main__":unittest.main()
