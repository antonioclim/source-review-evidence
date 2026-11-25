"""Run frozen pilot cells; outcomes contain all arm-side combinations, including errors."""
import argparse,sys,time,datetime
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import load,save,sha
from arms import execute

def work(source,data,cells,out):
    sys.path.insert(0,str(source/'src'))
    import codeprobe_measurement_kernel as k
    import codeprobe_interpretation as ip
    import codeprobe_evidence_gates as g
    import codeprobe_s01_observation_adapter as a
    import codeprobe_review_contract as consumer
    import codeprobe_numeric_policy as num
    mods=(k,ip,g,a,consumer,num);rows=[]
    for ident,sides in cells:
        control=load(data/'records'/f'{ident}_healthy.json')
        for side in sides:
            d=load(data/'records'/f'{ident}_{side}.json')
            for arm in ('B0','B1','B2'):
                t=time.perf_counter();row={'cell_id':ident,'side':side,'arm':arm,'input_sha256':sha((data/'records'/f'{ident}_{side}.json').read_bytes()),'start_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
                try:v,details=execute(d,control,arm,mods);row.update(predicate_vector=v,details=details,status='OBSERVED')
                except Exception as e:row.update(status='UNRESOLVED',error_type=type(e).__name__,error=str(e))
                row['elapsed_seconds']=time.perf_counter()-t;rows.append(row)
    save(out,rows);print(len(rows),'rows',sum(x['status']=='UNRESOLVED' for x in rows),'errors')
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--data',type=Path,required=True);ap.add_argument('--cells',required=True);ap.add_argument('--out',type=Path,required=True);ar=ap.parse_args()
    cells=[(part.split(':')[0],part.split(':')[1].split(',')) for part in ar.cells.split(';')]
    work(ar.source,ar.data,cells,ar.out)
