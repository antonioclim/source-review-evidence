import json,sys,hashlib
from pathlib import Path
import coverage
root=Path(sys.argv[1]);cand=Path(sys.argv[2]);out=Path(sys.argv[3]);out.mkdir(parents=True,exist_ok=True)
config=json.loads((root/'config.json').read_text());core=config['core']
events=[]
for f in (root/'processes').glob('*.jsonl'):
 for line in f.read_text().splitlines():
  try:events.append(json.loads(line))
  except json.JSONDecodeError:events.append({'kind':'malformed_event','file':str(f)})
actual={name:hashlib.sha256((cand/'source/src'/name).read_bytes()).hexdigest() for name in core}
bound={e['file']:e for e in events if e['kind']=='core_load' and actual.get(Path(e['file']).name)==e['sha256']}
co=coverage.Coverage(data_file=str(out/'combined'),branch=True,config_file=False);data=co.get_data();nfiles=0;arcs={};omitted=[]
for f in (root/'processes').glob('.coverage.*'):
 d=coverage.CoverageData(basename=str(f));d.read();nfiles+=1
 for name in d.measured_files():
  bn=Path(name).name
  if bn in core:
   if name in bound:
    destination=str(cand/'source/src'/bn);arcs.setdefault(destination,set()).update(d.arcs(name) or [])
   else:omitted.append({'file':name,'data':f.name,'reason':'No exact hash-bound load'})
data.add_arcs({p:sorted(a) for p,a in arcs.items()});data.write();co.json_report(morfs=[str(cand/'source/src'/x) for x in core],outfile=str(out/'coverage.json'))
j=json.loads((out/'coverage.json').read_text());short={Path(k).name:v['summary'] for k,v in j['files'].items()}
starts={e['pid'] for e in events if e['kind']=='start'};saved={e['pid'] for e in events if e['kind'].startswith('coverage_saved')};loads={e['pid'] for e in events if e['kind']=='core_load'}
s={'files':short,'totals':j['totals'],'data_files':nfiles,'started_pids':len(starts),'saved_pids':len(saved),'core_loaded_pids':len(loads),'core_loaded_without_save':sorted(loads-saved),'started_without_save':sorted(starts-saved),'hash_bound_paths':len(bound),'unbound_core_paths_omitted':omitted,'warnings':[e for e in events if 'warning' in e['kind']],'launches':len([e for e in events if e['kind']=='launch'])}
(out/'summary.json').write_text(json.dumps(s,indent=2));print(json.dumps({k:v for k,v in s.items() if k not in ('warnings','unbound_core_paths_omitted')},indent=2))
