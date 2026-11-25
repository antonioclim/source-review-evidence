#!/usr/bin/env python3
"""Verify this documentation edition against its immutable P7D baseline.
No product imports, experiments or network. Historical raw evidence stays raw.
"""
from pathlib import Path
import hashlib,json,importlib.util

def verify(root):
 root=Path(root).absolute()
 if any(p.is_symlink() for p in (root,*root.parents)):raise ValueError('linked package root')
 def get(n):return json.loads((root/n).read_text())
 def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
 count=0
 def need(x,msg):
  nonlocal count;count+=1
  if not x:raise ValueError(msg)
 ed=get('DOCUMENTATION_EDITION.json');rev=get('qualification/REVISION.json')
 need(ed['edition']=='P9B-docsync.1','edition');need(ed['computational_version']==rev['revision']=='P7-R4-review-candidate+a2p7d.1','computational identity')
 for k in ['source_changed','tests_changed','experiments_changed','results_changed','science_rerun','A19_A20_active','public_release','submission_ready']:need(ed[k] is False,k)
 need(ed['A17']=='NOT_MET' and ed['Q07']=='NOT_QUALIFIED_NOT_WAIVED','holds')
 need(ed['current_guide']=='documentation/current/REVIEWERS_GUIDE.md','guide route')
 guide=(root/ed['current_guide']).read_text();need('F6-V2, F6-V3 and F7-V4' in guide and 'A17 NOT_MET' in guide,'cases/hold')
 need('review_evidence/p7d/execution/full3' in guide,'raw evidence route')
 lock=get('qualification/p7d/INPUT_LOCK.json')
 for n,r in lock['files'].items():
  p=root/n;need(p.is_file() and not p.is_symlink() and p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],'protected '+n)
 fr=get('experiments/p7c/FREEZE2.json');need(sha(root/'experiments/p7c/FREEZE2.json')==lock['freeze_sha256'],'freeze')
 actual={p.relative_to(root/'source').as_posix():sha(p) for p in (root/'source').rglob('*') if p.is_file()}
 need(actual==fr['source_snapshot'],'source snapshot')
 for n,r in fr['files'].items():need(sha(root/'experiments/p7c'/n)==r['sha256'],'experiment '+n)
 for phase in ['p7a','p7b','p7d']:
  base=root/'review_evidence'/phase;rows=(base/'SHA256SUMS.txt').read_text().splitlines();exp={r[66:]:r[:64] for r in rows if r.strip()};actual={p.relative_to(base).as_posix():sha(p) for p in base.rglob('*') if p.is_file() and p.relative_to(base).as_posix()!='SHA256SUMS.txt'};need(actual==exp,'raw audit inventory '+phase)
 for n,r in get('DOCUMENTATION_FILES.json')['files'].items():need(sha(root/n)==r['sha256'],'current document '+n)
 # Exact result path is bound in the documentary evidence copy and in guide locators.
 pilot=get('documentation/companion/evidence/current/experiment/pilot_summary.json')
 need(pilot['P6_strict_continuation']=='NOT_MET','pilot');need(len(pilot['rows'])==32 and pilot['ineligible_challenges']==['F6-V2','F6-V3','F7-V4'],'all cases')
 return {'status':'PASS_DOCSYNC_AND_P7D_BYTES_ONLY','checks':count,'protected_files':len(lock['files']),'source_files':len(fr['source_snapshot']),'A17':'NOT_MET','Q07':'NOT_QUALIFIED','scientific_execution':False}
if __name__=='__main__':
 try:print(json.dumps(verify(Path(__file__).absolute().parent),indent=2))
 except Exception as e:print('REFUSED_DOCSYNC:',type(e).__name__,str(e));raise SystemExit(1)
