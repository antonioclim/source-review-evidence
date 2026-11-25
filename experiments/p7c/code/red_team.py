"""Post-pilot stress checks; separate from the frozen main32 and its decision.
Inputs are frozen before this script executes them. No result changes the main
pilot numerator or denominator and no product code is patched.
"""
import sys,argparse,copy,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import load,save,sha,canonical,traversal
from materialise import rehash
from arms import structure,binding,record,accepted

def main(root,controls,out):
    sys.path.insert(0,str(root/'source/src'))
    import codeprobe_measurement_kernel as k
    import codeprobe_interpretation as ip
    import codeprobe_evidence_gates as g
    import codeprobe_s01_observation_adapter as a
    droot=root/'experiments/p7c/data';rows=[]
    def consistency(d):
        m=d['capsule']['measurement']; recs={(r['entity']['entity_id'],r['observation_id']):r for r in m['observations']}
        for (entity,oid),r in recs.items():
            if oid=='python.callable.mccabe_complexity':
                dp=recs[(entity,'python.callable.decision_point_count')]
                if r['value']!=dp['value']+1:raise ValueError('C=1+dp is violated')
        # Actual represented item equality is checked without performing source replay.
        ids={r['record_id']:r for r in m['observations']}
        for dim in d['capsule']['dimensions']:
            for item in dim.get('items',[]):
                r=ids[item['record_ref']]
                if item.get('value')!=r['value'] or item['source_evidence_refs']!=r['source_evidence_ids']:raise ValueError('item equality mismatch')
    original=load(droot/'records/F6-V1_challenge.json')
    st,err=accepted(consistency,original)
    rows.append({'id':'STRONG-B1-F6V1','status':st,'error':err,'expect':'FAIL','meaning':'The main changed_value case is distinguishable by an additional cheap represented-value invariant, without source replay; no universal superiority claim.'})
    original=load(droot/'records/F6-V1_healthy.json')
    for inc in load(controls)['coherent_value_increments']:
        d=copy.deepcopy(original);m=d['capsule']['measurement'];entity=record(d)['entity']['entity_id']
        for r in m['observations']:
            if r['entity']['entity_id']==entity and r['observation_id'] in ('python.callable.decision_point_count','python.callable.mccabe_complexity'):
                r['value']+=inc
                for dim in d['capsule']['dimensions']:
                    for item in dim.get('items',[]):
                        if item['record_ref']==r['record_id']:item['value']=r['value']
        rehash(k,ip,d['capsule']);d['carrier']['observation']=a.adapt_observation(record(d))
        s,e=accepted(structure,d,k,ip);b,be=accepted(binding,d,k,ip,g);c,ce=accepted(consistency,d)
        actual=g.qualify_consumer(d['carrier'],d['capsule'],d['source'].encode(),record_id=d['record_id'],**d['request'])
        rows.append({'id':f'COHERENT-{inc}','schema':s,'binding':b,'value_consistency':c,'G6':actual,'input':d,'pass':s==b==c=='PASS' and actual['admission']=='PASS' and actual['replay']=='FAIL','role':'exploratory post-main robustness check; not substituted into32'})
    negative=[]
    for idx,text in enumerate(load(controls)['malformed_sources']):
        m=k.measure_bytes(text.encode(),language='python',path=f'negative{idx}.py')
        r=next(r for r in m['observations'] if r['observation_id']=='python.function_definition_count')
        negative.append({'id':f'INVALID_SYNTAX-{idx}','source':text,'state':r['applicability']['state'],'pass':r['applicability']['state']=='unavailable'})
    for idx,state in enumerate(k.APPLICABILITY_STATES):
        r=copy.deepcopy(record(original));r['applicability']={'state':state,'reason_code':'' if state=='observed' else 'CONTROL','reason':'' if state=='observed' else 'controlled invalid value'};r['value']=None if state=='observed' else 0
        s,e=accepted(k.validate_observation_record,r);negative.append({'id':f'INVALID_VALUE-{idx}','state':state,'status':s,'pass':s=='FAIL','reason':e})
    excluded=[]
    for item in load(controls)['excluded_subtree_sources']:
        m=k.measure_bytes(item['source'].encode(),language='python',path=item['id']+'.py')
        vals={r['entity']['entity_id'].split(':')[2]:r['value'] for r in m['observations'] if r['observation_id']=='python.callable.decision_point_count'}
        excluded.append({'id':item['id'],'actual':vals,'expected':item['expected_dp'],'pass':vals==item['expected_dp']})
    # Compare duplicate geometric perturbations independently of IDs/paths.
    f3=load(droot/'records/F3-V4_challenge.json');f6=load(droot/'records/F6-V4_challenge.json')
    def perturb(d):
        r=record(d);sp=[(e['start_line'],e['end_line'],e['scope']) for e in d['capsule']['measurement']['source_evidence'] if e['evidence_id'] in r['source_evidence_ids']]
        return {'source_sha256':sha(d['source'].encode()),'metric':r['observation_id'],'intervals':sp,'value':r['value']}
    duplicate={'ids':['F3-V4','F6-V4'],'same_normalised_perturbation':perturb(f3)==perturb(f6),'signature':perturb(f3),'consequence':'Two family labels are not independent mechanisms or two independent replications.'}
    ok=rows[0]['status']=='FAIL' and all(r['pass'] for r in rows[1:]) and all(x['pass'] for x in negative+excluded)
    save(out,{'schema':'codeprobe-p7c-post-pilot-redteam/1','main_dataset_changed':False,'main_scoring_changed':False,'rows':rows,'negative_controls':negative,'excluded_subtrees':excluded,'family_overlap':duplicate,'checks':len(rows)+len(negative)+len(excluded)+1,'status':'PASS_EXPECTED_STRESS_BEHAVIOUR' if ok else 'FAIL'})
    print('redteam',ok,len(rows)+len(negative)+len(excluded)+1,'checks')
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--controls',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);x=ap.parse_args();main(x.candidate,x.controls,x.out)
