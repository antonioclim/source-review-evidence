"""Three-track checks: parser-free frozen construction; production; iterative AST audit."""
from pathlib import Path
import sys,argparse,ast,importlib.util,time
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import load,save,sha,traversal,callable_index

def index_callable_observations(result):
    """Index complete entity/metric slots; reject duplicate slots explicitly."""
    indexed={}
    for record in result['observations']:
        if record['entity']['entity_kind']!='python_callable':continue
        key=(record['entity']['entity_id'],record['observation_id'].split('.')[-1])
        if key in indexed:raise ValueError('duplicate callable observation identity')
        indexed[key]=record
    return indexed

def run(root,out):
    sys.path.insert(0,str(root/'source/src'))
    import codeprobe_measurement_kernel as k
    data=root/'experiments/p7c/data';ex={r['id']:r['expected'] for r in load(data/'oracle_expected.json')}
    rows=[];checks=0;failures=[]
    metrics={'physical_span_lines':lambda r:r['end']-r['start']+1,'decision_point_count':lambda r:r['dp'],'mccabe_complexity':lambda r:r['dp']+1,'max_control_nesting_depth':lambda r:r['depth']}
    for c in load(data/'oracle_inputs.json'):
        t=time.perf_counter();r={'id':c['id'],'family':c['family'],'source_sha256':sha(c['source'].encode()),'expected':ex[c['id']],'comparisons':[]}
        try:
            result=k.measure_bytes(c['source'].encode(),language='python',path='oracle/'+c['id']+'.py');audit=traversal(c['source']);r['measurement']=result;r['iterative_audit']=audit
            recs=index_callable_observations(result)
            expected_callables=callable_index(ex[c['id']]);audit_callables=callable_index(audit)
            def check(label,observed,expected):
                nonlocal checks
                checks+=1;entry={'label':label,'observed':observed,'expected':expected,'pass':observed==expected};r['comparisons'].append(entry)
                if observed!=expected:failures.append({'id':c['id'],**entry})
            check('callable_set',sorted({entity_id for entity_id,_ in recs}),sorted(expected_callables))
            ev={x['evidence_id']:x for x in result['source_evidence']}
            for entity_id,x in expected_callables.items():
                for metric,formula in metrics.items():check(entity_id+'/'+metric,recs[(entity_id,metric)]['value'],formula(x))
                phys=ev[recs[(entity_id,'physical_span_lines')]['source_evidence_ids'][0]];trav=ev[recs[(entity_id,'decision_point_count')]['source_evidence_ids'][0]]
                for name,got,want in [('physical_start',phys['start_line'],x['start']),('physical_end',phys['end_line'],x['end']),('traversal_start',trav['start_line'],x['traversal_start']),('traversal_end',trav['end_line'],x['end'])]:check(entity_id+'/'+name,got,want)
                other=audit_callables[entity_id]
                for key in ('start','end','traversal_start','dp','depth'):check(entity_id+'/iterative_'+key,other[key],x[key])
                check(entity_id+'/visited_cover',all(trav['start_line']<=s[0] and trav['end_line']>=s[1] for s in other['spans']),True)
            r['status']='PASS' if all(x['pass'] for x in r['comparisons']) else 'MISMATCH'
        except Exception as e:r.update(status='UNRESOLVED',error_type=type(e).__name__,error=str(e));failures.append({'id':c['id'],'error':str(e)})
        r['elapsed_seconds']=time.perf_counter()-t;rows.append(r)
    save(out,{'schema':'codeprobe-a18-results/1','programs':len(rows),'family_count':8,'callables':sum(len(x) for x in ex.values()),'checks':checks,'failures':failures,'rows':rows,'sources_executed':False,'status':'PASS' if not failures else 'UNRESOLVED','limits':['Finite constructor grammar; implementation-informed','Iterative audit shares CPython parser','No new participant, natural project or external analyser study']})
    print('A18',len(rows),'programs',checks,'checks',len(failures),'disagreements')
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();run(a.candidate,a.out)
