"""Independent adjudication of integrated output bytes and source-derived views.
It recomputes the experimental judgement; it never executes an experiment.
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
import sys
from p7d_common import Refusal, inventory, protected, read, relative, sha
import views
import environment

def verify(root: Path, out: Path, stage_available: bool=True) -> dict:
    count=0
    def req(test, label):
        nonlocal count
        count+=1
        if not test:raise Refusal(label)
    protected(root)
    manifest=read(out/'RESULTS_MANIFEST.json')
    req(manifest['no_scientific_acceptance_inferred'] is True,'manifest scope')
    for name,item in manifest['files'].items():
        f=out/relative(name)
        req(f.is_file() and not f.is_symlink(),'missing or linked result '+name)
        req(f.stat().st_size==item['bytes'] and sha(f)==item['sha256'],'result identity '+name)
    observed=inventory(out)
    known=set(manifest['files'])|{'RESULTS_MANIFEST.json'}
    extra={x for x in observed if not x.startswith(('fixtures/','environment/dependencies/','home/','tmp/'))}-known
    req(not extra,'unlisted result files '+repr(extra))
    r=read(out/'RECEIPT.json')
    req(r['complete'] is True and r['status']=='COMPLETED_WITH_RETAINED_SCIENTIFIC_HOLD','incomplete or changed operational judgement')
    req(r['scientific_A17']=='NOT_MET' and r['novelty_promoted'] is False and r['A19_A20_active'] is False,'science/authority changed')
    if (out/'CANDIDATE_MANIFEST.txt').exists():
        req(sha(out/'CANDIDATE_MANIFEST.txt')==r['candidate_manifest_sha256'],'run-time candidate manifest binding')
    req(r['Q07']=='NOT_QUALIFIED' and r['same_host_qualification_only'] is True,'environment overclaim')
    req(all(x['returncode']==0 and x['timeout'] is False for x in r['commands']),'unsuccessful command omitted')
    req(len(r['commands'])==22,'expected complete stage inventory')
    for name in ('PREFLIGHT','POSTFLIGHT'):
        e=read(out/'environment'/f'{name}.json')
        req(e['status']=='AVAILABLE_RUNTIME_AND_RECORDED_BYTES_MATCH' and not e['problems'],'environment mismatch')
        req(not environment.evaluate(read(root/'metadata/review-environment.observed.json'),e),'environment raw evidence differs from pinned baseline')
        req(e['total_files_checked']==145 and len(e['packages'])==5,'dependency evidence missing')
        req(e['clean_machine_qualified'] is False and e['Q07']=='NOT_QUALIFIED','unsupported cold-machine status')
    sys.path.insert(0,str(root/'experiments/p7c/code'))
    from check_results import check
    derived_check=check(root,out/'experiment')
    req(derived_check==read(out/'INDEPENDENT_RECOMPUTATION.json'),'independent recomputation differs')
    req(views.compare_references(root,out/'experiment')==read(out/'REFERENCE_COMPARISON.json'),'reference comparison differs')
    numbers=views.derived(out)
    req(numbers==read(out/'views/NUMBERS.json'),'generated numeric view differs')
    req(views.LIMITATIONS==read(out/'views/LIMITATIONS.json'),'limitations lost or changed')
    raw=read(out/'regression/oracle.json')
    req(views.corrected_oracle(raw)==read(out/'views/legacy_oracle.current-wording.json'),'oracle wording projection differs')
    erratum=read(out/'views/ORACLE_ERRATUM.json')
    req(erratum['raw_sha256']==sha(out/'regression/oracle.json') and erratum['values_changed'] is False,'oracle erratum provenance')
    with (out/'views/A17_pairs.csv').open(newline='') as f:table=list(csv.DictReader(f))
    pilot=read(out/'experiment/pilot_summary.json'); expected={x['id'] for x in pilot['rows']}
    req(len(table)==len(expected)==32 and {x['cell_id'] for x in table}==expected,'pair table dropped/added cases')
    for row in table:
        req(row['eligible']==str(row['cell_id'] not in pilot['ineligible_challenges']),'eligibility table')
        req(row['strict_pilot_decision']=='NOT_MET','table scientific promotion')
        req(row['additional_obligation_in_fixed_B2']==str(row['cell_id'] in pilot['incremental_cells']),'table incremental scope')
    with (out/'views/A18_programs.csv').open(newline='') as f:table=list(csv.DictReader(f))
    oracle=read(out/'experiment/oracle.json'); exps={x['id']:x for x in oracle['rows']}
    req(len(table)==32 and {x['program'] for x in table}==set(exps),'oracle table inventory')
    for row in table:
        x=exps[row['program']]
        req(int(row['checks'])==len(x['comparisons']) and int(row['expected_callables'])==len(x['expected']),'oracle table values')
        req(row['all_comparisons_agree']=='True','oracle comparison not passed')
    regression=read(out/'regression/result.json')
    req(regression['tests']==len(regression['rows']) and len({x['id'] for x in regression['rows']})==regression['tests'],'test results inventory')
    wanted=894 if r['mode']=='full' else 83
    req(regression['tests']==r['tests']==wanted,'requested test domain not delivered')
    req(sum(x['outcome']=='SKIP' for x in regression['rows'])==r['skips']==regression['skips'],'skip accounting')
    req(all(x['outcome'] in ('PASS','SKIP') and (x['outcome']!='SKIP' or bool(x.get('reason'))) for x in regression['rows']),'unexplained test outcome')
    imports=read(out/'protocol/IMPORTS.json')
    req(imports['returncode']==0 and imports['isolated'] and imports['no_site'],'scoped protocol execution')
    req(imports['loaded_staged_modules']>0,'dependency stage not used')
    stage_records=read(out/'STAGED_INVENTORY.json')
    for module in imports['modules']:
        if module['staged_dependency']:
            rel=Path(module['path']).relative_to(Path(imports['site_directory'])).as_posix()
            key='environment/dependencies/site/'+relative(rel)
            req(stage_records[key]['sha256']==module['sha256'],'loaded dependency unbound')
        else:
            req('site-packages' not in Path(module['path']).parts,'ambient third-party import')
    if stage_available:
        for name,item in stage_records.items():
            f=out/relative(name)
            req(f.is_file() and sha(f)==item['sha256'],'staged data modified '+name)
    return {'schema':'codeprobe-p7d-result-adjudication/1','status':'VERIFIED_OPERATIONAL_REPRODUCTION_ONLY',
            'checks':count,'P7C_independent_checks':derived_check['checks'],'tests':regression['tests'],
            'stage_bytes_checked':stage_available,'A17':'NOT_MET','Q07':'NOT_QUALIFIED','novelty_promoted':False}

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--results',type=Path,required=True);ap.add_argument('--audit-copy',action='store_true',help='Acknowledge fixture/dependency bytes omitted from an audit copy; all raw results still required')
    a=ap.parse_args()
    try:result=verify(a.candidate,a.results,not a.audit_copy)
    except (ValueError,OSError,KeyError,TypeError) as exc:print('REFUSED_RESULTS:',exc);raise SystemExit(1)
    print(json.dumps(result,indent=2))
