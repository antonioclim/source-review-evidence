"""Post-implementation red-team probe; frozen before the corrective change."""
import sys,json
from pathlib import Path
from unittest.mock import patch
root=Path(sys.argv[1]);out=Path(sys.argv[2]);sys.path.insert(0,str(root/'source/src'))
import codeprobe_interpretation as ip
import codeprobe_evidence_gates as g
original=ip.threshold_decision
def altered(*args,**kwargs):
 r=original(*args,**kwargs);r['policy_sensitivity']='incorrect_sensitivity';return r
with patch.object(ip,'threshold_decision',altered):
 r=g.compare_profiles(b'def f():\n    pass\n',observation_id='python.callable.mccabe_complexity',profile_ids=('structural-review','structural-review-conservative'))
check=r['status']=='FAIL' and all(p['conformance']=='FAIL' for p in r['profiles'])
out.write_text(json.dumps({'expected':'FAIL with both conformance FAIL','observed':r,'check_pass':check},indent=2)+'\n')
print(check);sys.exit(not check)
