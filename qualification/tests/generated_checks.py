#!/usr/bin/env python3
"""Generated finite-domain checks: integer oracle, rational points and gate tables.

No input programme is executed. Test rows are written in full and are not an
independent statistical sample. No pilot A17 or extension A18 is run here.
"""
from pathlib import Path
from decimal import Decimal, localcontext
from fractions import Fraction
import argparse,copy,decimal,hashlib,importlib.util,itertools,json,math,sys,time
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--model',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);root=a.root.resolve();sys.path.insert(0,str(root/'source/src'))
import codeprobe_numeric_policy as n
import codeprobe_evidence_gates as g
import codeprobe_interpretation as ip
s=importlib.util.spec_from_file_location('p6_reference',a.model);model=importlib.util.module_from_spec(s);s.loader.exec_module(model)
rows=[];bad=[];start=time.perf_counter()
def add(group,case,checks,details):
 r={'group':group,'case':case,'checks':checks,'pass':all(checks.values()),'details':details};rows.append(r)
 if not r['pass']:bad.append({'group':group,'case':case,'failed':[k for k,v in checks.items() if not v]})
def ratio(text):
 v=Decimal(text); sign,digits,exp=v.as_tuple();i=0
 for d in digits:i=10*i+d
 i=-i if sign else i
 return (i*10**exp,1) if exp>=0 else (i,10**(-exp))
def exact_status(a,b,at,rt):
 # Integer pairs and cross-products. No production helpers or Fraction arithmetic.
 an,ad=ratio(a);bn,bd=ratio(b);tn,td=ratio(at);rn,rd=ratio(rt)
 dn,dd=abs(an*bd-bn*ad),ad*bd
 mn,md=(abs(an),ad) if abs(an)*bd>=abs(bn)*ad else (abs(bn),bd)
 un,ud=rn*mn,rd*md
 if tn*ud>=un*td:un,ud=tn,td
 return 'within_tolerance' if dn*ud<=un*dd else 'outside_tolerance'
tols=[('0','0'),('1e-10','1e-12'),('1','0'),('0','0.1')]
for coefficient,exponent in itertools.product(range(-30,31),(-40,-1,0,30)):
 x=f'{coefficient}e{exponent}'
 for yc,ye in ((coefficient,exponent),(coefficient+1,exponent),(-coefficient,exponent),(coefficient+2,exponent-1)):
  y=f'{yc}e{ye}'
  for at,rt in tols:
   r=n.compare_decimal(x,y,absolute_tolerance=at,relative_tolerance=rt)
   rev=n.compare_decimal(y,x,absolute_tolerance=at,relative_tolerance=rt)
   av,bv=Fraction(Decimal(x)),Fraction(Decimal(y));tv=max(Fraction(Decimal(at)),Fraction(Decimal(rt))*max(abs(av),abs(bv)))
   add('decimal_integer_oracle',len(rows),{'status':r['status']==exact_status(x,y,at,rt),'left_exact':Fraction(Decimal(r['left']))==av,'right_exact':Fraction(Decimal(r['right']))==bv,'delta_exact':Fraction(Decimal(r['delta']))==abs(av-bv),'tolerance_exact':Fraction(Decimal(r['tolerance']))==tv,'symmetry':all(r[k]==rev[k] for k in ('status','delta','tolerance'))},{'inputs':[x,y,at,rt],'output':r})
# Contexts and traps cannot change completed exact comparison or caller flags.
ctx_inputs=[('1.0000000000000000000000000001','0','1','0'),('-123.456789012345678901234567891','0','123','0'),('1e-1000','-2e-1000','2e-1000','1e-3')]
rounds=[decimal.ROUND_CEILING,decimal.ROUND_DOWN,decimal.ROUND_FLOOR,decimal.ROUND_HALF_DOWN,decimal.ROUND_HALF_EVEN,decimal.ROUND_HALF_UP,decimal.ROUND_UP,decimal.ROUND_05UP]
for prec,rounding,traps,args in itertools.product((2,7,28,29,50,80),rounds,(False,True),ctx_inputs):
 ref=n.compare_decimal(args[0],args[1],absolute_tolerance=args[2],relative_tolerance=args[3])
 with localcontext() as ctx:
  ctx.prec=prec;ctx.rounding=rounding
  for key in ctx.traps:ctx.traps[key]=traps
  ctx.clear_flags();flags=dict(ctx.flags)
  try:r=n.compare_decimal(args[0],args[1],absolute_tolerance=args[2],relative_tolerance=args[3]);err=None
  except Exception as exc:r=None;err=type(exc).__name__+':'+str(exc)
  add('decimal_context',len(rows),{'output_identical':r==ref,'flags_unchanged':flags==dict(ctx.flags)},{'prec':prec,'rounding':rounding,'traps':traps,'inputs':args,'error':err})
