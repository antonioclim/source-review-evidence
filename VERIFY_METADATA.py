#!/usr/bin/env python3
"""Verify the declared local metadata graph and observed dependency records.
No external context fetching, dependency installation or full SPDX certification.
Use the package SHA-256 verifier separately to verify the underlying file bytes.
"""
from pathlib import Path,PurePosixPath
import json,hashlib,re,sys

def read(path):
 def pairs(items):
  out={}
  for key,val in items:
   if key in out:raise ValueError('duplicate JSON key')
   out[key]=val
  return out
 return json.loads(path.read_text(encoding='utf-8'),object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('non-finite JSON')))
def verify(root):
 root=Path(root);env=read(root/'metadata/review-environment.observed.json');s=read(root/'metadata/sbom.spdx.json');g=read(root/'ro-crate-metadata.json');v=read(root/'qualification/REVISION.json');count=0
 def require(p,msg):
  nonlocal count
  count+=1
  if not p:raise ValueError(msg)
 require(g['@context']=='https://w3id.org/ro/crate/1.1/context','RO-Crate context')
 nodes={}
 for node in g['@graph']:
  ident=node['@id'];require(ident not in nodes,'duplicate entity');nodes[ident]=node
  if re.match(r'^https?://',ident):continue
  path=PurePosixPath(ident);require(not path.is_absolute() and '..' not in path.parts and '\\' not in ident and ':' not in ident,'unsafe entity path')
  p=root/ident;require(p.exists() and not p.is_symlink(),'missing or linked local entity: '+ident)
  if 'sha256' in node:require(p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==node['sha256'],'entity hash: '+ident)
 require(nodes['ro-crate-metadata.json']['about']=={'@id':'./'},'descriptor subject')
 require(nodes['./']['version']==v['revision'],'candidate version drift')
 require(nodes['./']['creativeWorkStatus']=='Unreleased intermediate candidate','candidate status')
 require(v['public_release'] is False and v['submission_ready'] is False,'unexpected publication claim')
 require(v['revision'] in (root/'CITATION.cff').read_text(),'citation version drift')
 policy=read(root/'PACKAGE_POLICY.json')
 require(policy['revision']==v['revision'],'package-policy revision drift')
 require(policy['inner_zips']=={} and policy['current_verifier']=='VERIFY.py','package-policy execution/nesting drift')
 require(policy['baseline_documentary_revision']=='LP02/v3.2','baseline policy identity drift')
 def walk(x):
  if isinstance(x,dict):
   if set(x)=={'@id'} and not re.match(r'^https?://',x['@id']):require(x['@id'] in nodes,'dangling local entity')
   for y in x.values():walk(y)
  elif isinstance(x,list):
   for y in x:walk(y)
 walk(g['@graph'])
 packages={}
 for p in s['packages']:
  require(p['SPDXID'] not in packages,'duplicate SPDX package');packages[p['SPDXID']]=p
 require(packages['SPDXRef-CodeProbe']['versionInfo']==v['revision'],'SPDX version drift')
 for key,p in env['packages'].items():
  require('SPDXRef-'+key in packages,'missing review dependency: '+key)
  require(packages['SPDXRef-'+key]['versionInfo']==p['version'],'dependency version drift: '+key)
 expected={('SPDXRef-CodeProbe','SPDXRef-jsonschema')}|{('SPDXRef-'+x['parent'],'SPDXRef-'+x['child']) for x in env['relationships']}
 actual=set()
 for x in s['relationships']:
  require(x['spdxElementId'] in set(packages)|{'SPDXRef-DOCUMENT'} and x['relatedSpdxElement'] in packages,'dangling SPDX endpoint')
  if x['relationshipType']=='DEPENDS_ON':actual.add((x['spdxElementId'],x['relatedSpdxElement']))
 require(actual==expected,'dependency relationship mismatch')
 require(env['wheel_artifact_hashes_available'] is False and env['system_library_closure_verified'] is False,'unqualified environment promotion')
 return count
if __name__=='__main__':
 try:count=verify(Path(__file__).resolve().parent)
 except (OSError,ValueError,KeyError,TypeError) as e:print('FAIL_METADATA:',e);raise SystemExit(1)
 print(f'PASS_LOCAL_METADATA: {count} checks; no cold-machine, complete SPDX/JSON-LD or vulnerability certification.')
