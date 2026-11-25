#!/usr/bin/env python3
"""Verify only this archive's exact file inventory and SHA-256 manifest."""
from pathlib import Path,PurePosixPath
import hashlib,os,re,stat,sys

def verify(root:Path)->int:
 
 if root.is_symlink():raise ValueError('symlink root')
 root=root.resolve();manifest=root/'SHA256SUMS.txt';expected={};folded=set()
 if manifest.is_symlink() or not manifest.is_file() or manifest.stat().st_size>2_000_000:
  raise ValueError('missing/unsafe/oversized root manifest')
 for line in manifest.read_text(encoding='utf-8').splitlines():
  if not line: continue
  if not re.fullmatch(r'[0-9a-f]{64}  .+',line): raise ValueError('invalid manifest line')
  digest,name=line.split('  ',1);path=PurePosixPath(name)
  if path.is_absolute() or any(x in ('..','.') for x in path.parts) or '\\' in name or ':' in name or str(path)!=name or name=='SHA256SUMS.txt':raise ValueError('unsafe/self-referential manifest path')
  if name in expected or name.casefold() in folded: raise ValueError('duplicate/colliding manifest path')
  expected[name]=digest;folded.add(name.casefold())
 actual=set();actual_fold=set()
 for directory,dirs,names in os.walk(root,followlinks=False):
  for name in dirs+names:
   p=Path(directory)/name;s=p.lstat()
   if stat.S_ISLNK(s.st_mode) or not (stat.S_ISREG(s.st_mode) or stat.S_ISDIR(s.st_mode)):raise ValueError('symlink/special entry')
   rel=p.relative_to(root).as_posix()
   if rel.casefold() in actual_fold:raise ValueError('case collision')
   actual_fold.add(rel.casefold())
   if stat.S_ISREG(s.st_mode) and rel!='SHA256SUMS.txt':actual.add(rel)
 if any(n.lower().endswith(('.zip','.whl','.tar','.gz')) for n in actual):raise ValueError('nested archive not declared for working candidate')
 if actual!=set(expected):raise ValueError('inventory mismatch: extra='+repr(sorted(actual-set(expected)))+' missing='+repr(sorted(set(expected)-actual)))
 for name,digest in expected.items():
  h=hashlib.sha256()
  with (root/name).open('rb') as f:
   for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
  if h.hexdigest()!=digest:raise ValueError('hash mismatch: '+name)
 return len(expected)
if __name__=='__main__':
 try:n=verify(Path(__file__).absolute().parent)
 except (OSError,ValueError,UnicodeError) as e:print('FAIL:',e);raise SystemExit(1)
 print('PASS: '+str(n)+' files; exact inventory and SHA-256. Scope: bytes only, no scientific qualification.')
