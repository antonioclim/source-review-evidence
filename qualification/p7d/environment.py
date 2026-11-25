"""Qualify available installed bytes, with explicit limits, without installation.

This module is stdlib-only. Distribution metadata is read from an explicit path;
.pth files, sitecustomize and package code are not loaded by this inspection.
"""
from __future__ import annotations
from pathlib import Path, PurePosixPath
import importlib.metadata
import platform
import shutil
import sys
import sysconfig
from p7d_common import Refusal, read, regular, relative, sha, write

BASELINE_SHA = 'f281e68f6778fc3d05061ce94401de00e4810532c7591030cd0715830596823e'

def default_site() -> Path:
    # Keep the lexical venv executable location. With -S, CPython 3.13 reports
    # the base interpreter prefix, so sys.prefix is not a venv-site locator.
    exe = Path(sys.executable).absolute()
    if exe.parent.name == 'bin':
        return exe.parent.parent/'lib'/('python'+platform.python_version_tuple()[0]+'.'+platform.python_version_tuple()[1])/'site-packages'
    raise Refusal('supply --site-dir explicitly for this interpreter layout')

def norm(name: str) -> str:
    return name.lower().replace('_','-').replace('.','-')

def evaluate(baseline: dict, observation: dict) -> list[str]:
    problems = []
    for key in ('python','platform','executable_sha256'):
        if observation.get(key) != baseline[key]:
            problems.append('runtime.'+key)
    for name, package in baseline['packages'].items():
        found = observation.get('packages',{}).get(name)
        if not isinstance(found,dict):
            problems.append('missing package '+name)
            continue
        if found.get('version') != package['version']:
            problems.append('version '+name)
        if found.get('metadata_sha256') != package['metadata_sha256']:
            problems.append('metadata '+name)
        if found.get('files') != package['installed_files']:
            problems.append('file evidence '+name)
        if found.get('file_mismatches'):
            problems.append('installed bytes '+name)
        if found.get('file_count') != len(package['installed_files']):
            problems.append('file count '+name)
    if observation.get('scan_errors'):
        problems += observation['scan_errors']
    return problems

def inspect(root: Path, site: Path) -> dict:
    path = root/'metadata/review-environment.observed.json'
    if sha(path) != BASELINE_SHA:
        raise Refusal('historical environment baseline changed')
    baseline = read(path)
    observed = {'schema':'codeprobe-p7d-environment/1','python':platform.python_version(),
                'platform':platform.platform(),'executable':sys.executable,
                'executable_sha256':sha(Path(sys.executable)),
                'isolated':bool(sys.flags.isolated),'no_site':bool(sys.flags.no_site),
                'site_directory':str(site.absolute()),'baseline_sha256':sha(path),
                'sys_path_at_inspection':list(sys.path),'packages':{},'scan_errors':[],
                'clean_machine_qualified':False,'Q07':'NOT_QUALIFIED',
                'portable_installation_qualified':False,'wheel_artifact_hashes_available':False,
                'system_library_closure_verified':False,'new_installations':0,
                'scope':'Exact runtime signature and recorded installed files only; same host and stdlib; no wheel or OS provenance closure.'}
    if not site.is_dir():
        observed['scan_errors'].append('site directory absent')
    candidates = {}
    for dist in importlib.metadata.distributions(path=[str(site)]):
        name = norm(dist.metadata.get('Name',''))
        if name in baseline['packages']:
            candidates.setdefault(name, []).append(dist)
    for name, pkg in baseline['packages'].items():
        found = candidates.get(name, [])
        if len(found) != 1:
            observed['scan_errors'].append('expected one distribution: '+name)
            continue
        dist = found[0]; mismatches = []; checked = []
        meta = dist.read_text('METADATA')
        import hashlib
        metadata_hash = hashlib.sha256(meta.encode('utf-8')).hexdigest() if meta is not None else None
        for item in pkg['installed_files']:
            rel = item['distribution_path']
            if rel == '../../../bin/jsonschema' and name == 'jsonschema':
                target = site/rel
            else:
                target = site/relative(rel)
            try:
                regular(target)
                got = {'distribution_path':rel,'bytes':target.stat().st_size,'sha256':sha(target)}
                if got != item:
                    mismatches.append({'expected':item,'actual':got})
                checked.append(got)
            except (OSError, ValueError) as e:
                mismatches.append({'distribution_path':rel,'error':str(e)})
        observed['packages'][name]={'version':dist.version,'metadata_sha256':metadata_hash,
            'file_count':len(checked),'file_mismatches':mismatches,'files':checked}
    observed['problems'] = evaluate(baseline,observed)
    observed['status'] = 'AVAILABLE_RUNTIME_AND_RECORDED_BYTES_MATCH' if not observed['problems'] else 'REFUSED_ENVIRONMENT'
    observed['total_files_checked'] = sum(p['file_count'] for p in observed['packages'].values())
    return observed

def stage(root: Path, site: Path, destination: Path) -> dict:
    """Copy only admitted records, without pip, entry-point invocation or .pth."""
    if destination.exists():
        raise Refusal('dependency staging already exists')
    baseline = read(root/'metadata/review-environment.observed.json')
    destination.mkdir()
    mapping = []
    for name,pkg in baseline['packages'].items():
        for item in pkg['installed_files']:
            rel = item['distribution_path']
            source = site/rel
            if rel == '../../../bin/jsonschema' and name == 'jsonschema':
                dest = destination/'bin/jsonschema'
            else:
                dest = destination/'site'/relative(rel)
            if source.stat().st_size != item['bytes'] or sha(source) != item['sha256']:
                raise Refusal('dependency changed between inspection and copying: '+rel)
            dest.parent.mkdir(parents=True,exist_ok=True)
            with source.open('rb') as f, dest.open('xb') as g:
                shutil.copyfileobj(f,g)
            if sha(dest) != item['sha256']:
                raise Refusal('copy hash differs: '+rel)
            mapping.append({'package':name, 'source_record':rel, 'destination':dest.relative_to(destination).as_posix(),
                            'sha256':sha(dest),'bytes':dest.stat().st_size})
    receipt={'schema':'codeprobe-p7d-dependency-stage/1','copied_files':len(mapping),'files':mapping,
             'site':str(destination/'site'),'installed':False,'Q07':'NOT_QUALIFIED',
             'scope':'Isolated dependency directory copied from verified existing files; same interpreter/stdlib/OS.'}
    write(destination/'STAGE.json', receipt)
    return receipt
