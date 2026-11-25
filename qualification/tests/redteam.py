#!/usr/bin/env python3
"""Behavioural fault injection on five declared obligations; not the P4 cohort score."""
from pathlib import Path
import argparse,ast,hashlib,importlib.util,io,json,sys,types,unittest
from unittest.mock import patch
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
sys.path.insert(0,str(a.root/'source/src'));import codeprobe_numeric_policy as original
s=importlib.util.spec_from_file_location('rt_test',Path(__file__).with_name('test_regressions.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
text=(a.root/'source/src/codeprobe_numeric_policy.py').read_text();rows=[]
faults=[('M025_semantic_successor',"if isinstance(value, (bool, float)) or not isinstance(value, (str, int, Decimal)):","if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):",'test_M025_float_refusal'),('M026','if at < 0 or rt < 0:','if at < 0 and rt < 0:','test_M026_single_negative_tolerance'),('M028','delta <= tolerance else','delta < tolerance else','test_M028_inclusive_equality')]
for mid,old,new,test in faults:
 assert old in text
 src=text.replace(old,new,1);mod=types.ModuleType('numeric_mutant');exec(compile(src,'<behavioural-mutant:'+mid+'>','exec'),mod.__dict__)
 m.num=mod;stream=io.StringIO();r=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.TestSuite([m.NumericRegression(test)]))
 rows.append({'id':mid,'expected_detected':True,'detected':not r.wasSuccessful(),'kind':'behavioural_test_failure','tests':r.testsRun,'log':stream.getvalue(),'source_sha256':hashlib.sha256(src.encode()).hexdigest(),'replace_before':old,'replace_after':new})
m.num=original
for mid,function,implementation,test in [('G2_validity_as_availability','availability_status',lambda *_args,**_kwargs:'PASS','test_syntax_unavailable_is_valid_G2_fail'),('G6_OR_instead_of_AND','consumer_full_status',lambda admission,replay,**_kwargs:'PASS' if 'PASS' in (admission,replay) else 'NOT_EVALUATED','test_G6_raw_ID_not_admitted')]:
 with patch.object(m.gates,function,implementation):
  stream=io.StringIO();r=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.TestSuite([m.GateIntegration(test)]))
 rows.append({'id':mid,'expected_detected':True,'detected':not r.wasSuccessful(),'kind':'behavioural_test_failure','tests':r.testsRun,'log':stream.getvalue()})
result={'scope':'Five obligation-level perturbations; separate from retained 52-mutant P4 cohort. M025 is a semantic successor fault because the closed type guard was refactored; no equivalence exclusion or historical score change.','source_unchanged':True,'rows':rows,'detected':sum(r['detected'] for r in rows),'attempted':len(rows),'status':'PASS' if all(r['detected'] for r in rows) else 'FAIL'}
a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='rows'}));sys.exit(result['status']!='PASS')
