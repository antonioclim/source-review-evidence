"""Executable B0/B1/B2 projections for the retained P7C pilot.
All arms receive the same supplied case data. The family digit in cell_id
selects the checks executed by each projection. Expected-result files are not
read here; predicates use the selected input contracts and source.
"""
from __future__ import annotations
import copy
from common import sha,canonical,traversal


def accepted(function,*args,**kwargs):
    try:function(*args,**kwargs);return 'PASS',None
    except (ValueError,TypeError,KeyError,IndexError,RecursionError) as e:return 'FAIL',str(e)


def record(d):
    return next(r for r in d['capsule']['measurement']['observations'] if r['record_id']==d['record_id'])


def structure(d,k,ip):
    k.validate_kernel_result(d['capsule']['measurement'])
    if d['capsule']['digest']!=ip.digest(ip.canonical({a:b for a,b in d['capsule'].items() if a!='digest'})):raise ValueError('capsule digest mismatch')


def binding(d,k,ip,g):
    req=d['request'];data=d['source'].encode();intake=k.intake_from_bytes(data,path=req['path'])
    cap=d['capsule'];art=cap['measurement']['artifact'];pid=req['profile_id'];p=ip.resolve_profile(pid,req['profile_sha256'])
    want={'raw_sha256':intake.raw_sha256,'normalised_sha256':intake.normalised_sha256,'language':req['language'],'path':req['path']}
    if any(art[key]!=v for key,v in want.items()):raise ValueError('source binding mismatch')
    prof={'profile_id':pid,'version':p['version'],'sha256':req['profile_sha256']}
    if cap['profile']!=prof or cap['context']!={'task_family':req['task_family']}:raise ValueError('profile binding mismatch')
    if cap['build']!=ip.build_identity():raise ValueError('build mismatch')
    ctx=d['carrier']['context']
    if any(ctx[key]!=v for key,v in want.items()) or ctx['profile']!=prof or ctx['producer_build']!=cap['build']:raise ValueError('carrier binding mismatch')
    if ctx['record_id']!=d['record_id'] or ctx['task_family']!=req['task_family'] or ctx['gate_component_sha256']!=g._core_hashes():raise ValueError('slot/core binding mismatch')


def coverage(d):
    from common import callable_index
    r=record(d);entity_id=r['entity']['entity_id']
    callables=callable_index(traversal(d['source']))
    if entity_id not in callables:raise ValueError('source callable identity is absent or inconsistent')
    actual=callables[entity_id]
    intervals=[e for e in d['capsule']['measurement']['source_evidence'] if e['evidence_id'] in r['source_evidence_ids']]
    missing=[s for s in actual['spans'] if not any(e['start_line']<=s[0] and e['end_line']>=s[1] for e in intervals)]
    return ('FAIL' if missing else 'PASS'),{'visited_spans':actual['spans'],'missing_spans':missing,'represented_intervals':intervals,'scope':'line containment under fixed visitor; not a minimal token slice'}


def execute(d,control,arm,modules):
    k,ip,g,a,consumer,num=modules
    f=int(d['cell_id'][1]);v={};details={}
    if f==8:
        x=d['numeric'];fun=num.compare_binary64 if x['representation']=='binary64' else num.compare_decimal
        left=float(x['left']) if x['representation']=='binary64' else x['left'];right=float(x['right']) if x['representation']=='binary64' else x['right']
        result=fun(left,right,absolute_tolerance=x['at'],relative_tolerance=x['rt'])
        return {'numeric':result['status']},{'comparison':result,'same_comparator_in_all_arms':True}
    if f==4:
        recs=[next(r for r in c['measurement']['observations'] if r['observation_id']==d['observation_id']) for c in d['capsules']]
        v['value']=recs[0]['value']
        if arm=='B0':v.update(relation='NOT_ASSESSED',decisions='NOT_ASSESSED');return v,{}
        for cap in d['capsules']:
            k.validate_kernel_result(cap['measurement']);ip.resolve_profile(cap['profile']['profile_id'],cap['profile']['sha256'])
        decisions=[]
        for rec,p in zip(recs,d['profiles']):
            levels=next(r for r in p['rules'] if r['observation_id']==rec['observation_id'])['threshold_set'];x=rec['value']
            decisions.append('no_rule_trigger' if x<=levels['lower'] else 'review_opportunity' if x>levels['upper'] else 'abstain')
        v.update(decisions=decisions,relation='RELATIONAL_WITNESS' if decisions[0]!=decisions[1] else 'NO_DIFFERENCE')
        details['retained_profiles']=d['profiles'];details['qualification']='Decisions algebraically inferable from retained values/thresholds; no exclusive B2 information credited'
        if arm=='B2':
            actual=g.compare_profiles(d['source'].encode(),observation_id=d['observation_id'],profile_ids=tuple(p['profile_id'] for p in d['profiles']),language=d['language'],path=d['path'])
            v.update(relation=actual['status'],decisions=[p['decision']['status'] for p in actual['profiles']]);details['executed_profiles']=actual
        return v,details
    r=record(d)
    v['value']=r['value']
    if arm=='B0':
        v['state']='NOT_ASSESSED'
        for key in ('schema','binding','coverage','consumer','replay','slot_same','digest_same'):v[key]='NOT_ASSESSED'
        return v,{'specification_id':r['specification_id'],'missing_values_are_not_admitted':True}
    v['schema'],err=accepted(structure,d,k,ip)
    if err:details['schema_error']=err
    v['state']=r['applicability']['state'];v['V2']=g.representation_status(r)
    if f in (1,2):
        v['availability']='PASS' if v['state']=='observed' else 'FAIL'
        if arm=='B2':
            actual=g.evaluate_availability(d['source'].encode(),language=d['language'],observation_id=d['observation_id'],path=d['path'])
            v['availability']=actual['status'];details['availability']=actual
    if f in (3,6):
        v['binding'],err=accepted(binding,d,k,ip,g)
        if err:details['binding_error']=err
        v['coverage']='NOT_ASSESSED';v['replay']='NOT_ASSESSED'
        if arm=='B2':
            if v['schema']=='PASS' and v['binding']=='PASS':
                v['coverage'],details['coverage']=coverage(d)
                actual=g.qualify_consumer(d['carrier'],d['capsule'],d['source'].encode(),record_id=d['record_id'],**d['request'])
            else:
                actual=g.qualify_consumer(d['carrier'],d['capsule'],d['source'].encode(),record_id=d['record_id'],**d['request'])
            v['replay']=actual['replay'];details['G6']=actual
            v['replay']='NOT_EVALUATED' if actual['context_binding']=='INVALID_INPUT' else actual['replay']
    if f==5:
        v['consumer'],err=accepted(consumer._validate_observation,d['carrier']['observation'],0)
        if err:details['consumer_error']=err
        if arm=='B2':
            actual=g.qualify_consumer(d['carrier'],d['capsule'],d['source'].encode(),record_id=d['record_id'],**d['request']);details['G6']=actual
    if f==7:
        cr=record(control)
        v['slot_same']=r['record_id']==cr['record_id'];v['digest_same']=d['capsule']['measurement']['measurement_digest']==control['capsule']['measurement']['measurement_digest']
        details['identity_pair']={'control_slot':cr['record_id'],'challenge_slot':r['record_id'],'control_spec':cr['specification_id'],'challenge_spec':r['specification_id'],'control_digest':control['capsule']['measurement']['measurement_digest'],'challenge_digest':d['capsule']['measurement']['measurement_digest'],'path_is_separately_bound':True}
    return v,details
