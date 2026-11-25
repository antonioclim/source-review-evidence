#!/usr/bin/env python3
"""Parser-independent model oracle for the finite callable-metric domain.

The oracle does not import ast, tokenize, libcst or another parser. It creates
programmes from fixed source templates whose expected callable spans and
control metrics are part of the generator specification, then compares those
expectations with the production measurement kernel.
"""
from __future__ import annotations
import argparse, importlib, json, sys
from pathlib import Path
from typing import Any

SCHEMA='codeprobe-p7-parser-independent-oracle/v1'

def _templates(index:int)->tuple[str,list[dict[str,Any]],str]:
    root=f'f{index}'; inner=f'inner{index}'; method=f'method{index}'
    kind=index % 16
    if kind==0:
        lines=[f'def {root}(x):','    return x']
        ex=[dict(name=root,start=1,end=2,traversal_start=1,dp=0,depth=0)]
        label='straight_line'
    elif kind==1:
        lines=[f'def {root}(x):','    if x:','        return 1','    return 0']
        ex=[dict(name=root,start=1,end=4,traversal_start=1,dp=1,depth=1)]
        label='if'
    elif kind==2:
        lines=[f'def {root}(x, flag):','    if x and flag:','        return 1','    return 0']
        ex=[dict(name=root,start=1,end=4,traversal_start=1,dp=2,depth=1)]
        label='if_boolop'
    elif kind==3:
        lines=[f'def {root}(x, y):','    if x:','        if y:','            return 1','    return 0']
        ex=[dict(name=root,start=1,end=5,traversal_start=1,dp=2,depth=2)]
        label='nested_if'
    elif kind==4:
        lines=[f'def {root}(xs):','    total = 0','    for x in xs:','        if x:','            total += 1','    return total']
        ex=[dict(name=root,start=1,end=6,traversal_start=1,dp=2,depth=2)]
        label='for_if'
    elif kind==5:
        lines=[f'def {root}(x):','    try:','        return 10 // x','    except ValueError:','        return 1','    except TypeError:','        return 2','    return 0']
        ex=[dict(name=root,start=1,end=8,traversal_start=1,dp=2,depth=1)]
        label='try_two_handlers'
    elif kind==6:
        lines=[f'def {root}(xs, ys):','    values = [x + y for x in xs if x for y in ys if y]','    return values']
        ex=[dict(name=root,start=1,end=3,traversal_start=1,dp=4,depth=0)]
        label='comprehension'
    elif kind==7:
        lines=[f'def {root}(x, flag):','    match x:','        case 0:','            return 0','        case y if y and flag:','            return y','    return -1']
        ex=[dict(name=root,start=1,end=7,traversal_start=1,dp=3,depth=1)]
        label='match_guard'
    elif kind==8:
        lines=[f'def {root}(cm, x):','    with cm:','        while x:','            x -= 1','    return x']
        ex=[dict(name=root,start=1,end=5,traversal_start=1,dp=1,depth=2)]
        label='with_while'
    elif kind==9:
        lines=['@wrap(flag if cond else alt)',f'def {root}(x):','    return x']
        ex=[dict(name=root,start=2,end=3,traversal_start=1,dp=1,depth=0)]
        label='decorator_ifexp'
    elif kind==10:
        lines=[f'def {root}(x=(1 if cond else 2)):','    return x']
        ex=[dict(name=root,start=1,end=2,traversal_start=1,dp=1,depth=0)]
        label='default_ifexp'
    elif kind==11:
        lines=[f'def {root}(x):',f'    def {inner}(y):','        if y:','            return 1','        return 0',f'    return {inner}(x)']
        ex=[dict(name=root,start=1,end=6,traversal_start=1,dp=0,depth=0),dict(name=inner,start=2,end=5,traversal_start=2,dp=1,depth=1)]
        label='nested_function_exclusion'
    elif kind==12:
        lines=[f'def {root}(x):','    fn = lambda y: 1 if y else 0','    return fn(x)']
        ex=[dict(name=root,start=1,end=3,traversal_start=1,dp=0,depth=0)]
        label='lambda_exclusion'
    elif kind==13:
        lines=[f'def {root}(x):','    class Local:',f'        def {method}(self, y):','            if y:','                return 1','            return 0','    return Local()']
        ex=[dict(name=root,start=1,end=7,traversal_start=1,dp=0,depth=0),dict(name=method,start=3,end=6,traversal_start=3,dp=1,depth=1)]
        label='class_subtree_exclusion'
    elif kind==14:
        lines=[f'async def {root}(xs):','    total = 0','    async for x in xs:','        total += 1','    return total']
        ex=[dict(name=root,start=1,end=5,traversal_start=1,dp=1,depth=1)]
        label='async_for'
    else:
        lines=[f'async def {root}(cm, x):','    async with cm:','        while x:','            x -= 1','    return x']
        ex=[dict(name=root,start=1,end=5,traversal_start=1,dp=1,depth=2)]
        label='async_with_while'
    return '\n'.join(lines)+'\n', ex, label

