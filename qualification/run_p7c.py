#!/usr/bin/env python3
"""Execute the retained P7C finite experiment in a new local directory.
No installation, network, automatic retry, project-source execution or production
patch. Parsed generated source is data. Exact frozen carrier identities require
an identical declared source/runtime context; this is not clean-machine Q07.
"""
from pathlib import Path
import argparse,datetime,json,hashlib,subprocess,sys,time,platform,os

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    root=Path(__file__).resolve().parents[1];ex=root/'experiments/p7c';out=args.output.absolute()
    if out.is_symlink() or any(p.is_symlink() for p in out.parents):ap.error('Linked output/ancestor is not permitted')
    out=out.resolve()
    if out.exists() or out==root or root in out.parents:ap.error('Choose a new directory outside candidate; no deletion or overwrite')
    sys.path.insert(0,str(ex/'code'));from common import load,save,sha,identities,overlay_profiles
    fr=load(ex/'FREEZE2.json')
    for name,entry in fr['files'].items():
        if sha((ex/name).read_bytes())!=entry['sha256']:raise ValueError('frozen study input/code changed '+name)
    if identities(root/'source')!=fr['source_snapshot']:raise ValueError('production source changed')
    out.mkdir(parents=True,exist_ok=False);commands=[];t0=time.perf_counter()
    env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONHASHSEED='0',TZ='UTC')
    result={'schema':'codeprobe-p7c-run/1','candidate':load(root/'qualification/REVISION.json')['revision'],'python':platform.python_version(),'platform':platform.platform(),'freeze_sha256':sha((ex/'FREEZE2.json').read_bytes()),'complete':False,'A19_A20_active':False,'Q07':'NOT_QUALIFIED'}
    def step(label,cmd):
        started=datetime.datetime.now(datetime.timezone.utc).isoformat();t=time.perf_counter()
        with (out/(label+'.log')).open('xb') as log:
            p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env,cwd=root)
            try:rc=p.wait(timeout=90);timedout=False
            except subprocess.TimeoutExpired:p.kill();rc=p.wait();timedout=True
        row={'label':label,'command':cmd,'returncode':rc,'timeout':timedout,'start_utc':started,'seconds':time.perf_counter()-t};commands.append(row)
        save(out/(label+'.receipt.json'),row)
        if rc:raise RuntimeError('retained failed execution '+label)
    try:
        for name in ('VERIFY','VERIFY_METADATA'):step(name,[sys.executable,'-I','-B',str(root/(name+'.py'))])
        for f in range(1,9):
            if f==4:
                recipes={c['id']:c for c in load(ex/'data/pilot_recipes.json')}
                for v in range(1,5):
                    for side in ('healthy','challenge'):
                        ident=f'F4-V{v}';c=recipes[ident];label=ident+'_'+side;source=out/'fixtures'/label
                        thresholds=c['profile_thresholds'] if side=='challenge' else [c['profile_thresholds'][0]]*2
                        over=overlay_profiles(root/'source',source,thresholds)
                        if over!=load(ex/'data'/f'profiles_{label}.json'):raise ValueError('profile fixture provenance mismatch')
                        step(label,[sys.executable,'-I','-B',str(ex/'code/worker.py'),'--source',str(source),'--data',str(ex/'data'),'--cells',ident+':'+side,'--out',str(out/(label+'.json'))])
            else:
                step(f'F{f}',[sys.executable,'-I','-B',str(ex/'code/worker.py'),'--source',str(root/'source'),'--data',str(ex/'data'),'--cells',';'.join(f'F{f}-V{v}:healthy,challenge' for v in range(1,5)),'--out',str(out/f'F{f}.json')])
        step('ORACLE',[sys.executable,'-I','-B',str(ex/'code/oracle_run.py'),'--candidate',str(root),'--out',str(out/'oracle.json')])
        step('ADJUDICATE',[sys.executable,'-I','-B',str(ex/'code/adjudicate.py'),'--candidate',str(root),'--results',str(out)])
        step('RED_TEAM',[sys.executable,'-I','-B',str(ex/'code/red_team.py'),'--candidate',str(root),'--controls',str(ex/'redteam_inputs.json'),'--out',str(out/'redteam.json')])
        p=load(out/'pilot_summary.json');o=load(out/'oracle.json');red=load(out/'redteam.json')
        result.update(complete=True,pilot_cells=p['cells'],pilot_comparisons=p['comparisons'],pilot_disagreements=p['frozen_expectation_disagreements'],pilot_continuation=p['P6_strict_continuation'],oracle_programs=o['programs'],oracle_checks=o['checks'],oracle_status=o['status'],redteam_status=red['status'])
        result['execution_status']='COMPLETED_WITH_RETAINED_SCIENTIFIC_HOLD' if p['P6_strict_continuation']!='MET_LOCAL_SCOPE_ONLY' else 'COMPLETED_LOCAL_SCOPE'
        if p['failures'] or o['failures'] or red['status']!='PASS_EXPECTED_STRESS_BEHAVIOUR':raise RuntimeError('outcome disagreement; all retained')
    except Exception as e:result.update(error=str(e),execution_status='ERROR_RETAINED')
    result['commands']=commands;result['elapsed_seconds']=time.perf_counter()-t0;save(out/'RECEIPT.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='commands'},indent=2))
    return 0 if result.get('complete') and 'error' not in result else 1
if __name__=='__main__':raise SystemExit(main())