values=[0.0,-0.0,float.fromhex('0x0.0000000000001p-1022'),-float.fromhex('0x0.0000000000001p-1022'),0.1,-0.1,1.0,math.nextafter(1.0,0.0),2.0,sys.float_info.max,sys.float_info.min,math.nextafter(sys.float_info.min,0.0)]
btols=[('0','0'),('1e-323','0'),('1e-12','0'),('0','1e-12'),('1','0'),('0','1')]
subs=0
for x,y,(at,rt) in itertools.product(values,values,btols):
 r=n.compare_binary64(x,y,absolute_tolerance=at,relative_tolerance=rt)
 ax,by=Fraction.from_float(x),Fraction.from_float(y);rx,ry=Fraction.from_float(math.ulp(x))/2,Fraction.from_float(math.ulp(y))/2
 lo,hi=map(lambda s:Fraction(Decimal(s)),r['delta_interval']);tl,th=map(lambda s:Fraction(Decimal(s)),r['tolerance_interval']);conservative=True;decisive=True
 for vx,vy in itertools.product((ax-rx,ax,ax+rx),(by-ry,by,by+ry)):
  d=abs(vx-vy);t=max(Fraction(Decimal(at)),Fraction(Decimal(rt))*max(abs(vx),abs(vy)));subs+=1
  conservative &= lo<=d<=hi and tl<=t<=th
  if r['status']=='within_tolerance':decisive &= d<=t
  if r['status']=='outside_tolerance':decisive &= d>t
 ref=model.binary_comparison(x,y,at,rt)
 add('binary_interval_points',len(rows),{'bounds_contain_points':conservative,'categorical_soundness_on_points':decisive,'reference_status':r['status']==ref['status'],'reference_bounds':r['delta_interval']==[ref['delta_low'],ref['delta_high']] and r['tolerance_interval']==[ref['tolerance_low'],ref['tolerance_high']]},{'x_hex':x.hex(),'y_hex':y.hex(),'tolerances':[at,rt],'output':r})
for g1,state,val,reason_ok in itertools.product(('PASS','FAIL','NOT_EVALUATED','INVALID_INPUT'),('observed','unavailable','not_applicable','insufficient_evidence'),(None,0,1),(False,True)):
 rec={'value':val,'applicability':{'state':state,'reason_code':'R' if reason_ok and state!='observed' else '', 'reason':'typed reason' if reason_ok and state!='observed' else ''}}
 valid=(state=='observed')==(val is not None) and (state=='observed' or reason_ok)
 expected='INVALID_INPUT' if g1=='INVALID_INPUT' else 'NOT_EVALUATED' if g1!='PASS' else 'INVALID_INPUT' if not valid else 'PASS' if state=='observed' else 'FAIL'
 add('G2_status_table',len(rows),{'truth':g.availability_status(g1,rec)==expected,'V2':g.representation_status(rec)==('PASS' if valid else 'INVALID_INPUT')},{'g1':g1,'record':rec,'expected':expected})
for admission,replay,context in itertools.product(g.STATES,g.STATES,(False,True)):
 expected=('INVALID_INPUT' if not context or 'INVALID_INPUT' in (admission,replay) else 'FAIL' if 'FAIL' in (admission,replay) else 'PASS' if admission==replay=='PASS' else 'NOT_EVALUATED')
 add('G6_status_table',len(rows),{'truth':g.consumer_full_status(admission,replay,same_context=context)==expected},{'admission':admission,'replay':replay,'context':context,'expected':expected})
for branches in range(0,26):
 src=('def f(x):\n'+''.join(f'    if x == {i}:\n        x += 1\n' for i in range(branches))+'    return x\n').encode()
 r=g.compare_profiles(src,observation_id='python.callable.mccabe_complexity',profile_ids=('structural-review','structural-review-conservative'))
 add('G5_real_profiles',branches,{'value':r['value']==branches+1,'both_conformant':all(p['conformance']=='PASS' for p in r['profiles']),'relation_label':r['status']==('NO_DIFFERENCE' if r['profiles'][0]['decision']==r['profiles'][1]['decision'] else 'RELATIONAL_WITNESS')},{'source_sha256':hashlib.sha256(src).hexdigest(),'branches':branches,'result':r})
summary={'schema':'codeprobe-p7a-generated-tests/1','status':'PASS' if not bad else 'FAIL','cases':len(rows),'checks':sum(len(r['checks']) for r in rows),'failures':bad,'groups':{g:sum(r['group']==g for r in rows) for g in sorted({r['group'] for r in rows})},'point_substitutions':subs,'elapsed_seconds':time.perf_counter()-start,'counts_overlap':True,'P6_model_sha256':hashlib.sha256(a.model.read_bytes()).hexdigest(),'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary));sys.exit(bool(bad))
