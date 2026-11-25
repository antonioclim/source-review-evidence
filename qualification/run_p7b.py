#!/usr/bin/env python3
"""Reproduce bounded P7B qualification on an already installed environment.

No dependency installation, remote write or automatic retry. --mutation is
expensive: the fixed 52 transported faults and 12 new-module faults run with a
focused workload, then surviving faults run with the complete source workload.
The historical cohort and its original score are never rewritten.
"""
from pathlib import Path
import argparse,concurrent.futures,hashlib,importlib.util,json,os,platform,signal,subprocess,sys,time

CORE=['codeprobe_measurement_kernel.py','codeprobe_interpretation.py','codeprobe_numeric_policy.py','codeprobe_review_contract.py','codeprobe_s01_observation_adapter.py','codeprobe_evidence_gates.py']

def dump(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--full',action='store_true',help='894 tests rather than the 83-test focused cohort')
    ap.add_argument('--coverage',action='store_true',help='measure Python core branches with the pinned existing coverage.py')
    ap.add_argument('--mutation',action='store_true',help='run 64 faults; full-source follow-up for survivors; can take over 30 minutes')
    ap.add_argument('--workers',type=int,choices=range(1,5),default=1)
    a=ap.parse_args();root=Path(__file__).resolve().parents[1];out=a.output.resolve();tools=root/'qualification/p7b'
    if out==root or root in out.parents:ap.error('Use a new output directory outside the candidate')
    if out.exists():ap.error('Output exists; retain it and use an explicitly chosen new directory')
    site=None
    if a.coverage:
        try:
            import coverage
        except ImportError:ap.error('coverage.py 7.13.3 is required but is not installed; no automatic installation')
        if coverage.__version__!='7.13.3':ap.error('Coverage version differs from the qualified 7.13.3')
        site=str(Path(coverage.__file__).resolve().parents[1])
    for file in CORE:
        if not (root/'source/src'/file).is_file():ap.error('Missing core source: '+file)
    out.mkdir(parents=True,exist_ok=False);(out/'home').mkdir();(out/'tmp').mkdir()
    env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONHASHSEED='0',LC_ALL='C.UTF-8',TZ='UTC',HOME=str(out/'home'),TMPDIR=str(out/'tmp'))
    py=[sys.executable,'-I','-S','-B'];records=[];start=time.perf_counter()
    def step(directory,command,limit=900):
        directory.mkdir(parents=True,exist_ok=False);t=time.perf_counter();timeout=False
        with (directory/'run.log').open('wb') as log:
            proc=subprocess.Popen(command,cwd=root,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=(os.name=='posix'))
            try:rc=proc.wait(timeout=limit)
            except subprocess.TimeoutExpired:
                timeout=True
                if os.name=='posix':os.killpg(proc.pid,signal.SIGKILL)
                else:proc.kill()
                rc=proc.wait()
        receipt={'command':command,'returncode':rc,'timeout':timeout,'seconds':time.perf_counter()-t,'timeout_seconds':limit}
        dump(directory/'receipt.json',receipt);return receipt
    base={'workspace':str(out.parent),'root':str(root),'core':CORE,'coverage':a.coverage,'site_packages':site,'source_dirs':None,'include':['*/'+name for name in CORE]}
    # Both root and output may be siblings or distant paths. The bootstrap scope is
    # a common parent, and SHA-256 binding excludes any unrelated source variant.
    base['workspace']=os.path.commonpath([str(root),str(out)])
    def workload(name,mode,mutation=None,identity=False,collect=False):
        folder=out/name;folder.mkdir(parents=True,exist_ok=False)
        cfg={**base,'coverage':collect,'output':str(folder/'processes'),'mutation':mutation,'compile_identity':identity};dump(folder/'config.json',cfg)
        cmd=py+[str(tools/'bootstrap.py'),'--cfg',str(folder/'config.json'),'--',str(tools/'workload.py'),'--root',str(root),'--out',str(folder/'results'),'--mode',mode]
        receipt=step(folder/'job',cmd)
        path=folder/'results/result.json';result=json.loads(path.read_text()) if path.exists() else None
        events=[]
        for path in (folder/'processes').glob('*.jsonl'):
            events.extend(json.loads(line) for line in path.read_text().splitlines())
        return folder,receipt,result,events
    result={'schema':'codeprobe-p7b-run/1','revision':'P7-R4-review-candidate+a2p7b.1','python':platform.python_version(),'platform':platform.platform(),'source_hashes':{n:sha(root/'source/src'/n) for n in CORE},'complete':False,'full_requested':a.full,'coverage_requested':a.coverage,'mutation_requested':a.mutation,'scope':'Existing environment; direct current-Python Popen descendants. Node is observed only. No syscall-complete or hostile-runtime claim.','Q07':'NOT_QUALIFIED','public_release':False,'submission_ready':False}
    try:
        for name in ['VERIFY.py','VERIFY_METADATA.py']:
            rec=step(out/('check_'+Path(name).stem),[sys.executable,'-I','-B',str(root/name)],60)
            if rec['returncode']:raise RuntimeError(name+' failed; retained logs')
        folder,rec,positive,events=workload('baseline','full' if a.full else 'focus',collect=a.coverage)
        if not positive or not positive['success'] or rec['returncode']:raise RuntimeError('Unmutated baseline failed; mutation not started')
        result['baseline']={k:v for k,v in positive.items() if k!='rows'}
        if a.coverage:
            rec=step(out/'coverage_summary_job',[sys.executable,'-I','-B',str(tools/'summarise_coverage.py'),str(folder),str(root),str(out/'coverage_summary')],60)
            if rec['returncode']:raise RuntimeError('Coverage aggregation failed')
            cv=json.loads((out/'coverage_summary/summary.json').read_text());result['coverage']={k:v for k,v in cv.items() if k!='warnings'}
            if cv['core_loaded_without_save'] or cv['unbound_core_paths_omitted']:raise RuntimeError('Core coverage scope incomplete; inspect records')
        if a.mutation:
            _,rec,identity,_=workload('identity_control','focus',identity=True)
            if not identity or not identity['success'] or rec['returncode']:raise RuntimeError('AST identity control failed')
            cohort=json.loads((tools/'mapped52.json').read_text())+json.loads((tools/'gate_mutants12.json').read_text())
            if len(cohort)!=64 or len({x['id'] for x in cohort})!=64:raise ValueError('Cohort identity/count')
            for m in cohort:
                if result['source_hashes'][m['file']]!=m['source_sha256']:raise ValueError('Fault binding does not match current source: '+m['id'])
            def one(m):
                row={'id':m['id'],'file':m['file'],'mapping':m['mapping'],'tiers':[]}
                for mode in ['focus','full']:
                    _,rec,j,ev=workload('mutation/'+m['id']+'/'+mode,mode,m)
                    applied=sum(x['kind']=='mutation_applied' for x in ev)
                    fault=bool(j and (j['failures'] or j['errors'] or j.get('oracle_or_claim_exception') or j.get('oracle')=='FAIL' or j.get('claims')=='FAIL'))
                    outcome='INCONCLUSIVE' if rec['timeout'] or not j or not applied else ('SURVIVED' if j['success'] else 'DETECTED_REQUIRES_BEHAVIOURAL_REVIEW' if fault else 'INCONCLUSIVE')
                    row['tiers'].append({'mode':mode,'status':outcome,'applied_imports':applied,'seconds':rec['seconds'],'tests':None if not j else j['tests'],'failures':None if not j else j['failures'],'errors':None if not j else j['errors']})
                    if outcome!='SURVIVED':break
                row['status']=row['tiers'][-1]['status'];dump(out/'mutation'/m['id']/'classification.json',row);return row
            with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:rows=list(pool.map(one,cohort))
            dump(out/'mutation/results.json',rows);result['mutation']={'count':len(rows),'detected_pending_review':sum(x['status'].startswith('DETECTED') for x in rows),'survived':sum(x['status']=='SURVIVED' for x in rows),'inconclusive':sum(x['status']=='INCONCLUSIVE' for x in rows),'historical_score_not_changed':'15/52, P4 test set'}
        result['complete']=True;result['status']='EXECUTED_DECLARED_P7B_SCOPE'
    except Exception as exc:result.update(status='STOPPED_WITH_RETAINED_EVIDENCE',error=repr(exc))
    result['seconds']=time.perf_counter()-start
    result['files']=[{'path':p.relative_to(out).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(out.rglob('*')) if p.is_file() and not p.is_symlink()]
    dump(out/'P7B_RUN.json',result);print(json.dumps({k:result[k] for k in ['status','complete','seconds']}));return int(not result['complete'])
if __name__=='__main__':raise SystemExit(main())
