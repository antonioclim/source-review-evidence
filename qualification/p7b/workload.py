"""Unchanged source and P7A cohorts; per-test receipts and trace-gap recording."""
import argparse,sys,os,json,time,unittest,importlib.util,builtins
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--mode',choices=['full','focus','extra'],default='full');a=p.parse_args()
r=a.root.resolve();o=a.out.resolve();o.mkdir(parents=True,exist_ok=False)
sys.path[:0]=[str(r/'source/src'),str(r/'source/tools'),str(r/'source'),str(r/'review')];os.chdir(r/'source');start=time.perf_counter();rows=[]
class R(unittest.TextTestResult):
 def addSuccess(self,t):super().addSuccess(t);rows.append({'id':t.id(),'outcome':'PASS'})
 def addFailure(self,t,e):super().addFailure(t,e);rows.append({'id':t.id(),'outcome':'FAIL','exception':str(e[1])})
 def addError(self,t,e):super().addError(t,e);rows.append({'id':t.id(),'outcome':'ERROR','exception':str(e[1])})
 def addSkip(self,t,reason):super().addSkip(t,reason);rows.append({'id':t.id(),'outcome':'SKIP','reason':reason})
 def stopTest(self,t):
  if hasattr(builtins,'_cp7b_restore_trace'):builtins._cp7b_restore_trace()
  super().stopTest(t)
pattern='test*.py' if a.mode=='full' else 'test_p6_formal_core_contracts.py'
suite=unittest.defaultTestLoader.discover(str(r/'source/tests'),pattern=pattern) if a.mode!='extra' else unittest.TestSuite()
for f in [r/'qualification/tests/test_regressions.py',r/'qualification/p7b/test_contracts.py']:
 if f.exists():
  s=importlib.util.spec_from_file_location('q_'+f.stem,f);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(m))
res=unittest.TextTestRunner(verbosity=1,resultclass=R).run(suite)
result={'tests':res.testsRun,'failures':len(res.failures),'errors':len(res.errors),'skips':len(res.skipped),'rows':rows,'source_mode':a.mode,'success':res.wasSuccessful()}
try:
 import parser_independent_oracle,claims_suite
 oracle=parser_independent_oracle.run(r/'source',256);claims=claims_suite.run(r,oracle)
 (o/'oracle.json').write_text(json.dumps(oracle,indent=2));(o/'claims.json').write_text(json.dumps(claims,indent=2))
 result.update(oracle=oracle['status'],claims=claims['status']);result['success'] &= oracle['status']==claims['status']=='PASS'
except BaseException as e:result.update(oracle_or_claim_exception=repr(e),success=False)
result['seconds']=time.perf_counter()-start;(o/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='rows'}));raise SystemExit(not result['success'])
