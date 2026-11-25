#!/usr/bin/env python3
"""Bound only this local test process; exercise explicit no-verdict resource paths."""
from pathlib import Path
import argparse,json,resource,sys,time
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,512*1024*1024));resource.setrlimit(resource.RLIMIT_CPU,(5,5))
sys.path.insert(0,str(a.root/'source/src'));import codeprobe_numeric_policy as n
rows=[];t=time.perf_counter()
for val in ('1e100000000','1e-100000000'):
 try:r=n.compare_decimal(val,'0',absolute_tolerance='1',relative_tolerance='0',max_work_digits=1000);status=r['status']
 except n.NumericResourceError as e:status=e.status
 rows.append({'input':val,'observed':status,'pass':status=='RESOURCE_REFUSED'})
for limit in (0,False,-1,'100'):
 try:n.compare_decimal('0','0',absolute_tolerance='0',relative_tolerance='0',max_work_digits=limit);ok=False
 except ValueError:ok=True
 rows.append({'budget':limit,'expected':'ValueError','pass':ok})
from decimal import Decimal
x=10**4500+123;r=n.compare_decimal(x,x,absolute_tolerance=0,relative_tolerance=0)
rows.append({'integer_decimal_digits':4501,'explicit_budget':None,'pass':r['status']=='within_tolerance' and Decimal(r['left'])==Decimal(x)})
r={'scope':'One Linux test process, existing Python; no global availability/sandbox claim','address_space_cap_bytes':512*1024*1024,'CPU_seconds_cap':5,'elapsed_seconds':time.perf_counter()-t,'rows':rows,'cases':len(rows),'status':'PASS' if all(r['pass'] for r in rows) else 'FAIL'};a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r));sys.exit(r['status']!='PASS')
