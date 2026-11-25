"""Small strict, local-only primitives for P7D orchestration and verification."""
from __future__ import annotations
import hashlib
import json
import os
import stat
from pathlib import Path, PurePosixPath
from typing import Any

class Refusal(ValueError):
    """A precondition was not met; no scientific verdict is implied."""

def read(path: Path) -> Any:
    def pairs(items):
        out = {}
        for k, v in items:
            if k in out:
                raise Refusal('duplicate JSON key: ' + k)
            out[k] = v
        return out
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(Refusal('non-finite JSON: ' + x)))

def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def write(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n')

def text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as f:
        f.write(value)

def no_links(path: Path) -> Path:
    p = path.absolute()
    for part in (p, *p.parents):
        if part.is_symlink():
            raise Refusal('symlink path or ancestor: ' + str(part))
    return p

def regular(path: Path) -> None:
    no_links(path)
    if not stat.S_ISREG(path.stat().st_mode):
        raise Refusal('not a regular file: ' + str(path))

def relative(name: str) -> str:
    p = PurePosixPath(name)
    if not name or p.is_absolute() or '..' in p.parts or '\\' in name or ':' in name or p.as_posix() != name:
        raise Refusal('unsafe relative path: ' + name)
    return name

def new_output(path: Path, root: Path) -> Path:
    p = no_links(path).resolve()
    root = no_links(root).resolve()
    if p.exists() or p == root or root in p.parents or p in root.parents:
        raise Refusal('output must be absent and outside candidate: ' + str(p))
    return p

def inventory(root: Path) -> dict[str, dict[str, Any]]:
    out = {}
    for base, dirs, files in os.walk(root, followlinks=False):
        for n in dirs:
            no_links(Path(base)/n)
        for n in files:
            p = Path(base)/n
            regular(p)
            name = p.relative_to(root).as_posix()
            out[name] = {'bytes': p.stat().st_size, 'sha256': sha(p)}
    return dict(sorted(out.items()))

def protected(root: Path) -> dict[str, Any]:
    lock = read(root/'qualification/p7d/INPUT_LOCK.json')
    mismatches = []
    for name, item in lock['files'].items():
        relative(name)
        p = root/name
        try:
            regular(p)
            if p.stat().st_size != item['bytes'] or sha(p) != item['sha256']:
                mismatches.append(name)
        except OSError:
            mismatches.append(name)
    if mismatches:
        raise Refusal('protected predecessor input differs: ' + ', '.join(mismatches))
    if sha(root/'experiments/p7c/FREEZE2.json') != lock['freeze_sha256']:
        raise Refusal('frozen experiment changed')
    fr = read(root/'experiments/p7c/FREEZE2.json')
    for name, item in fr['files'].items():
        p = root/'experiments/p7c'/relative(name)
        if p.stat().st_size != item['bytes'] or sha(p) != item['sha256']:
            raise Refusal('freeze member changed: ' + name)
    actual = {k: v['sha256'] for k, v in inventory(root/'source').items()}
    if actual != fr['source_snapshot']:
        raise Refusal('source inventory differs from the experimental freeze')
    return {'status': 'VERIFIED_IMMUTABLE_P7C_INPUTS', 'protected_files': len(lock['files']),
            'source_files': len(actual), 'freeze_members': len(fr['files']),
            'freeze_sha256': lock['freeze_sha256'], 'input_lock_sha256': sha(root/'qualification/p7d/INPUT_LOCK.json')}
