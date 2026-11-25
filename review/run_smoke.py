#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,subprocess,sys,tempfile,time
from pathlib import Path

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--package-root',type=Path,default=Path(__file__).resolve().parents[1]); ap.add_argument('--timeout-seconds',type=int,default=330); a=ap.parse_args(); root=a.package_root.resolve()
    with tempfile.TemporaryDirectory(prefix='codeprobe-p7-r4-smoke-') as td:
        start=time.perf_counter(); timed_out=False
        try:
            p=subprocess.run([sys.executable,'-I','-S','-B',str(root/'review'/'run_reproduction.py'),'--package-root',str(root),'--output',td,'--skip-full-suite'],cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=a.timeout_seconds)
            returncode=p.returncode; output=p.stdout
        except subprocess.TimeoutExpired as exc:
            timed_out=True; returncode=124; output=(exc.stdout or '')+(exc.stderr or '')
        elapsed=time.perf_counter()-start
        result={'schema':'codeprobe-p7-smoke-receipt/v2','status':'PASS' if returncode==0 and not timed_out else 'FAIL','seconds':elapsed,'budget_seconds':300,'process_timeout_seconds':a.timeout_seconds,'within_budget':elapsed<=300,'timed_out':timed_out,'network_policy':{'external_network_required':False,'external_network_intentional_use':False,'loopback_used_by_source_tests':False,'telemetry':'not_syscall_instrumented'},'output':output}
        print(json.dumps(result,indent=2)); return 0 if result['status']=='PASS' and result['within_budget'] else 1
if __name__=='__main__': raise SystemExit(main())
