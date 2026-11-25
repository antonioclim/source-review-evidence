#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, re, stat, sys, zipfile
from pathlib import Path, PurePosixPath

ROOT=Path(__file__).resolve().parent
MANIFEST=ROOT/'SHA256SUMS.txt'
POLICY_FILE=ROOT/'PACKAGE_POLICY.json'
HEX64=re.compile(r'^[0-9a-f]{64}$')

def fail(message:str)->None:
    print('FAIL')
    print(message)
    raise SystemExit(1)

def safe_rel(name:str)->bool:
    if not name or '\\' in name or '\x00' in name:
        return False
    p=PurePosixPath(name)
    return not p.is_absolute() and '..' not in p.parts and not (p.parts and ':' in p.parts[0])

def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):
            h.update(block)
    return h.hexdigest()

def main()->int:
    errors=[]
    if not MANIFEST.is_file(): errors.append('MISSING: SHA256SUMS.txt')
    if not POLICY_FILE.is_file(): errors.append('MISSING: PACKAGE_POLICY.json')
    if errors:
        print('FAIL'); print('\n'.join(errors)); return 1
    try: policy=json.loads(POLICY_FILE.read_text(encoding='utf-8'))
    except Exception as exc:
        fail(f'INVALID_POLICY: {exc}')
    expected={}; seen_manifest=set()
    for lineno,line in enumerate(MANIFEST.read_text(encoding='utf-8').splitlines(),1):
        if not line.strip(): continue
        try: digest,name=line.split('  ',1)
        except ValueError:
            errors.append(f'MALFORMED_MANIFEST_LINE: {lineno}'); continue
        if not HEX64.fullmatch(digest): errors.append(f'INVALID_DIGEST: line {lineno}')
        if not safe_rel(name): errors.append(f'UNSAFE_MANIFEST_PATH: {name}')
        if name in seen_manifest: errors.append(f'DUPLICATE_MANIFEST_ENTRY: {name}')
        seen_manifest.add(name); expected[name]=digest
    all_nodes=list(ROOT.rglob('*'))
    for p in all_nodes:
        if p.is_symlink(): errors.append(f'SYMLINK: {p.relative_to(ROOT).as_posix()}')
    actual_files={p.relative_to(ROOT).as_posix() for p in all_nodes if p.is_file() and not p.is_symlink() and p.name!='SHA256SUMS.txt'}
    casefold={}
    for name in sorted(actual_files): casefold.setdefault(name.casefold(),[]).append(name)
    for names in casefold.values():
        if len(names)>1: errors.append('CASE_COLLISION: '+', '.join(names))
    if policy.get('layout')=='flat':
        for name in sorted(actual_files):
            if '/' in name: errors.append(f'NON_FLAT_PATH: {name}')
    for name,digest in expected.items():
        p=ROOT/name
        if not p.is_file() or p.is_symlink(): errors.append(f'MISSING_OR_NONREGULAR: {name}'); continue
        got=sha256(p)
        if got!=digest: errors.append(f'MISMATCH: {name}: {got} != {digest}')
    for name in sorted(actual_files-set(expected)): errors.append(f'UNLISTED: {name}')
    for name in sorted(set(expected)-actual_files):
        if not any(x.startswith(f'MISSING_OR_NONREGULAR: {name}') for x in errors): errors.append(f'MISSING: {name}')
    rules=policy.get('inner_zips',{})
    if not isinstance(rules,dict): errors.append('INVALID_POLICY: inner_zips must be an object'); rules={}
    zip_files=sorted(name for name in actual_files if name.lower().endswith('.zip'))
    for name in zip_files:
        if name not in rules: errors.append(f'UNDECLARED_INNER_ZIP: {name}')
    for name in rules:
        if name not in zip_files: errors.append(f'DECLARED_ZIP_MISSING: {name}')
    zip_checked=0
    for name in zip_files:
        rule=rules.get(name)
        if rule is None: continue
        p=ROOT/name
        try:
            with zipfile.ZipFile(p) as z:
                zip_checked+=1
                bad=z.testzip()
                if bad: errors.append(f'ZIP_CRC_FAIL: {name}::{bad}')
                infos=z.infolist(); names=[i.filename for i in infos]
                if len(names)!=len(set(names)): errors.append(f'ZIP_DUPLICATE_MEMBER: {name}')
                cf={}
                for n in names: cf.setdefault(n.casefold(),[]).append(n)
                for vals in cf.values():
                    if len(vals)>1: errors.append(f'ZIP_CASE_COLLISION: {name}::'+', '.join(vals))
                file_members=[]
                for info in infos:
                    member=info.filename
                    if not safe_rel(member): errors.append(f'ZIP_UNSAFE_PATH: {name}::{member}')
                    mode=(info.external_attr>>16)&0o170000
                    if mode==stat.S_IFLNK: errors.append(f'ZIP_SYMLINK: {name}::{member}')
                    if info.flag_bits & 0x1: errors.append(f'ZIP_ENCRYPTED_MEMBER: {name}::{member}')
                    if info.is_dir(): continue
                    file_members.append(member)
                    if member.lower().endswith('.zip') and not rule.get('allow_nested_zips',False):
                        errors.append(f'NESTED_ZIP: {name}::{member}')
                if rule.get('flat'):
                    for member in file_members:
                        if len(PurePosixPath(member).parts)!=1: errors.append(f'ZIP_NON_FLAT_MEMBER: {name}::{member}')
                if rule.get('single_top_level_directory'):
                    tops={PurePosixPath(m).parts[0] for m in file_members if PurePosixPath(m).parts}
                    if len(tops)!=1: errors.append(f'ZIP_TOP_LEVEL_COUNT: {name}::{len(tops)}')
                    for member in file_members:
                        if len(PurePosixPath(member).parts)<2: errors.append(f'ZIP_FILE_OUTSIDE_TOP_DIR: {name}::{member}')
                for req in rule.get('required_members',[]):
                    if req not in file_members: errors.append(f'ZIP_REQUIRED_MEMBER_MISSING: {name}::{req}')
                max_members=rule.get('max_members')
                if isinstance(max_members,int) and len(file_members)>max_members: errors.append(f'ZIP_TOO_MANY_MEMBERS: {name}::{len(file_members)}>{max_members}')
        except zipfile.BadZipFile: errors.append(f'BAD_ZIP: {name}')
        except Exception as exc: errors.append(f'ZIP_ERROR: {name}: {type(exc).__name__}: {exc}')
    if errors:
        print('FAIL')
        for e in errors: print(e)
        return 1
    print(f"PASS: {len(expected)} files verified; {zip_checked} declared inner ZIP archive(s) passed CRC, path, identity and nesting checks")
    return 0
if __name__=='__main__': raise SystemExit(main())
