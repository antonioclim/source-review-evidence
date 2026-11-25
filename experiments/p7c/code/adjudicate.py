"""Audit outcomes against frozen expectations; never imported by an experimental arm."""
from pathlib import Path
from collections import Counter
import sys,json,argparse
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import load,save,sha

def adjudicate(root,out):
    ex=root/'experiments/p7c';data=ex/'data';expected={x['id']:x for x in load(data/'pilot_expected.json')};rows=[]
    for f in range(1,9):
        paths=sorted(out.glob('F4-V*.json')) if f==4 else [out/f'F{f}.json']
        for p in paths:
            if '.receipt.' in p.name:continue
            val=load(p)
            if isinstance(val,list):rows.extend(val)
    got={(r['cell_id'],r['side'],r['arm']):r for r in rows}
    if len(rows)!=192 or len(got)!=192:raise ValueError('pilot inventory mismatch; all32 x2 x3 required')
    comparisons=[];case_summary=[]
    for cid,exp in expected.items():
        for side in ('healthy','challenge'):
            for arm in ('B0','B1','B2'):
                row=got[(cid,side,arm)]
                if row['status']!='OBSERVED':comparisons.append({'id':cid,'side':side,'arm':arm,'field':'execution','pass':False,'actual':row});continue
                vector=row['predicate_vector']
                for field,want in exp[side].items():
                    if arm=='B0' and field!='value' and field!='numeric':want='NOT_ASSESSED'
                    if arm=='B1' and field in ('coverage','replay'):want='NOT_ASSESSED'
                    comparisons.append({'id':cid,'side':side,'arm':arm,'field':field,'actual':vector.get(field),'expected':want,'pass':vector.get(field)==want})
        h1=got[(cid,'healthy','B1')].get('predicate_vector',{});b1=got[(cid,'challenge','B1')].get('predicate_vector',{});b2=got[(cid,'challenge','B2')].get('predicate_vector',{})
        admissible=b1.get('schema','PASS')=='PASS' and b1.get('binding','PASS')=='PASS'
        added=[field for field in ('coverage','replay') if b1.get(field)=='NOT_ASSESSED' and b2.get(field)=='FAIL' and admissible]
        case_summary.append({'id':cid,'family':int(cid[1]),'B1_predecessor_admitted':admissible,'added_executed_failures':added,'additional_check_distinction':bool(added),'P6_recipe_conflict':exp['P6_recipe_divergence'],'healthy_controls_conform':all(c['pass'] for c in comparisons if c['id']==cid and c['side']=='healthy'),'explanatory_scope':'NOT_ASSESSED is no wrong acceptance; additional executed obligation in this explicitly defined projection only'})
    failures=[r for r in comparisons if not r['pass']]
    fams=sorted({x['family'] for x in case_summary if x['additional_check_distinction']})
    invalid=[x['id'] for x in case_summary if not x['B1_predecessor_admitted']]
    summary={'schema':'codeprobe-p7c-pilot-adjudication/1','cells':32,'pairs':32,'arm_pairs':96,'arm_side_rows':192,'comparisons':len(comparisons),'frozen_expectation_disagreements':len(failures),'failures':failures,'rows':case_summary,'family_level_incremental_distinctions':fams,'incremental_cells':[x['id'] for x in case_summary if x['additional_check_distinction']],'ineligible_challenges':invalid,'healthy_controls_conform':all(x['healthy_controls_conform'] for x in case_summary),'P6_strict_continuation_all_predecessors_valid':not invalid and not failures,'P6_strict_continuation':'NOT_MET' if invalid or failures or len(fams)<2 else 'MET_LOCAL_SCOPE_ONLY','no_A19_A20_activation':True,'no_primary_novelty_promotion':True,'scope':'Implementation-informed diagnostic pilot. 32 cells retained. Frozen implementation expectations do not amend P6 recipe statements; conflicts stay visible. Conditional family existence is not substituted for the strict continuation rule.'}
    save(out/'pilot_summary.json',summary)
    return summary

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--results',type=Path,required=True);ar=ap.parse_args();j=adjudicate(ar.candidate,ar.results);print(json.dumps({k:j[k] for k in ('cells','comparisons','frozen_expectation_disagreements','family_level_incremental_distinctions','ineligible_challenges','P6_strict_continuation')}))