def run(source_root:Path,cases:int=256)->dict[str,Any]:
    sys.path.insert(0,str(source_root/'src'))
    mk=importlib.import_module('codeprobe_measurement_kernel')
    failures=[]; checks=0; labels={}
    for i in range(cases):
        source, expected, label=_templates(i); labels[label]=labels.get(label,0)+1
        result=mk.measure_bytes(source.encode('utf-8'),language='python',path=f'oracle-{i}.py')
        evidence={e['evidence_id']:e for e in result['source_evidence']}
        recs={}
        for rec in result['observations']:
            if rec['entity']['entity_kind']=='python_callable':
                parts=rec['entity']['entity_id'].split(':')
                recs[(parts[2],rec['observation_id'])]=rec
        expected_names={e['name'] for e in expected}
        observed_names={k[0] for k in recs}
        checks+=1
        if observed_names!=expected_names:
            failures.append({'case':i,'label':label,'kind':'callable_set','expected':sorted(expected_names),'observed':sorted(observed_names)})
        for ex in expected:
            name=ex['name']
            metric_ids=('python.callable.physical_span_lines','python.callable.decision_point_count','python.callable.mccabe_complexity','python.callable.max_control_nesting_depth')
            try: vals={oid:recs[(name,oid)] for oid in metric_ids}
            except KeyError as err:
                failures.append({'case':i,'label':label,'kind':'missing_record','name':name,'record':str(err)}); continue
            got=(vals[metric_ids[0]]['value'],vals[metric_ids[1]]['value'],vals[metric_ids[2]]['value'],vals[metric_ids[3]]['value'])
            want=(ex['end']-ex['start']+1,ex['dp'],ex['dp']+1,ex['depth'])
            checks+=4
            if got!=want: failures.append({'case':i,'label':label,'kind':'metrics','name':name,'expected':want,'observed':got})
            phys=evidence[vals[metric_ids[0]]['source_evidence_ids'][0]]
            trav=evidence[vals[metric_ids[1]]['source_evidence_ids'][0]]
            checks+=4
            if (phys['start_line'],phys['end_line'])!=(ex['start'],ex['end']):
                failures.append({'case':i,'label':label,'kind':'physical_span','name':name,'expected':[ex['start'],ex['end']],'observed':[phys['start_line'],phys['end_line']]})
            if (trav['start_line'],trav['end_line'])!=(ex['traversal_start'],ex['end']):
                failures.append({'case':i,'label':label,'kind':'traversal_span','name':name,'expected':[ex['traversal_start'],ex['end']],'observed':[trav['start_line'],trav['end_line']]})
            if not (trav['start_line']<=ex['traversal_start']<=ex['end']<=trav['end_line']):
                failures.append({'case':i,'label':label,'kind':'coverage','name':name})
    return {'schema':SCHEMA,'oracle_mechanism':'source-template generator with embedded expectations; no parser imported','production_parser':'CPython ast inside candidate kernel','cases':cases,'template_distribution':labels,'checks':checks,'failures':failures,'status':'PASS' if not failures else 'FAIL','limitations':['The generator covers a declared finite grammar, not all valid Python.','The source is still executed by the same Python runtime after measurement; the expectation mechanism itself does not consume an AST.']}

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--source-root',type=Path,required=True); ap.add_argument('--cases',type=int,default=256); ap.add_argument('--output',type=Path)
    a=ap.parse_args(); out=run(a.source_root.resolve(),a.cases); text=json.dumps(out,indent=2,sort_keys=True)+'\n'
    if a.output: a.output.write_text(text,encoding='utf-8')
    else: print(text,end='')
    return 0 if out['status']=='PASS' else 1
if __name__=='__main__': raise SystemExit(main())
