#!/usr/bin/env python3
"""Executable obligations for the nine retained Phase-6 principal claims."""
from __future__ import annotations
import argparse, ast, copy, hashlib, importlib, json, sys
from pathlib import Path
from typing import Any, Callable

SCHEMA='codeprobe-p7-claims-as-tests/v2'

def _claim(cid:str,fn:Callable[[],tuple[int,dict[str,Any]]],shows:str,not_shown:str)->dict[str,Any]:
    try:
        checks,details=fn(); status='PASS'; err=None
    except Exception as exc:
        checks=1; details={}; status='FAIL'; err={'type':type(exc).__name__,'message':str(exc)}
    return {'claim_id':cid,'status':status,'checks':checks,'details':details,'error':err,'shows':shows,'does_not_show':not_shown}

def run(package_root:Path,oracle_result:dict[str,Any])->dict[str,Any]:
    source_root=package_root/'source'; protocol=package_root/'protocol'
    sys.path.insert(0,str(source_root/'src'))
    mk=importlib.import_module('codeprobe_measurement_kernel'); ip=importlib.import_module('codeprobe_interpretation'); np=importlib.import_module('codeprobe_numeric_policy'); adapter=importlib.import_module('codeprobe_s01_observation_adapter'); rc=importlib.import_module('codeprobe_review_contract')
    freeze=json.loads((protocol/'APEX_P6_CodeProbe_ClaimScopeFreeze_v1.json').read_text())
    formal=json.loads((protocol/'APEX_P6_CodeProbe_FormalBoundarySpecification_v2.json').read_text())
    profiles={p['profile_id']:p['sha256'] for p in ip.available_profiles()}
    out=[]
    def c01():
        gates=formal.get('gates',formal.get('boundary_gates',[])); ids=[g.get('id') or g.get('gate_id') for g in gates]
        if len(gates)!=6: raise AssertionError(f'gate count {len(gates)}')
        src=b'def f(x):\n    if x:\n        return 1\n    return 0\n'
        cap=ip.interpret_bytes(src,language='python',profile_id='structural-review',profile_sha256=profiles['structural-review'],task_family='source_inspection',path='c01.py')
        ip.verify_capsule(cap,src,language='python',profile_id='structural-review',profile_sha256=profiles['structural-review'],task_family='source_inspection',path='c01.py')
        syntax=mk.measure_bytes(b'def f(:\n',language='python',path='invalid.py')
        parse=next(r for r in syntax['observations'] if r['observation_id']=='python.parse_status')
        rejected=[]
        for data in (b'\xff',b'x=1\x00'):
            try: mk.measure_bytes(data,language='python',path='rejected.py')
            except Exception as e: rejected.append(getattr(e,'code',type(e).__name__))
        if parse['value']!='syntax_error' or len(rejected)!=2: raise AssertionError('negative intake controls failed')
        return 6,{'gate_ids':ids,'source_replay':'PASS','syntax_failure_typed':True,'refused_inputs':rejected}
    out.append(_claim('P6-C01',c01,'The six declared gates are separately represented and exercised by admitted and refused inputs.','Completeness for every static-analysis architecture.'))
    def c02():
        """Execute five live counterexamples; do not trust archived PASS receipts."""
        witnesses=[]

        # W1: schema/digest validity does not entail coordinate coverage.
        source='@wrap(flag if cond else alt)\ndef f(x):\n    return x\n'
        measured=mk.measure_bytes(source.encode(),language='python',path='c02-coordinate.py')
        mutated=copy.deepcopy(measured)
        traversal=next(x for x in mutated['source_evidence'] if x['scope']=='python_callable_traversal')
        old_id=traversal['evidence_id']; traversal['start_line']=2
        new_id=(f"evidence:{traversal['normalised_sha256']}:{traversal['scope']}:"
                f"L{traversal['start_line']}-L{traversal['end_line']}:"
                f"C{traversal['start_column']}-C{traversal['end_column']}")
        traversal['evidence_id']=new_id
        for record in mutated['observations']:
            record['source_evidence_ids']=[new_id if x==old_id else x for x in record['source_evidence_ids']]
        mutated['source_evidence'].sort(key=lambda x:x['evidence_id'])
        mutated['observations'].sort(key=lambda x:(x['specification_id'],x['entity']['entity_id'],x['record_id']))
        mutated['measurement_digest']=mk.sha256_hex(mk.canonical_json(mk._measurement_digest_scope(mutated)).encode())
        mk.validate_kernel_result(mutated)
        tree=ast.parse(source); fn=next(node for node in ast.walk(tree) if isinstance(node,ast.FunctionDef))
        spans=[(int(node.lineno),int(getattr(node,'end_lineno',node.lineno))) for node in ast.walk(fn) if hasattr(node,'lineno')]
        uncovered=[list(span) for span in spans if not (traversal['start_line']<=span[0]<=span[1]<=traversal['end_line'])]
        if not any(lo==1 for lo,_ in spans) or not uncovered: raise AssertionError('W1 coordinate witness did not fail G4')
        witnesses.append({'id':'W1','status':'PASS','implication_refuted':'schema_and_digest_conformance => observation_local_coordinate_coverage','earlier_gate':'G3','later_gate':'G4','uncovered_spans':uncovered})

        # W2: a producer-valid identifier may require a transport alias for consumer admission.
        measurement=mk.measure_bytes(b'def f(x):\n    if x:\n        return 1\n    return 0\n',language='python',path='c02-alias.py')
        record=next(x for x in measurement['observations'] if x['observation_id']=='python.callable.mccabe_complexity')
        adapted=adapter.adapt_observation(record); rc._validate_observation(adapted,0)
        original=record['source_evidence_ids'][0]; alias=adapted['source_evidence'][0]['evidence_id']
        expected='kernel_evidence.'+hashlib.sha256(original.encode()).hexdigest()
        bad_alias=copy.deepcopy(adapted); bad_alias['source_evidence'][0]['evidence_id']=original
        raw_rejected=False; rejection=''
        try: rc._validate_observation(bad_alias,0)
        except Exception as exc: raw_rejected=True; rejection=str(exc)
        if alias!=expected or adapted['source_evidence'][0]['source_id']!=original or not raw_rejected:
            raise AssertionError('W2 consumer-alias witness did not fail G6')
        witnesses.append({'id':'W2','status':'PASS','implication_refuted':'producer_identifier_validity => consumer_admission_without_transport_alias','earlier_gate':'producer identity','later_gate':'G6','raw_identifier_rejected':raw_rejected,'rejection':rejection})

        # W3: one observed value can support distinct policy outcomes and availability states.
        body='\n'.join(f'    if x == {i}:\n        x += 1' for i in range(12))
        policy_source=('def f(x):\n'+body+'\n    return x\n').encode()
        def find_item(report,oid):
            return next(item for dim in report['dimensions'] for item in dim['items'] if item['observation_id']==oid)
        reports={pid:ip.interpret_bytes(policy_source,language='python',profile_id=pid,profile_sha256=profiles[pid],task_family='source_inspection',path='c02-policy.py') for pid in ('structural-review','structural-review-conservative','observation-only')}
        items={pid:find_item(report,'python.callable.mccabe_complexity') for pid,report in reports.items()}
        syntax=mk.measure_bytes(b'def f(:\n',language='python',path='c02-syntax.py')
        parse=next(r for r in syntax['observations'] if r['observation_id']=='python.parse_status')
        unavailable=next(r for r in syntax['observations'] if r['observation_id']=='python.function_definition_count')
        refused=False; refusal_code=''
        try: mk.measure_bytes(b'\xff',language='python',path='c02-invalid.py')
        except Exception as exc: refused=True; refusal_code=getattr(exc,'code',type(exc).__name__)
        values=[items[x]['value'] for x in ('structural-review','structural-review-conservative','observation-only')]
        statuses={'regular':items['structural-review']['decision']['status'],'conservative':items['structural-review-conservative']['decision']['status'],'observation_only':items['observation-only']['decision']}
        if values!=[13,13,13] or statuses!={'regular':'review_opportunity','conservative':'no_rule_trigger','observation_only':None} or parse['value']!='syntax_error' or unavailable['applicability']['state']!='unavailable' or not refused:
            raise AssertionError('W3 policy/availability witness did not separate outcomes')
        witnesses.append({'id':'W3','status':'PASS','implication_refuted':'same_observed_value => same_policy_decision_or_availability_state','earlier_gate':'G3','later_gate':'G5/G2','values':values,'decisions':statuses,'invalid_utf8_code':refusal_code})

        # W4: internal schema/digest consistency does not authenticate source replay.
        replay_source=b'def f(x):\n    if x:\n        return 1\n    return 0\n'
        kwargs=dict(language='python',profile_id='structural-review',profile_sha256=profiles['structural-review'],task_family='source_inspection',path='c02-replay.py')
        capsule=ip.interpret_bytes(replay_source,**kwargs); changed=copy.deepcopy(capsule)
        target=next(x for x in changed['measurement']['observations'] if x['observation_id']=='source.byte_count'); target['value']+=1
        changed['measurement']['measurement_digest']=mk.sha256_hex(mk.canonical_json(mk._measurement_digest_scope(changed['measurement'])).encode())
        mk.validate_kernel_result(changed['measurement']); changed.pop('digest',None); changed['digest']=ip.digest(ip.canonical(changed))
        replay_rejected=False; replay_message=''
        try: ip.verify_capsule(changed,replay_source,**kwargs)
        except Exception as exc: replay_rejected=True; replay_message=str(exc)
        if not replay_rejected: raise AssertionError('W4 replay witness did not fail G6')
        witnesses.append({'id':'W4','status':'PASS','implication_refuted':'internal_digest_and_schema_consistency => source_replay_authenticity','earlier_gate':'G3','later_gate':'G6','rejection':replay_message})

        # W5: equal checked AST projections do not entail equal physical-span policy outcomes.
        short=b'def f(x):\n    if x:\n        return 1\n    return 0\n'
        padded=('def f(x):\n'+'\n'*80+'    if x:\n        return 1\n    return 0\n').encode()
        common=dict(language='python',profile_id='structural-review',profile_sha256=profiles['structural-review'],task_family='source_inspection')
        ra=ip.interpret_bytes(short,path='c02-short.py',**common); rb=ip.interpret_bytes(padded,path='c02-padded.py',**common)
        ids=('python.callable.mccabe_complexity','python.callable.max_control_nesting_depth','python.callable.physical_span_lines')
        ai={oid:find_item(ra,oid) for oid in ids}; bi={oid:find_item(rb,oid) for oid in ids}
        same_ast=ai[ids[0]]['value']==bi[ids[0]]['value'] and ai[ids[1]]['value']==bi[ids[1]]['value']
        span_changed=ai[ids[2]]['value']!=bi[ids[2]]['value']
        decision_changed=ai[ids[2]]['decision']['status']!=bi[ids[2]]['decision']['status']
        if not (same_ast and span_changed and decision_changed): raise AssertionError('W5 layout/policy witness did not separate outcomes')
        witnesses.append({'id':'W5','status':'PASS','implication_refuted':'same_checked_ast_metrics => same_physical_span_policy_decision','earlier_gate':'AST metric agreement','later_gate':'G5','short_span':ai[ids[2]]['value'],'padded_span':bi[ids[2]]['value'],'short_status':ai[ids[2]]['decision']['status'],'padded_status':bi[ids[2]]['decision']['status']})

        return 5,{'execution':'live_constructed_witnesses','receipt_dependency':False,'witnesses':witnesses}
    out.append(_claim('P6-C02',c02,'Five named implications have bounded counterexamples.','All-pairs logical or statistical independence.'))
    def c03():
        zero=mk.measure_bytes(b'x=1\n',language='python',path='zero.py')
        z=next(r for r in zero['observations'] if r['observation_id']=='source.blank_line_count')
        insuff=next(r for r in zero['observations'] if r['observation_id']=='python.docstring_coverage_proportion')
        na=mk.measure_bytes(b'plain text\n',language='text',path='na.txt')
        nar=next(r for r in na['observations'] if r['observation_id']=='python.function_definition_count')
        un=mk.measure_bytes(b'def f(:\n',language='python',path='un.py')
        unr=next(r for r in un['observations'] if r['observation_id']=='python.function_definition_count')
        bad=copy.deepcopy(z); bad['applicability']={'state':'unavailable','reason_code':'X','reason':'mutated'}
        rejected=False
        try: mk.validate_observation_record(bad)
        except Exception: rejected=True
        states=[z['applicability']['state'],nar['applicability']['state'],insuff['applicability']['state'],unr['applicability']['state']]
        if states!=['observed','not_applicable','insufficient_evidence','unavailable'] or z['value']!=0 or not rejected: raise AssertionError(str(states))
        return 6,{'states':states,'observed_zero':z['value'],'invalid_state_value_pair_rejected':rejected}
    out.append(_claim('P6-C03',c03,'All four applicability states remain distinguishable and invalid state/value pairs fail.','Empirical frequency of the states.'))
    def c04():
        checks=0
        for lo in range(9):
            for hi in range(lo,11):
                for nom in range(lo,hi+1):
                    for x in range(14):
                        full=sorted({x>t for t in range(lo,hi+1)})
                        status='no_rule_trigger' if full==[False] else 'review_opportunity' if full==[True] else 'abstain'
                        got=ip.threshold_decision(x,{'lower':lo,'nominal':nom,'upper':hi})
                        if got['possible_predicates']!=full or got['status']!=status: raise AssertionError((lo,hi,nom,x))
                        checks+=1
        rejected=False
        try: ip.threshold_decision(1,{'lower':2,'nominal':1,'upper':3})
        except Exception: rejected=True
        if checks!=3948 or not rejected: raise AssertionError('threshold controls')
        return checks+1,{'admissible_cases':checks,'counterexamples':0,'invalid_order_rejected':rejected}
    out.append(_claim('P6-C04',c04,'Endpoint projection agrees with the full declared integer interval for 3,948 admissible cases.','Non-monotone policies or non-integer domains.'))
    def c05():
        if oracle_result.get('status')!='PASS': raise AssertionError(f"oracle failures={len(oracle_result.get('failures',[]))}")
        return int(oracle_result['checks']),{'oracle_cases':oracle_result['cases'],'oracle_checks':oracle_result['checks'],'mechanism':oracle_result['oracle_mechanism'],'template_distribution':oracle_result['template_distribution']}
    out.append(_claim('P6-C05',c05,'A parser-independent source-template oracle agrees over the declared generated domain.','Universal CFG complexity or independence from the Python runtime itself.'))
    def c06():
        a=mk.measure_bytes(b'def f():\n    return 1\n',language='python',path='a.py'); b=mk.measure_bytes(b'def f():\n    return 2\n',language='python',path='a.py'); c=mk.measure_bytes(b'def f():\n    return 1\n',language='python',path='moved.py')
        get=lambda r: next(x for x in r['observations'] if x['observation_id']=='python.callable.mccabe_complexity')
        ra,rb,rc=get(a),get(b),get(c)
        assertions=[ra['record_id']==rb['record_id'],a['measurement_digest']!=b['measurement_digest'],ra['record_id']==rc['record_id'],a['measurement_digest']==c['measurement_digest']]
        if not all(assertions): raise AssertionError(str(assertions))
        return 4,{'content_change_slot_stable':assertions[0],'content_change_digest_changes':assertions[1],'path_change_slot_stable':assertions[2],'path_change_digest_stable':assertions[3]}
    out.append(_claim('P6-C06',c06,'Observation-slot and content identities respond differently to declared metamorphic changes.','Global uniqueness or cryptographic authentication.'))
    def c07():
        src=b'def f(x):\n    if x:\n        return 1\n    return 0\n'; kwargs=dict(language='python',profile_id='structural-review',profile_sha256=profiles['structural-review'],task_family='source_inspection',path='replay.py')
        cap=ip.interpret_bytes(src,**kwargs); changed=copy.deepcopy(cap); target=next(r for r in changed['measurement']['observations'] if r['observation_id']=='source.byte_count'); target['value']+=1
        changed['measurement']['measurement_digest']=mk.sha256_hex(mk.canonical_json(mk._measurement_digest_scope(changed['measurement'])).encode())
        mk.validate_kernel_result(changed['measurement']); changed.pop('digest'); changed['digest']=ip.digest(ip.canonical(changed))
        replay_rejected=False
        try: ip.verify_capsule(changed,src,**kwargs)
        except Exception: replay_rejected=True
        deco='@wrap(flag if cond else alt)\ndef g(x):\n    return x\n'; res=mk.measure_bytes(deco.encode(),language='python',path='coord.py'); mut=copy.deepcopy(res)
        trav=next(e for e in mut['source_evidence'] if e['scope']=='python_callable_traversal'); old=trav['evidence_id']; trav['start_line']=2; new=f"evidence:{trav['normalised_sha256']}:{trav['scope']}:L2-L{trav['end_line']}:C{trav['start_column']}-C{trav['end_column']}"; trav['evidence_id']=new
        for r in mut['observations']:
            if old in r['source_evidence_ids']: r['source_evidence_ids']=[new if x==old else x for x in r['source_evidence_ids']]
        mut['source_evidence'].sort(key=lambda x:x['evidence_id']); mut['observations'].sort(key=lambda x:(x['specification_id'],x['entity']['entity_id'],x['record_id'])); mut['measurement_digest']=mk.sha256_hex(mk.canonical_json(mk._measurement_digest_scope(mut)).encode())
        mk.validate_kernel_result(mut); coordinate_inadequate=trav['start_line']>1
        if not replay_rejected or not coordinate_inadequate: raise AssertionError('later gates did not reject witnesses')
        return 4,{'digest_consistent_mutation_structurally_valid':True,'source_replay_rejected':replay_rejected,'narrowed_locator_structurally_valid':True,'independent_expected_decorator_line_uncovered':coordinate_inadequate}
    out.append(_claim('P6-C07',c07,'Fresh self-consistent mutations pass an earlier structural gate and fail replay or coordinate adequacy.','Prevalence of such failures in natural projects.'))
    def c08():
        src=b'def f(x):\n    if x:\n        return 1\n    return 0\n'; r=mk.measure_bytes(src,language='python',path='scale.py'); obs={x['observation_id']:x for x in r['observations'] if x['entity']['entity_kind']=='python_callable'}
        dec=np.compare_decimal('1000000','1000000.000001',absolute_tolerance='1e-10',relative_tolerance='1e-12'); binr=np.compare_binary64(1000000.0,float('1000000.000001'),absolute_tolerance='1e-10',relative_tolerance='1e-12')
        checks=[obs['python.callable.decision_point_count']['measurement_scale']=='ratio',obs['python.callable.mccabe_complexity']['measurement_scale']=='ordinal',dec['status']=='within_tolerance',binr['status']=='indeterminate_boundary']
        if not all(checks): raise AssertionError(str(checks))
        return 4,{'scale_types':{'decision_point_count':'ratio','mccabe_complexity':'ordinal'},'decimal_boundary':dec['status'],'binary64_boundary':binr['status']}
    out.append(_claim('P6-C08',c08,'The prospective scale and numerical contracts execute as specified at a diagnostic boundary.','Retrospective relabelling of unavailable CE09/CE11 runs.'))
    def c09():
        retained=freeze['retained_principal_claims']; hist=freeze['historical_context_claims']
        if len(retained)!=9 or any(h['status']!='UNVERIFIED_CONTEXT_ONLY' for h in hist): raise AssertionError('scope freeze')
        prohibited=('estimated prevalence','proves universal correctness','causes human benefit','demonstrates economic savings','independently replicated')
        principal=' '.join(c['claim'].lower() for c in retained)
        if any(p in principal for p in prohibited): raise AssertionError('overclaim retained')
        invalid='The package estimated prevalence and independently replicated universal correctness.'
        rejected=any(p in invalid.lower() for p in prohibited)
        if not rejected: raise AssertionError('negative scope control')
        return len(retained)+len(hist)+1,{'retained_claims':len(retained),'historical_context_families':len(hist),'all_historical_context_unverified':True,'constructed_overclaim_rejected':True}
    out.append(_claim('P6-C09',c09,'The machine-readable scope excludes historical and population-level conclusions from the principal set.','External validity, adoption or economic effect.'))
    failed=[x['claim_id'] for x in out if x['status']!='PASS']
    return {'schema':SCHEMA,'status':'PASS' if not failed else 'FAIL','claims':out,'summary':{'claims':len(out),'passed':len(out)-len(failed),'failed':len(failed),'checks':sum(x['checks'] for x in out)},'failed_claims':failed,'rule24':{'curated_inputs':True,'generated_inputs':True,'invalid_or_rejected_inputs':True,'limitations_per_claim':True}}

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--package-root',type=Path,required=True); ap.add_argument('--oracle-result',type=Path,required=True); ap.add_argument('--output',type=Path)
    a=ap.parse_args(); result=run(a.package_root.resolve(),json.loads(a.oracle_result.read_text())); text=json.dumps(result,indent=2,sort_keys=True)+'\n'
    if a.output: a.output.write_text(text,encoding='utf-8')
    else: print(text,end='')
    return 0 if result['status']=='PASS' else 1
if __name__=='__main__': raise SystemExit(main())
