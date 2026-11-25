"""Second-track recomputation of reported quantities. No experiment is run here."""
from pathlib import Path
import sys,json,argparse
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import load,sha,identities

def check(root,results):
 ex=root/'experiments/p7c';count=0
 def req(x,msg):
  nonlocal count
  count+=1
  if not x:raise ValueError(msg)
 fr=load(ex/'FREEZE2.json')
 for name,entry in fr['files'].items():req(sha((ex/name).read_bytes())==entry['sha256'],'frozen content '+name)
 req(identities(root/'source')==fr['source_snapshot'],'production identity')
 expected={x['id']:x for x in load(ex/'data/pilot_expected.json')}
 rows=[]
 for p in sorted(results.glob('F*.json')):
  if '.receipt.' in p.name:continue
  obj=load(p)
  if isinstance(obj,list):rows.extend(obj)
 req(len(rows)==192,'192 raw side-arm rows');index={(r['cell_id'],r['side'],r['arm']):r for r in rows};req(len(index)==192,'unique side-arm rows')
 diff=[];n=0
 for cid in expected:
  for side in ('healthy','challenge'):
   for arm in ('B0','B1','B2'):
    r=index[(cid,side,arm)];req(r['status']=='OBSERVED','all cases executed')
    req(r['input_sha256']==sha((ex/'data/records'/f'{cid}_{side}.json').read_bytes()),'raw input binding')
    req(r['start_utc']>=fr['utc'],'outcome precedes freeze')
    for field,target in expected[cid][side].items():
     if arm=='B0' and field not in ('value','numeric'):target='NOT_ASSESSED'
     if arm=='B1' and field in ('coverage','replay'):target='NOT_ASSESSED'
     n+=1
     if r['predicate_vector'].get(field)!=target:diff.append((cid,side,arm,field))
 summary=load(results/'pilot_summary.json');req(summary['comparisons']==n==432,'pilot comparison arithmetic');req(summary['frozen_expectation_disagreements']==len(diff)==0,'pilot disagreement arithmetic')
 invalid=[];fams=set();incremental=[]
 for cid in expected:
  b1=index[(cid,'challenge','B1')]['predicate_vector'];b2=index[(cid,'challenge','B2')]['predicate_vector'];valid=all(b1.get(key,'PASS')=='PASS' for key in ('schema','binding'))
  if not valid:invalid.append(cid)
  if valid and any(b1.get(x)=='NOT_ASSESSED' and b2.get(x)=='FAIL' for x in ('coverage','replay')):fams.add(int(cid[1]));incremental.append(cid)
 req(invalid==summary['ineligible_challenges']==['F6-V2','F6-V3','F7-V4'],'ineligibility retained')
 req(sorted(fams)==summary['family_level_incremental_distinctions']==[3,6],'family count')
 req(summary['incremental_cells']==incremental,'cell count')
 req(summary['P6_strict_continuation']=='NOT_MET','no invented continuation')
 o=load(results/'oracle.json');exps={x['id']:x['expected'] for x in load(ex/'data/oracle_expected.json')};req(len(o['rows'])==32 and len({x['id'] for x in o['rows']})==32,'oracle32')
 oraclechecks=0
 for row in o['rows']:
  req(row['expected']==exps[row['id']],'oracle expectation binding')
  observations=row['measurement']['observations'];ev={r['evidence_id']:r for r in row['measurement']['source_evidence']}
  names={r['entity']['entity_id'].split(':')[2] for r in observations if r['entity']['entity_kind']=='python_callable'}
  req(names=={x['name'] for x in exps[row['id']]},'oracle actual callable set')
  for x in exps[row['id']]:
   rr={r['observation_id'].split('.')[-1]:r for r in observations if r['entity']['entity_kind']=='python_callable' and r['entity']['entity_id'].split(':')[2]==x['name']}
   req([rr[k]['value'] for k in ('physical_span_lines','decision_point_count','mccabe_complexity','max_control_nesting_depth')]==[x['end']-x['start']+1,x['dp'],x['dp']+1,x['depth']],'oracle recomputed metrics')
   phy=ev[rr['physical_span_lines']['source_evidence_ids'][0]];trav=ev[rr['decision_point_count']['source_evidence_ids'][0]]
   req([phy['start_line'],phy['end_line'],trav['start_line'],trav['end_line']]==[x['start'],x['end'],x['traversal_start'],x['end']],'oracle recomputed spans')
  for c in row['comparisons']:
   oraclechecks+=1;req(c['actual']==c['expected'] if 'actual' in c else c['observed']==c['expected'],'oracle comparison false')
 req(o['checks']==oraclechecks==592,'oracle592');req(o['callables']==sum(len(v) for v in exps.values())==40,'oracle40callables');req(o['status']=='PASS' and not o['failures'],'oracle verdict')
 return {'checks':count,'pilot_rows':len(rows),'pilot_comparisons':n,'oracle_checks':oraclechecks,'strict_continuation':'NOT_MET','status':'CHECKED_RETAINED_RESULTS_ONLY'}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--results',type=Path,required=True);a=ap.parse_args();print(json.dumps(check(a.candidate,a.results),indent=2))
