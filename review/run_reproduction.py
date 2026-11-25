#!/usr/bin/env python3
"""One-command deterministic reproduction pipeline for the P7-R4 review kit."""
from __future__ import annotations
import argparse, hashlib, json, os, platform, re, subprocess, sys, time
from pathlib import Path
from typing import Any

NETWORK_POLICY={
    "external_network_required": False,
    "external_network_intentional_use": False,
    "loopback_used_by_source_tests": True,
    "telemetry": "not_syscall_instrumented",
    "statement": "No external network access is required or intentionally used. The source test suite intentionally exercises loopback-only HTTP and process fixtures; syscall-level telemetry was not collected."
}

def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def write_json(path:Path,obj:Any):
    path.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n',encoding='utf-8')

def run_cmd(cmd:list[str],cwd:Path,env:dict[str,str],timeout_s:int)->tuple[int,str,float,bool]:
    start=time.perf_counter()
    try:
        p=subprocess.run(cmd,cwd=cwd,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout_s)
        return p.returncode,p.stdout,time.perf_counter()-start,False
    except subprocess.TimeoutExpired as exc:
        stdout=exc.stdout.decode(errors='replace') if isinstance(exc.stdout,bytes) else (exc.stdout or '')
        stderr=exc.stderr.decode(errors='replace') if isinstance(exc.stderr,bytes) else (exc.stderr or '')
        return 124,stdout+stderr+f"\nTIMEOUT after {timeout_s} seconds\n",time.perf_counter()-start,True

def source_manifest(source:Path)->dict[str,Any]:
    files=[]
    for p in sorted(x for x in source.rglob('*') if x.is_file() and '__pycache__' not in x.parts and not x.name.endswith('.pyc')):
        rel=p.relative_to(source).as_posix(); files.append({'path':rel,'bytes':p.stat().st_size,'sha256':sha(p)})
    tree=hashlib.sha256(''.join(f"{x['sha256']}  {x['path']}\n" for x in files).encode()).hexdigest()
    return {'schema':'codeprobe-source-tree-manifest/v1','files':files,'summary':{'file_count':len(files),'byte_count':sum(x['bytes'] for x in files),'tree_sha256':tree}}

