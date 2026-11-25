#!/usr/bin/env python3
"""Verify the exact file inventory of a Source Review Evidence distribution.

Only the Python standard library is used. No file is changed and no network
request or research computation is performed. The root .git entry is excluded
as repository metadata. All other unlisted files and symbolic links fail.
The manifest's authenticity must be established from a separately trusted
archive digest; agreement with a manifest alone is an integrity check.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys

MANIFEST = 'DISTRIBUTION_MANIFEST.json'
SCHEMA = 'source-review-evidence-manifest/1'


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'Duplicate JSON key: {key}')
        result[key] = value
    return result


def safe_relative(value):
    if not isinstance(value, str) or not value:
        return False
    if any(ord(c) < 32 or ord(c) == 127 for c in value):
        return False
    if '\\' in value or ':' in value:
        return False
    parts = value.split('/')
    path = PurePosixPath(value)
    return (not path.is_absolute() and all(p not in ('', '.', '..') for p in parts)
            and parts[0] != '.git' and value != MANIFEST)


def load_manifest(root):
    path = root / MANIFEST
    if path.is_symlink() or not path.is_file():
        raise ValueError('Manifest is missing or is not a regular non-symlink file.')
    raw = path.read_bytes()
    document = json.loads(raw.decode('utf-8'), object_pairs_hook=unique_object)
    if not isinstance(document, dict) or document.get('schema') != SCHEMA:
        raise ValueError('Unsupported manifest schema.')
    if document.get('version') != '1.0.0' or document.get('self_excluded') != MANIFEST:
        raise ValueError('Unexpected distribution version or manifest exclusion.')
    if not isinstance(document.get('files'), list) or not document['files']:
        raise ValueError('Manifest must contain a non-empty files array.')
    entries = {}
    folded = set()
    for item in document['files']:
        if not isinstance(item, dict) or not safe_relative(item.get('path')):
            raise ValueError('Unsafe or malformed file path in manifest.')
        name = item['path']
        if name in entries or name.casefold() in folded:
            raise ValueError(f'Duplicate or case-colliding file path: {name}')
        size = item.get('bytes')
        if type(size) is not int or size < 0:
            raise ValueError(f'Invalid file size: {name}')
        if not isinstance(item.get('sha256'), str) or not re.fullmatch('[0-9a-f]{64}', item['sha256']):
            raise ValueError(f'Invalid SHA-256 digest: {name}')
        entries[name] = item
        folded.add(name.casefold())
    return entries, hashlib.sha256(raw).hexdigest()


def inventory(root):
    files = {}
    issues = []
    pending = [(root, '')]
    while pending:
        directory, prefix = pending.pop()
        try:
            children = sorted(os.scandir(directory), key=lambda e: e.name)
        except OSError as exc:
            issues.append({'kind': 'unreadable_directory', 'path': prefix or '.', 'error': str(exc)})
            continue
        for entry in children:
            relative = prefix + entry.name
            if not prefix and entry.name == '.git':
                continue
            try:
                mode = entry.stat(follow_symlinks=False).st_mode
                if stat.S_ISLNK(mode):
                    issues.append({'kind': 'symbolic_link', 'path': relative})
                elif stat.S_ISDIR(mode):
                    pending.append((Path(entry.path), relative + '/'))
                elif stat.S_ISREG(mode):
                    if relative != MANIFEST:
                        files[relative] = Path(entry.path)
                else:
                    issues.append({'kind': 'non_regular_file', 'path': relative})
            except OSError as exc:
                issues.append({'kind': 'unreadable_entry', 'path': relative, 'error': str(exc)})
    return files, issues


def verify(root):
    if root.is_symlink() or not root.is_dir():
        raise ValueError('Distribution root must be a non-symlink directory.')
    expected, manifest_sha = load_manifest(root)
    actual, issues = inventory(root)
    for name in sorted(expected.keys() - actual.keys()):
        issues.append({'kind': 'missing_file', 'path': name})
    for name in sorted(actual.keys() - expected.keys()):
        issues.append({'kind': 'unexpected_file', 'path': name})
    checked = 0
    checked_bytes = 0
    for name in sorted(expected.keys() & actual.keys()):
        entry = expected[name]
        try:
            hasher = hashlib.sha256()
            size = 0
            with actual[name].open('rb') as stream:
                while True:
                    block = stream.read(1024 * 1024)
                    if not block:
                        break
                    size += len(block)
                    hasher.update(block)
            checked += 1
            checked_bytes += size
            if size != entry['bytes']:
                issues.append({'kind': 'size_mismatch', 'path': name, 'expected': entry['bytes'], 'actual': size})
            if hasher.hexdigest() != entry['sha256']:
                issues.append({'kind': 'sha256_mismatch', 'path': name, 'expected': entry['sha256'], 'actual': hasher.hexdigest()})
        except OSError as exc:
            issues.append({'kind': 'unreadable_file', 'path': name, 'error': str(exc)})
    return {
        'schema': 'source-review-evidence-integrity-result/1',
        'status': 'PASS_EXACT_FILE_INVENTORY' if not issues else 'FAIL_FILE_INVENTORY',
        'version': '1.0.0', 'manifest_sha256': manifest_sha,
        'manifest_files': len(expected), 'observed_files': len(actual),
        'files_hashed': checked, 'bytes_hashed': checked_bytes,
        'ignored_root_entry': '.git', 'issues': issues,
        'scope': 'Exact regular-file inventory and SHA-256 integrity; no software execution, reproduction or native qualification.'
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1], help='Extracted distribution root (defaults to the parent of tools).')
    args = parser.parse_args()
    try:
        result = verify(args.root.absolute())
    except (ValueError, OSError, UnicodeError) as exc:
        result = {'schema': 'source-review-evidence-integrity-result/1', 'status': 'FAIL_INVALID_MANIFEST_OR_ROOT', 'error': str(exc)}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['status'] == 'PASS_EXACT_FILE_INVENTORY' else 1


if __name__ == '__main__':
    sys.exit(main())
