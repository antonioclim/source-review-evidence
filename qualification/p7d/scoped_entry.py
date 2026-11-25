"""Run an inspected script with explicitly staged dependency data and no site.
The script executes software tests, never the instructions of generated sources.
The import observation records loaded module files, not native OS dependencies.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import runpy
import sys

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--site',type=Path,required=True)
p.add_argument('--receipt',type=Path,required=True)
p.add_argument('target',nargs=argparse.REMAINDER)
a=p.parse_args()
if not sys.flags.isolated or not sys.flags.no_site:
    p.error('requires -I -S')
if not a.target or a.target[0]!='--' or len(a.target)<2:
    p.error('target must follow --')
site=a.site.resolve()
if not site.is_dir() or a.receipt.exists():
    p.error('missing stage or receipt exists')
sys.path.insert(0,str(site));sys.argv=a.target[1:]
rc=0;error=None
try:
    runpy.run_path(sys.argv[0],run_name='__main__')
except SystemExit as exc:
    rc=exc.code if isinstance(exc.code,int) else int(exc.code is not None)
except BaseException as exc:
    rc=1;error=repr(exc)
    import traceback
    traceback.print_exc()
finally:
    records=[]
    for name,module in sorted(sys.modules.items()):
        f=getattr(module,'__file__',None)
        if f and Path(f).is_file():
            path=Path(f).resolve()
            records.append({'module':name,'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                            'staged_dependency':site in path.parents})
    receipt={'schema':'codeprobe-p7d-scoped-imports/1','isolated':True,'no_site':True,
             'site_directory':str(site),'sys_path':sys.path,'returncode':rc,'error':error,'modules':records,
             'loaded_staged_modules':sum(r['staged_dependency'] for r in records),
             'same_host_and_stdlib':True,'Q07':'NOT_QUALIFIED'}
    a.receipt.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
raise SystemExit(rc)