def normalise_protocol(raw:dict[str,Any])->dict[str,Any]:
    return {'schema':'codeprobe-p7-normalised-protocol-results/v2','status':raw['status'],'failed_tests':raw['failed_tests'],'input_sha256':raw['input_sha256'],'tests':raw['tests'],'summary':raw['summary'],'scope':{'network_policy':NETWORK_POLICY,'historical_ce09_ce11_available':False}}

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--package-root',type=Path,default=Path(__file__).resolve().parents[1])
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--skip-full-suite',action='store_true')
    ap.add_argument('--verify-reference',type=Path)
    ap.add_argument('--review-timeout-seconds',type=int,default=300)
    ap.add_argument('--source-timeout-seconds',type=int,default=1200)
    a=ap.parse_args(); root=a.package_root.resolve(); out=a.output.resolve(); out.mkdir(parents=True,exist_ok=True); receipts=out/'receipts'; receipts.mkdir(exist_ok=True)
    env=os.environ.copy(); env.update({'PYTHONDONTWRITEBYTECODE':'1','PYTHONHASHSEED':'0','TZ':'UTC','LC_ALL':'C.UTF-8','LANG':'C.UTF-8'})
    canonical=[]; runtime=[]
    def step(name,cmd,cwd,timeout,output_path=None):
        rc,log,secs,timed_out=run_cmd(cmd,cwd,env,timeout); (receipts/f'{name}.log').write_text(log,encoding='utf-8')
        runtime.append({'step':name,'seconds':round(secs,6),'returncode':rc,'timeout_seconds':timeout,'timed_out':timed_out})
        if output_path is not None: canonical.append(output_path)
        if rc!=0: raise RuntimeError(f'{name} failed with return code {rc}; see {receipts/f"{name}.log"}')
    try:
        oracle=out/'parser-independent-oracle-results.json'
        step('oracle',[sys.executable,'-I','-S','-B',str(root/'review'/'parser_independent_oracle.py'),'--source-root',str(root/'source'),'--cases','256','--output',str(oracle)],root,a.review_timeout_seconds,oracle)
        claims=out/'claims-as-tests-results.json'
        step('claims',[sys.executable,'-I','-S','-B',str(root/'review'/'claims_suite.py'),'--package-root',str(root),'--oracle-result',str(oracle),'--output',str(claims)],root,a.review_timeout_seconds,claims)
        rawp=out/'protocol-harness-raw.json'
        step('protocol',[sys.executable,'-I','-B',str(root/'review'/'p6_protocol_harness.py'),'--root',str(root/'source'),'--phase-dir',str(root/'protocol'),'--p3-results',str(root/'protocol'/'APEX_P3_CodeProbe_AuditHarnessResults_v1.json'),'--output',str(rawp)],root,a.review_timeout_seconds)
        raw=json.loads(rawp.read_text()); rawp.unlink(); norm=out/'protocol-harness-results.json'; write_json(norm,normalise_protocol(raw)); canonical.append(norm)
        sm=out/'source-tree-manifest.json'; write_json(sm,source_manifest(root/'source')); canonical.append(sm)
        if not a.skip_full_suite:
            rc,log,secs,timed_out=run_cmd([sys.executable,'-I','-S','-B','-m','unittest','discover','-s','tests','-p','test_*.py'],root/'source',env,a.source_timeout_seconds)
            (receipts/'source_full_suite.log').write_text(log,encoding='utf-8'); runtime.append({'step':'source_full_suite','seconds':round(secs,6),'returncode':rc,'timeout_seconds':a.source_timeout_seconds,'timed_out':timed_out})
            m=re.search(r'Ran (\d+) tests?',log); skip_match=re.search(r'skipped=(\d+)',log)
            summary={'schema':'codeprobe-source-test-summary/v2','status':'PASS' if rc==0 else 'FAIL','tests':int(m.group(1)) if m else None,'failures':0 if rc==0 else None,'errors':0 if rc==0 else None,'skip_declarations':int(skip_match.group(1)) if skip_match else 0,'command':'python -I -S -B -m unittest discover -s tests -p test_*.py','timeout_seconds':a.source_timeout_seconds,'timed_out':timed_out}
            if rc!=0: raise RuntimeError(f'source_full_suite failed with return code {rc}')
        else:
            summary={'schema':'codeprobe-source-test-summary/v2','status':'NOT_RUN_SMOKE','tests':None,'failures':None,'errors':None,'skip_declarations':None,'command':'full suite omitted by --skip-full-suite','timeout_seconds':a.source_timeout_seconds,'timed_out':False}
        st=out/'source-test-summary.json'; write_json(st,summary); canonical.append(st)
        claim_obj=json.loads(claims.read_text())
        demo={'schema':'codeprobe-p7-demonstration-results/v2','status':'PASS' if claim_obj['status']=='PASS' else 'FAIL','demonstrations':[{'id':f"D-{c['claim_id']}",'claim_id':c['claim_id'],'status':c['status'],'shows':c['shows'],'does_not_show':c['does_not_show'],'checks':c['checks'],'execution':'live' if c['claim_id']=='P6-C02' else 'claim_obligation'} for c in claim_obj['claims']]}
        dp=out/'demonstration-results.json'; write_json(dp,demo); canonical.append(dp)
        items=[{'path':p.name,'sha256':sha(p),'bytes':p.stat().st_size,'role':'canonical_result'} for p in sorted(canonical,key=lambda x:x.name)]
        manifest={'schema':'codeprobe-p7-results-manifest/v2','candidate_status':'local_unreleased_review_candidate','review_package_revision':'R4','canonical_command':'python -I -S -B review/run_reproduction.py --output <directory>','source_tree_sha256':json.loads(sm.read_text())['summary']['tree_sha256'],'outputs':items,'historical_context_policy':'CE09/CE11-dependent values are excluded from the principal result set and remain UNVERIFIED_CONTEXT_ONLY','network_policy':NETWORK_POLICY,'all_canonical_steps_pass':all(obj.get('status') in {'PASS','NOT_RUN_SMOKE'} for obj in (json.loads(p.read_text()) for p in canonical if p.suffix=='.json') if 'status' in obj)}
        mp=out/'results-manifest.json'; write_json(mp,manifest)
        receipt={'schema':'codeprobe-p7-run-receipt/v2','candidate_revision':'R4','python':platform.python_version(),'implementation':platform.python_implementation(),'platform':platform.platform(),'steps':runtime,'network_policy':NETWORK_POLICY,'output_directory':str(out),'manifest_sha256':sha(mp)}; write_json(receipts/'run-receipt.json',receipt)
        mismatches=[]
        if a.verify_reference:
            ref=json.loads(a.verify_reference.resolve().read_text()); refmap={x['path']:x['sha256'] for x in ref['outputs']}; gotmap={x['path']:x['sha256'] for x in items}
            mismatches=[{'path':k,'expected':v,'observed':gotmap.get(k)} for k,v in refmap.items() if gotmap.get(k)!=v]
            write_json(receipts/'reference-verification.json',{'status':'PASS' if not mismatches else 'FAIL','mismatches':mismatches,'reference':str(a.verify_reference)})
        failed=mismatches
        result={'status':'PASS' if not failed else 'FAIL','manifest':str(mp),'runtime_steps':runtime,'network_policy':NETWORK_POLICY,'reference_mismatches':mismatches}
        print(json.dumps(result,indent=2)); return 0 if not failed else 1
    except Exception as exc:
        receipt={'schema':'codeprobe-p7-run-receipt/v2','candidate_revision':'R4','python':platform.python_version(),'implementation':platform.python_implementation(),'platform':platform.platform(),'steps':runtime,'network_policy':NETWORK_POLICY,'status':'FAIL','error':{'type':type(exc).__name__,'message':str(exc)}}
        write_json(receipts/'run-receipt.json',receipt); print(json.dumps(receipt,indent=2)); return 1
if __name__=='__main__': raise SystemExit(main())
