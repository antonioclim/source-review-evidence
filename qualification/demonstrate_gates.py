#!/usr/bin/env python3
"""Live typed gate witnesses, separate from the future A17 comparison pilot."""
import argparse,copy,hashlib,json,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();root=a.root.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);sys.path.insert(0,str(root/'source/src'))
import codeprobe_evidence_gates as g
import codeprobe_measurement_kernel as mk
import codeprobe_interpretation as ip
import codeprobe_numeric_policy as num

def store(name,obj): (out/name).write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
source=b'def f(x):\n    if x:\n        return 1\n    return 0\n';(out/'source.py.txt').write_bytes(source)
profiles={p['profile_id']:p['sha256'] for p in ip.available_profiles()};kw=dict(language='python',profile_id='structural-review',profile_sha256=profiles['structural-review'],task_family='source_inspection',path='p7a-demo.py')
cap=ip.interpret_bytes(source,**kw);record=next(r for r in cap['measurement']['observations'] if r['observation_id']=='source.byte_count');carrier=g.make_carrier(cap,source,record_id=record['record_id'],**kw)
store('capsule.json',cap);store('carrier.json',carrier)
good=g.qualify_consumer(carrier,cap,source,**kw)
bad=copy.deepcopy(carrier);bad['observation']['source_evidence'][0]['evidence_id']=record['source_evidence_ids'][0]
raw_refused=g.qualify_consumer(bad,cap,source,**kw);store('raw_alias_carrier.json',bad)
changed=copy.deepcopy(cap);r=next(r for r in changed['measurement']['observations'] if r['record_id']==record['record_id']);r['value']+=1
changed['measurement']['measurement_digest']=mk.sha256_hex(mk.canonical_json(mk._measurement_digest_scope(changed['measurement'])).encode());mk.validate_kernel_result(changed['measurement']);changed.pop('digest');changed['digest']=ip.digest(ip.canonical(changed))
mut_carrier=copy.deepcopy(carrier)
from codeprobe_s01_observation_adapter import adapt_observation
mut_carrier['observation']=adapt_observation(r)
replay_refused=g.qualify_consumer(mut_carrier,changed,source,**kw);store('changed_capsule.json',changed);store('changed_carrier.json',mut_carrier)
syntax=g.evaluate_availability(b'def f(:\n',language='python',observation_id='python.function_definition_count')
zero=g.evaluate_availability(b'pass\n',language='python',observation_id='python.function_definition_count')
policy_source=('def f(x):\n'+''.join(f'    if x == {i}:\n        x += 1\n' for i in range(12))+'    return x\n').encode();(out/'profiles_source.py.txt').write_bytes(policy_source)
relation=g.compare_profiles(policy_source,observation_id='python.callable.mccabe_complexity',profile_ids=('structural-review','structural-review-conservative'))
num_dec=num.compare_decimal('1.0000000000000000000000000001','0',absolute_tolerance='1',relative_tolerance='0');num_bin=num.compare_binary64(0.1,0.0,absolute_tolerance='0.100000000000000012490009027',relative_tolerance='0')
checks={'good_G6':good['status']=='PASS','raw_alias_G6':raw_refused['admission']=='FAIL' and raw_refused['replay']=='PASS' and raw_refused['status']=='FAIL','rehash_G6':replay_refused['admission']=='PASS' and replay_refused['replay']=='FAIL' and replay_refused['status']=='FAIL','syntax_G2':syntax['G1']=='PASS' and syntax['V2']=='PASS' and syntax['status']=='FAIL','zero_G2':zero['status']=='PASS' and zero['record']['value']==0,'G5_relation':relation['status']=='RELATIONAL_WITNESS' and all(p['conformance']=='PASS' for p in relation['profiles']),'decimal_regression':num_dec['status']=='outside_tolerance','binary_regression':num_bin['status']=='indeterminate_boundary'}
r={'schema':'codeprobe-a2-p7a-gate-evidence/v1','revision':'P7-R4-review-candidate+a2p7a.1','status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'G2_syntax':syntax,'G2_zero':zero,'G5_relation':relation,'G6_bound':good,'G6_alias_refused':raw_refused,'G6_rehashed_refused':replay_refused,'numeric_decimal':num_dec,'numeric_binary64':num_bin,'historical_crosswalk':'Fig1 W1->P6-C02/W3 syntax;W2->W1 coordinate;W3->W3 profile relation;W4->W2 alias;W5->W4 replay; executable W5 supplementary retained','scope':'New G2/G5/G6 typed receipts and two numeric regressions. Coordinate and extra slot witnesses remain exercised by the unchanged legacy suite. This is not A17, prevalence evidence or final article certification.'};store('summary.json',r);print(json.dumps({'status':r['status'],'checks':len(checks)}));sys.exit(r['status']!='PASS')
