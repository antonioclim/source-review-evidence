"""Construct immutable study inputs and analytic expectations; no parser or product imports.
The generator never executes its emitted Python sources. Reference expectations are
specified by the grammar, integer arithmetic and the approved P6 recipe constants.
"""
from __future__ import annotations
import json, hashlib
from pathlib import Path


def dump(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as f:
        f.write(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + '\n')


def oracle(family: int, variant: int):
    n=variant; name=f'a18_f{family}_v{variant}'
    ex=[]
    if family == 1:
        cond=' and '.join(f'a{i}' for i in range(n+1))
        lines=[f'@wrap(1 if ({cond}) else 0)', '@wrap(2 if flag else 3)', f'def {name}(x):', '    return x']
        ex=[dict(name=name,start=3,end=4,traversal_start=1,dp=n+2,depth=0)]
    elif family == 2:
        cond=' or '.join(f'a{i}' for i in range(n+1))
        lines=[f'def {name}(*, x=({cond})):', '    return x']
        ex=[dict(name=name,start=1,end=2,traversal_start=1,dp=n,depth=0)]
    elif family == 3:
        cond=' and '.join(f'a{i}' for i in range(n+1))
        lines=[f'def {name}(x: (A if flag else B)=({cond})) -> (A or B):', '    if x:', '        return 1', '    return 0']
        ex=[dict(name=name,start=1,end=4,traversal_start=1,dp=n+3,depth=1)]
    elif family == 4:
        inner=f'inner_{name}'; method=f'method_{name}'
        lines=[f'def {name}(x):', f'    def {inner}(y):']
        for i in range(n): lines += [f'        if y == {i}:', f'            return {i}']
        lines+=['        return -1']; iend=len(lines)
        lines+=['    class Local:',f'        def {method}(self, y):','            if y and flag:', '                return y','            return 0']; mend=len(lines); mstart=mend-3
        lines+=['    fn = lambda z: 1 if (z and flag) else 0',f'    return {inner}(x)']
        ex=[dict(name=name,start=1,end=len(lines),traversal_start=1,dp=0,depth=0),dict(name=inner,start=2,end=iend,traversal_start=2,dp=n,depth=1),dict(name=method,start=mstart,end=mend,traversal_start=mstart,dp=2,depth=1)]
    elif family == 5:
        cond=' and '.join(f'a{i}' for i in range(n+1))
        lines=[f'async def {name}(xs, ys):','    async for x in xs:','        for y in ys:',f'            while {cond}:','                break','    return 0']
        ex=[dict(name=name,start=1,end=len(lines),traversal_start=1,dp=n+3,depth=3)]
    elif family == 6:
        filters=' '.join(f'if x > {i}' for i in range(n))
        lines=[f'def {name}(xs, ys):',f'    return [(x if flag else y) for x in xs {filters} for y in ys if y]']
        ex=[dict(name=name,start=1,end=2,traversal_start=1,dp=n+4,depth=0)]
    elif family == 7:
        lines=[f'def {name}(x, flag):','    match x:']
        for i in range(n): lines += [f'        case {i} if flag and x:',f'            return {i}']
        lines+=['        case _:', '            return -1']
        ex=[dict(name=name,start=1,end=len(lines),traversal_start=1,dp=2*n+1,depth=1)]
    else:
        lines=[f'def {name}(x):','    try:', '        if x:', '            x += 1']
        for i in range(n): lines += [f'    except E{i}:',f'        x = {i}']
        lines+=['    else:', '        if x:', '            x += 1', '    finally:', '        while x:', '            x -= 1', '    return x']
        ex=[dict(name=name,start=1,end=len(lines),traversal_start=1,dp=n+3,depth=2)]
    source='\n'.join(lines)+'\n'
    return {'id':f'O{family}-V{variant}','family':family,'variant':variant,'source':source,'expected':ex,'source_sha256':hashlib.sha256(source.encode()).hexdigest()}


def construct(root: Path):
    data=root/'data'; data.mkdir(exist_ok=True)
    pilot=json.loads((root/'design/PilotCells_v1.json').read_text())['cells']
    cases=[]; expectations=[]
    default='def f(x):\n    if x:\n        return 1\n    return 0\n'
    for recipe in pilot:
        ident=recipe['id']; f=int(ident[1]); v=int(ident[-1]); p=recipe['parameters']
        c={'id':ident,'family':recipe['family'],'variant':recipe['variant'],'parameters':p,'healthy_source':default,'challenge_source':default,'language':'python','path':f'pilot/{ident}.py','observation':'python.callable.mccabe_complexity','entity_name':'f'}
        healthy={}; challenge={}
        if f==1:
            c.update(healthy_source='def f():\n    return 0\n',challenge_source=p['source'],observation='python.function_definition_count',entity_name=None)
            healthy={'state':'observed','value':1}; challenge={'state':'unavailable','value':None}
        elif f==2:
            c.update(healthy_source='def f():\n    return 0\n',observation='python.function_definition_count',entity_name=None)
            c['challenge_source']=['pass\n','plain text\n','','def f(:\n'][v-1]
            if v==2:c['language']='text';c['healthy_source']='plain healthy text\n'
            if v==3:c['observation']='source.mean_line_length_codepoints';c['healthy_source']='a\n'
            healthy={'state':'observed' if v!=2 else 'not_applicable','value':1 if v!=2 else None}
            challenge={'state':['observed','not_applicable','insufficient_evidence','unavailable'][v-1],'value':0 if v==1 else None}
        elif f==3:
            c['healthy_source']=c['challenge_source']=[ '@wrap(1 if flag else 2)\ndef f(x):\n    return x\n', 'def f(x=(1 if flag else 2)):\n    return x\n','def f(x: (A or B)):\n    return x\n', default][v-1]
            c['required_line']=[1,1,1,2][v-1];c['narrow_line']=[3,2,2,1][v-1]
            healthy={'schema':'PASS','binding':'PASS','coverage':'PASS'};challenge={'schema':'PASS','binding':'PASS','coverage':'FAIL'}
        elif f==4:
            lines=['def f(x):']
            for i in range(12): lines += [f'    if x == {i}:',f'        return {i}']
            lines+=['    return -1'];c['healthy_source']=c['challenge_source']='\n'.join(lines)+'\n'
            pairs=[[[8,10,12],[14,16,18]],[[12,13,14],[14,16,18]],[[8,10,12],[12,13,14]],[[12,12,12],[13,13,13]]]
            c['profile_thresholds']=pairs[v-1]
            def status(t): return 'no_rule_trigger' if 13<=t[0] else 'review_opportunity' if 13>t[2] else 'abstain'
            healthy={'value':13,'decisions':[status(c['profile_thresholds'][0])]*2,'relation':'NO_DIFFERENCE'}
            challenge={'value':13,'decisions':[status(t) for t in c['profile_thresholds']],'relation':'RELATIONAL_WITNESS'}
        elif f==5:
            c['healthy_source']=c['challenge_source']=p['source'];healthy={'consumer':'PASS'};challenge={'consumer':'FAIL'}
        elif f==6:
            c['narrow_line']=1
            healthy={'schema':'PASS','binding':'PASS','replay':'PASS'}
            challenge={'schema':'PASS','binding':'FAIL' if v in (2,3) else 'PASS','replay':'NOT_EVALUATED' if v in (2,3) else 'FAIL'}
        elif f==7:
            c['healthy_source']='def f(x):\n    return x\n';c['challenge_source']=c['healthy_source']
            if v==1:c['challenge_source']='def f(x):\n    return x+1\n'
            if v==3:c['challenge_source']='\n'+c['healthy_source']
            c['challenge_path']=c['path']+'.other' if v==2 else c['path']
            healthy={'schema':'PASS','slot_same':True,'digest_same':True}
            challenge={'schema':'FAIL' if v==4 else 'PASS','slot_same':v in (1,2),'digest_same':v==2}
        else:
            c['numeric']={k:p[k] for k in ('left','right','at','rt','representation')}
            healthy={'numeric':'within_tolerance'};challenge={'numeric':p['expected_status']}
        cases.append(c)
        expectations.append({'id':ident,'healthy':healthy,'challenge':challenge,'primary_counterexample_eligible':not(f==6 and v in (2,3)) and not(f==7 and v==4),'incremental_check_candidate':f==3 or (f==6 and v in (1,4)), 'P6_recipe_divergence': 'Binding mismatch prevents replay; retain as invalid context, no gain' if f==6 and v in (2,3) else 'Unregistered specification version rejected; pure identity change remains a separate formal observation' if f==7 and v==4 else None})
    dump(data/'pilot_recipes.json',cases); dump(data/'pilot_expected.json',expectations)
    rows=[oracle(f,v) for f in range(1,9) for v in range(1,5)]
    dump(data/'oracle_inputs.json',[{k:v for k,v in r.items() if k!='expected'} for r in rows])
    dump(data/'oracle_expected.json',[{'id':r['id'],'expected':r['expected']} for r in rows])
    dump(data/'ANALYSIS_RULES.json',{'schema':'codeprobe-p7c-analysis/1','preserve_P6_design':True,'no_outcomes_read':True,'frozen_before_arm_execution':True,'score':'Only B2 executed added checks with B1 predecessor PASS qualify; NOT_ASSESSED is no false acceptance. F4 policy decisions are inferable in B1 and give no exclusive information win.','strict_continuation':'P6 all predecessor and binding controls valid is reported over all 32 cells; no silent subset replacement. Known source/profile/context challenges may cause this literal condition to fail. Report conditional family existence separately without promoting full continuation.','anticipated_recipe_conflicts':['F6-V2','F6-V3','F7-V4'],'P6_conflicts_status':'Static discrepancies disclosed before materialisation, not erased or amended into passing hypotheses.','no_A19_A20':True,'input_sources_never_executed':True,'seeds':[2026092006,2026092018],'random_sampling':False,'case_retention':'all32 per study including null, invalid and failed','repetitions':'fresh processes/directories for reproducibility; no independent data claim','provenance':'local hash freeze with timestamps, not external preregistration or signed trusted clock'})
    return {'pilot_cells':len(cases),'oracle_programs':len(rows),'oracle_callables':sum(len(r['expected']) for r in rows)}

if __name__=='__main__':
    print(json.dumps(construct(Path(__file__).resolve().parents[1])))
