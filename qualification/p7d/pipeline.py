"""One local command for P7A/B regressions, A17/A18 and evidence views.

Default: 83 focused tests plus retained oracles, claims, protocol and all A17/A18
cases. --full selects all 894 retained tests. No installation, download, mutation
rerun, source-input execution, figure regeneration or scientific promotion.
"""
from __future__ import annotations
import argparse
import datetime
import importlib.util
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import time
from p7d_common import Refusal, inventory, new_output, protected, read, sha, text, write
import environment
import views

CORE=['codeprobe_measurement_kernel.py','codeprobe_interpretation.py','codeprobe_numeric_policy.py',
      'codeprobe_review_contract.py','codeprobe_s01_observation_adapter.py','codeprobe_evidence_gates.py']

def main(argv=None) -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--site-dir',type=Path)
    ap.add_argument('--full',action='store_true')
    ap.add_argument('--preflight-only',action='store_true')
    args=ap.parse_args(argv)
    root=Path(__file__).resolve().parents[2]
    if not sys.flags.isolated or not sys.flags.no_site or not sys.dont_write_bytecode:
        ap.error('run with python -I -S -B REPRODUCE.py; no automatic relaunch')
    try:
        out=new_output(args.output,root)
    except (OSError,ValueError) as exc:
        print('REFUSED_OUTPUT:',exc);return 2
    out.mkdir(parents=True,exist_ok=False)
    text(out/'CANDIDATE_MANIFEST.txt',(root/'SHA256SUMS.txt').read_text())
    for name in ('logs','experiment','environment','protocol'):
        (out/name).mkdir()
    # Absence of inherited PYTHONPATH, proxy and preload is intentional. PATH is
    # retained to permit declared local subprocess fixtures; all values used here
    # are logged, with no credential enumeration.
    env={'PATH':os.environ.get('PATH','/usr/bin:/bin'),'HOME':str(out/'home'),
         'TMPDIR':str(out/'tmp'),'LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TZ':'UTC',
         'PYTHONDONTWRITEBYTECODE':'1','PYTHONHASHSEED':'0'}
    (out/'home').mkdir();(out/'tmp').mkdir()
    write(out/'environment/CHILD_ENVIRONMENT.json',env)
    started=datetime.datetime.now(datetime.timezone.utc).isoformat();t0=time.perf_counter()
    receipt={'schema':'codeprobe-p7d-integrated-run/1','start_utc':started,'complete':False,
             'candidate':read(root/'qualification/REVISION.json')['revision'],
             'candidate_manifest_sha256':sha(root/'SHA256SUMS.txt'),
             'input_lock_sha256':sha(root/'qualification/p7d/INPUT_LOCK.json'),
             'mode':'full' if args.full else 'focus','A19_A20_active':False,
             'novelty_promoted':False,'Q07':'NOT_QUALIFIED','commands':[],'experiment_started':False,
             'same_host_qualification_only':True,'preflight_only':args.preflight_only}
    def step(label,script,arguments=(),timeout=180):
        command=[sys.executable,'-I','-S','-B',str(script),*map(str,arguments)]
        start=datetime.datetime.now(datetime.timezone.utc).isoformat();t=time.perf_counter()
        with (out/'logs'/(label+'.log')).open('xb') as log:
            p=subprocess.Popen(command,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=(os.name=='posix'))
            timedout=False
            try:rc=p.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timedout=True
                if os.name=='posix':os.killpg(p.pid,signal.SIGKILL)
                else:p.kill()
                rc=p.wait()
        row={'label':label,'command':command,'start_utc':start,'seconds':time.perf_counter()-t,
             'returncode':rc,'timeout':timedout}
        receipt['commands'].append(row);write(out/'logs'/(label+'.json'),row)
        if rc or timedout:raise Refusal('retained unsuccessful stage: '+label)
    try:
        step('PACKAGE',root/'VERIFY.py');step('METADATA',root/'VERIFY_METADATA.py')
        inp=protected(root);write(out/'INPUT_ADMISSION.json',inp)
        site=args.site_dir or environment.default_site()
        observation=environment.inspect(root,site);write(out/'environment/PREFLIGHT.json',observation)
        if observation['problems']:raise Refusal('environment differs: '+str(observation['problems']))
        if args.preflight_only:
            receipt.update(complete=True,status='PREFLIGHT_ONLY_MATCH_NO_EXPERIMENT',experiment_started=False)
        else:
            environment.stage(root,site,out/'environment/dependencies')
            ex=root/'experiments/p7c';data=ex/'data';code=ex/'code';result=out/'experiment'
            sys.path.insert(0,str(code))
            from common import overlay_profiles
            from check_results import check
            recipes={x['id']:x for x in read(data/'pilot_recipes.json')}
            receipt['experiment_started']=True
            for family in range(1,9):
                if family==4:
                    for variant in range(1,5):
                        ident=f'F4-V{variant}'
                        for side in ('healthy','challenge'):
                            label=ident+'_'+side;source=out/'fixtures'/label
                            levels=recipes[ident]['profile_thresholds']
                            thresholds=levels if side=='challenge' else [levels[0]]*2
                            overlay=overlay_profiles(root/'source',source,thresholds)
                            if overlay!=read(data/f'profiles_{label}.json'):
                                raise Refusal('profile fixture drift '+label)
                            step(label,code/'worker.py',['--source',source,'--data',data,'--cells',ident+':'+side,'--out',result/(label+'.json')])
                else:
                    label=f'F{family}';cells=';'.join(f'{label}-V{v}:healthy,challenge' for v in range(1,5))
                    step(label,code/'worker.py',['--source',root/'source','--data',data,'--cells',cells,'--out',result/(label+'.json')])
            step('A18',code/'oracle_run.py',['--candidate',root,'--out',result/'oracle.json'])
            step('ADJUDICATE',code/'adjudicate.py',['--candidate',root,'--results',result])
            step('POSTPILOT',code/'red_team.py',['--candidate',root,'--controls',ex/'redteam_inputs.json','--out',result/'redteam.json'])
            write(out/'INDEPENDENT_RECOMPUTATION.json',check(root,result))
            write(out/'REFERENCE_COMPARISON.json',views.compare_references(root,result))
            config={'output':str(out/'process_observation'),'workspace':str(out), 'core':CORE,
                    'mutation':None,'coverage':False,'compile_identity':False}
            # Include direct canonical source loads as well as temporary copies.
            config['workspace']=str(root.parent)
            write(out/'PROCESS_CONFIG.json',config)
            step('REGRESSION',root/'qualification/p7b/bootstrap.py',
                 ['--cfg',out/'PROCESS_CONFIG.json','--',root/'qualification/p7b/workload.py',
                  '--root',root,'--out',out/'regression','--mode',receipt['mode']],timeout=900)
            step('PROTOCOL',root/'qualification/p7d/scoped_entry.py',
                 ['--site',out/'environment/dependencies/site','--receipt',out/'protocol/IMPORTS.json','--',
                  root/'review/p6_protocol_harness.py','--root',root/'source','--phase-dir',root/'protocol',
                  '--p3-results',root/'protocol/APEX_P3_CodeProbe_AuditHarnessResults_v1.json','--output',out/'protocol/raw.json'])
            numbers=views.make_views(out)
            post=environment.inspect(root,site);write(out/'environment/POSTFLIGHT.json',post)
            if post['problems']:raise Refusal('installed environment changed during run')
            write(out/'INPUT_POSTFLIGHT.json',protected(root))
            receipt.update(complete=True,status='COMPLETED_WITH_RETAINED_SCIENTIFIC_HOLD',
                           scientific_A17=numbers['A17']['strict_continuation'],
                           A18_checks=numbers['A18']['checks'],tests=numbers['regression']['tests'],
                           failures=numbers['regression']['failures'],errors=numbers['regression']['errors'],
                           skips=numbers['regression']['skips'],protected_files=inp['protected_files'])
    except Exception as exc:
        receipt.update(status='REFUSED_OR_FAILED_RETAINED',error=str(exc))
        print('RETAINED:',exc)
    receipt['elapsed_seconds']=time.perf_counter()-t0
    write(out/'RECEIPT.json',receipt)
    # Both raw results and generated views are bound; no deletion of incomplete
    # output. Reproducible fixture/dependency copies have separate inventories.
    all_files=inventory(out)
    selected={k:v for k,v in all_files.items() if not k.startswith(('fixtures/','environment/dependencies/','home/','tmp/'))}
    write(out/'STAGED_INVENTORY.json',{k:v for k,v in all_files.items() if k not in selected})
    selected['STAGED_INVENTORY.json']={'bytes':(out/'STAGED_INVENTORY.json').stat().st_size,'sha256':sha(out/'STAGED_INVENTORY.json')}
    write(out/'RESULTS_MANIFEST.json',{'schema':'codeprobe-p7d-results-manifest/1','files':selected,
        'stage_inventory':'STAGED_INVENTORY.json','no_scientific_acceptance_inferred':True})
    print(receipt['status'], 'A17='+str(receipt.get('scientific_A17')), 'Q07='+receipt['Q07'])
    if not receipt['complete']:
        return 2
    if not args.preflight_only:
        from verify_results import verify
        try:
            adjudication=verify(root,out)
            print(__import__('json').dumps(adjudication,indent=2))
        except (ValueError,OSError,KeyError,TypeError) as exc:
            print('POSTCHECK_REFUSED:',exc)
            return 3
    return 0
