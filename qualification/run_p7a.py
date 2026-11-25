#!/usr/bin/env python3
"""Local P7A qualification entry point. Never promotes a submission/release state."""
from pathlib import Path
import argparse,hashlib,json,os,platform,subprocess,sys,time

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True,type=Path);ap.add_argument('--full',action='store_true',help='also run the unchanged historical source cohort (824 tests)');a=ap.parse_args()
 root=Path(__file__).resolve().parents[1];out=a.output.resolve()
 if out==root or root in out.parents: raise SystemExit('Use a new output directory outside the candidate')
 out.mkdir(parents=True,exist_ok=False); receipts=out/'receipts';receipts.mkdir()
 env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONHASHSEED='0',LC_ALL='C.UTF-8',TZ='UTC')
 steps=[]
 def step(name,argv,cwd=root,seconds=60):
  start=time.perf_counter()
  with (receipts/(name+'.log')).open('wb') as f:
   try:rc=subprocess.run(argv,cwd=cwd,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=seconds).returncode
   except subprocess.TimeoutExpired:rc=124
  row={'id':name,'returncode':rc,'seconds':time.perf_counter()-start,'command':argv,'timeout_seconds':seconds};steps.append(row)
  (receipts/'steps.json').write_text(json.dumps(steps,indent=2)+'\n')
  if rc:raise RuntimeError(name+' failed; retained log, no retry')
 try:
  tests=root/'qualification/tests';py=[sys.executable,'-I','-B']
  step('regressions',py+[str(tests/'run_tests.py'),'--root',str(root),'--output',str(out/'regressions')])
  step('generated',py+[str(tests/'generated_checks.py'),'--root',str(root),'--model',str(root/'qualification/formal/spec_model.py'),'--output',str(out/'generated')])
  step('gates',py+[str(root/'qualification/demonstrate_gates.py'),'--root',str(root),'--output',str(out/'gates')])
  step('redteam',py+[str(tests/'redteam.py'),'--root',str(root),'--output',str(out/'redteam.json')])
  step('sensitivity',py+[str(tests/'test_policy_sensitivity_guard.py'),str(root),str(out/'sensitivity.json')])
  if sys.platform.startswith('linux'):
   step('resource',py+[str(tests/'resource_probe.py'),'--root',str(root),'--output',str(out/'resource.json')])
  else:steps.append({'id':'resource','status':'NOT_RUN_PLATFORM_SPECIFIC','reason':'Linux process-limit probe only'})
  step('legacy_oracle',py+[str(root/'review/parser_independent_oracle.py'),'--source-root',str(root/'source'),'--cases','256','--output',str(out/'legacy_oracle.json')])
  step('legacy_claims',py+[str(root/'review/claims_suite.py'),'--package-root',str(root),'--oracle-result',str(out/'legacy_oracle.json'),'--output',str(out/'legacy_claims.json')])
  if a.full:step('historical_source_cohort',[sys.executable,'-I','-S','-B','-m','unittest','discover','-s','tests','-p','test_*.py','-v'],root/'source',600)
  status='PASS_P7A_EXECUTED_SCOPE'
 except Exception as exc:status='FAIL_P7A_EXECUTED_SCOPE';error=str(exc)
 else:error=None
 source_files=[p for p in sorted((root/'source').rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc']
 source_identity=hashlib.sha256(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(root).as_posix()+'\n' for p in source_files).encode()).hexdigest()
 result={'schema':'codeprobe-a2-p7a-qualification/v1','revision':'P7-R4-review-candidate+a2p7a.1','status':status,'error':error,'source_identity':source_identity,'python':platform.python_version(),'platform':platform.platform(),'full_source_cohort_requested':a.full,'steps':steps,'limits':['Existing runtime; no clean-machine qualification','Legacy claims retained for regression; current G2/G5/G6 evidence separately versioned','No A17 pilot, A18 experiment, full 52-mutant campaign, manuscript update or release','Loopback/process fixtures in full cohort; no syscall network telemetry'],'outputs':[]}
 for p in sorted(out.rglob('*')):
  if p.is_file():result['outputs'].append({'path':p.relative_to(out).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 (out/'P7A_RESULTS_MANIFEST.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'status':status,'revision':result['revision'],'error':error,'full_source_cohort_requested':a.full}));return int(error is not None)
if __name__=='__main__': raise SystemExit(main())
