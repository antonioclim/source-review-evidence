"""Materialise actual predecessor records. No B0/B1/B2 arm and no expectation read.
Production measurements/replays needed to construct bona fide carriers are logged
as preparation, never mislabelled as blind experiment outputs.
"""
from __future__ import annotations
import argparse,copy,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import load,save,sha,canonical

def rehash(k,ip,cap):
    m=cap['measurement'];m['measurement_digest']=k.sha256_hex(k.canonical_json(k._measurement_digest_scope(m)).encode())
    cap['digest']=ip.digest(ip.canonical({key:val for key,val in cap.items() if key!='digest'}))

def narrow(k,ip,cap,record,line):
    m=cap['measurement']; old=record['source_evidence_ids'][0]
    ev=next(e for e in m['source_evidence'] if e['evidence_id']==old)
    ev['start_line']=ev['end_line']=line
    ev['evidence_id']=f"evidence:{ev['normalised_sha256']}:{ev['scope']}:L{line}-L{line}:C{ev['start_column']}-C{ev['end_column']}"
    def swap(obj):
        if isinstance(obj,list):return [swap(x) for x in obj]
        if isinstance(obj,dict):return {key:swap(val) for key,val in obj.items()}
        return ev['evidence_id'] if obj==old else obj
    cap.update(swap(cap));rehash(k,ip,cap)

def run(source,case,side):
    sys.path.insert(0,str(source/'src'))
    import codeprobe_measurement_kernel as k
    import codeprobe_interpretation as ip
    import codeprobe_evidence_gates as g
    import codeprobe_s01_observation_adapter as a
    f=int(case['id'][1]);v=int(case['id'][-1]);text=case[side+'_source'];path=case.get('challenge_path',case['path']) if side=='challenge' else case['path']
    d={'cell_id':case['id'],'side':side,'source':text,'source_sha256':sha(text.encode()),'path':path,'language':case['language'],'observation_id':case['observation'],'preparation_scope':'producer measurement, typed record construction and healthy carrier verification; no experiment arm'}
    if f==8:
        num=copy.deepcopy(case['numeric'])
        if side=='healthy':num['left']='0';num['right']='0'
        d['numeric']=num;return d
    if f==4:
        ids=('structural-review','structural-review-conservative')
        profiles={p['profile_id']:p for p in ip.available_profiles()}
        d['capsules']=[ip.interpret_bytes(text.encode(),language='python',profile_id=pid,profile_sha256=profiles[pid]['sha256'],task_family='source_inspection',path=path) for pid in ids]
        d['profiles']=[ip.resolve_profile(pid,profiles[pid]['sha256']) for pid in ids]
        return d
    pid='structural-review'; p=next(x for x in ip.available_profiles() if x['profile_id']==pid)
    args=dict(language=case['language'],profile_id=pid,profile_sha256=p['sha256'],task_family='source_inspection',path=path)
    cap=ip.interpret_bytes(text.encode(),**args)
    recs=[r for r in cap['measurement']['observations'] if r['observation_id']==case['observation'] and (case['entity_name'] is None or r['entity']['entity_id'].split(':')[2]==case['entity_name'])]
    if len(recs)!=1:raise ValueError('unique actual predecessor record absent')
    r=recs[0];rid=r['record_id'];carrier=g.make_carrier(cap,text.encode(),record_id=rid,**args)
    healthy_k=copy.deepcopy(cap['measurement'])
    if side=='challenge':
        if f==3:narrow(k,ip,cap,r,case['narrow_line'])
        elif f==5:
            carrier['observation']['source_evidence'][0]['evidence_id']=r['source_evidence_ids'][0]
            obs=carrier['observation'];obs['fingerprint_sha256']=sha(canonical({key:val for key,val in obs.items() if key!='fingerprint_sha256'})) if 'fingerprint_sha256' in obs else obs.get('fingerprint_sha256')
            # Remove an absent optional key; adapter uses its actual fingerprint key below.
            if obs.get('fingerprint_sha256') is None:obs.pop('fingerprint_sha256',None)
            if 'fingerprint' in obs:obs['fingerprint']=sha(canonical({key:val for key,val in obs.items() if key!='fingerprint'}))
        elif f==6:
            if v==1:
                r['value']+=1
                for dim in cap['dimensions']:
                    for item in dim['items']:
                        if item['record_ref']==rid and 'value' in item:item['value']=r['value']
            elif v==2:
                cap['measurement']['artifact']['raw_sha256']='0'*64
                carrier['context']['raw_sha256']='0'*64
            elif v==3:
                pid2='structural-review-conservative'; pp=next(x for x in ip.available_profiles() if x['profile_id']==pid2)
                args2=dict(args,profile_id=pid2,profile_sha256=pp['sha256'])
                cap=ip.interpret_bytes(text.encode(),**args2)
                carrier=g.make_carrier(cap,text.encode(),record_id=rid,**args2)
            else:narrow(k,ip,cap,r,case['narrow_line'])
        elif f==7 and v==4:
            r['specification_id']=r['specification_id'].rsplit('/',1)[0]+'/99.0.0'
            r['record_id']=k._record_id(r['specification_id'],r['entity']['entity_id'])
            rid=r['record_id']
    rehash(k,ip,cap)
    if side=='challenge' and (f==3 or(f==6 and v in (1,4))):
        carrier['observation']=a.adapt_observation(next(x for x in cap['measurement']['observations'] if x['record_id']==rid))
    d.update(capsule=cap,carrier=carrier,record_id=rid,request=args)
    return d

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--recipes',type=Path,required=True);ap.add_argument('--cell',required=True);ap.add_argument('--side',choices=['healthy','challenge'],required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    c=next(c for c in load(args.recipes) if c['id']==args.cell)
    try:out=run(args.source,c,args.side);save(args.out,out)
    except Exception as exc:
        save(args.out,{'cell_id':args.cell,'side':args.side,'status':'MATERIALISATION_ERROR','error_type':type(exc).__name__,'error':str(exc)});raise
