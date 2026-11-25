#!/usr/bin/env python3
"""Run a fixed test file against the explicitly selected local candidate."""
import argparse,hashlib,importlib.util,io,json,sys,time,unittest
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
root=a.root.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
sys.path.insert(0,str(root/'source/src'))
f=Path(__file__).with_name('test_regressions.py')
s=importlib.util.spec_from_file_location('test_p7a',f);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
suite=unittest.defaultTestLoader.loadTestsFromModule(m)
class R(unittest.TextTestResult):
    def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.rows=[]
    def addSuccess(self,test):super().addSuccess(test);self.rows.append({'id':test.id(),'outcome':'PASS'})
    def addFailure(self,test,err):super().addFailure(test,err);self.rows.append({'id':test.id(),'outcome':'FAIL','exception':str(err[1])})
    def addError(self,test,err):super().addError(test,err);self.rows.append({'id':test.id(),'outcome':'ERROR','exception':str(err[1])})
stream=io.StringIO();start=time.perf_counter();r=unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=R).run(suite)
(out/'tests.log').write_text(stream.getvalue())
data={'root':str(root),'test_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'skipped':len(r.skipped),'elapsed_seconds':time.perf_counter()-start,'rows':r.rows,'result':'PASS' if r.wasSuccessful() else 'FAIL'}
(out/'results.json').write_text(json.dumps(data,indent=2)+'\n');print(json.dumps({k:v for k,v in data.items() if k!='rows'}));sys.exit(not r.wasSuccessful())
