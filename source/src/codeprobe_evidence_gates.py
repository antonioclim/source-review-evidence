"""Typed P6 evidence-gate integration for the local APEX2 P7A revision.

G2 measures availability after source admission; V2 is a separate necessary
representation invariant. G5 compares correctly evaluated declared profiles.
G6 checks a bound S01 observation and an S04 capsule through distinct mechanisms.
The G6 admission scope is one S01 observation, not the complete S01 report API.
Hashes establish local consistency, not authenticated provenance or authorship.
Input source bytes are parsed by the inherited kernel and never executed.
"""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path
from typing import Any, Mapping

import codeprobe_interpretation as interpretation
import codeprobe_measurement_kernel as kernel
import codeprobe_review_contract as consumer
import codeprobe_s01_observation_adapter as adapter

SCHEMA = 'codeprobe-evidence-gates/1.0.0-a2p7a'
CARRIER_SCHEMA = 'codeprobe-bound-s01-observation/1'
STATES = ('PASS', 'FAIL', 'NOT_EVALUATED', 'INVALID_INPUT')
_SOURCE_FILES = ('codeprobe_evidence_gates.py', 'codeprobe_numeric_policy.py')


def _core_hashes() -> dict[str, str]:
    paths = {name: Path(__file__).resolve().with_name(name) for name in _SOURCE_FILES}
    if any(p.is_symlink() or not p.is_file() for p in paths.values()):
        raise ValueError('gate component must be a regular file')
    return {name: hashlib.sha256(p.read_bytes()).hexdigest() for name, p in paths.items()}


_LOADED_CORE = _core_hashes()


def _check_loaded_core() -> dict[str, str]:
    current = _core_hashes()
    if current != _LOADED_CORE:
        raise ValueError('gate implementation changed after import; reload a qualified copy')
    return current


def representation_status(record: Any) -> str:
    """Check only V2, not value-domain conformance or the full kernel schema."""
    if not isinstance(record, Mapping) or 'value' not in record:
        return 'INVALID_INPUT'
    app = record.get('applicability')
    if not isinstance(app, Mapping):
        return 'INVALID_INPUT'
    state = app.get('state')
    if type(state) is not str or state not in kernel.APPLICABILITY_STATES:
        return 'INVALID_INPUT'
    if (state == 'observed') != (record['value'] is not None):
        return 'INVALID_INPUT'
    if state == 'observed':
        if app.get('reason_code') or app.get('reason'):
            return 'INVALID_INPUT'
    elif not all(type(app.get(k)) is str and app[k].strip() for k in ('reason_code', 'reason')):
        return 'INVALID_INPUT'
    return 'PASS'


def availability_status(g1: str, record: Any) -> str:
    """Pure status reducer. Actual source admission is done by evaluate_availability."""
    if type(g1) is not str or g1 not in STATES or g1 == 'INVALID_INPUT':
        return 'INVALID_INPUT'
    if g1 != 'PASS':
        return 'NOT_EVALUATED'
    if representation_status(record) != 'PASS':
        return 'INVALID_INPUT'
    return 'PASS' if record['applicability']['state'] == 'observed' else 'FAIL'


def evaluate_availability(data: bytes, *, language: str, observation_id: str,
                          entity_id: str | None = None, path: str = '<memory>') -> dict[str, Any]:
    """Admit and measure source, then select exactly one requested observation."""
    result: dict[str, Any] = {'schema': SCHEMA, 'gate': 'G2', 'G1': 'NOT_EVALUATED',
                              'V2': 'NOT_EVALUATED', 'status': 'NOT_EVALUATED', 'record': None}
    if (type(data) is not bytes or type(language) is not str or type(observation_id) is not str
            or (entity_id is not None and type(entity_id) is not str) or type(path) is not str):
        result.update(G1='INVALID_INPUT', status='INVALID_INPUT'); return result
    try:
        kernel.intake_from_bytes(data, path=path)
    except (kernel.MeasurementError, ValueError, TypeError) as exc:
        result.update(G1='FAIL', reason=str(exc)); return result
    result['G1'] = 'PASS'
    try:
        measured = kernel.measure_bytes(data, language=language, path=path)
    except (kernel.MeasurementError, ValueError, TypeError) as exc:
        result.update(status='INVALID_INPUT', reason=str(exc)); return result
    records = [r for r in measured['observations'] if r['observation_id'] == observation_id
               and (entity_id is None or r['entity']['entity_id'] == entity_id)]
    if len(records) != 1:
        result.update(status='INVALID_INPUT', reason='requested observation slot is absent or ambiguous'); return result
    record = records[0]
    result.update(V2=representation_status(record), status=availability_status('PASS', record),
                  record=copy.deepcopy(record), raw_sha256=measured['artifact']['raw_sha256'],
                  normalised_sha256=measured['artifact']['normalised_sha256'])
    return result


def consumer_full_status(admission: str, replay: str, *, same_context: bool) -> str:
    """Pure truth rule; booleans/substatuses alone are not evidence of execution."""
    if (type(same_context) is not bool or not same_context or type(admission) is not str
            or type(replay) is not str or admission not in STATES[:3] or replay not in STATES[:3]):
        return 'INVALID_INPUT'
    if admission == 'FAIL' or replay == 'FAIL':
        return 'FAIL'
    if admission == replay == 'PASS':
        return 'PASS'
    return 'NOT_EVALUATED'


def _context(data: bytes, *, record_id: str, language: str, profile_id: str,
             profile_sha256: str, task_family: str, path: str) -> dict[str, Any]:
    if type(data) is not bytes or type(record_id) is not str or not record_id:
        raise ValueError('immutable bytes and explicit observation-slot identity required')
    p = interpretation.resolve_profile(profile_id, profile_sha256)
    if language not in p['languages'] or task_family not in p['task_families']:
        raise ValueError('undeclared source/profile context')
    if type(path) is not str or len(path) > 4096 or '\x00' in path:
        raise ValueError('invalid logical source path')
    intake = kernel.intake_from_bytes(data, path=path)
    return {'record_id': record_id, 'raw_sha256': intake.raw_sha256,
            'normalised_sha256': intake.normalised_sha256, 'language': language, 'path': path,
            'profile': {'profile_id': profile_id, 'version': p['version'], 'sha256': profile_sha256},
            'task_family': task_family, 'producer_build': interpretation.build_identity(),
            'gate_component_sha256': _check_loaded_core()}


def _one_record(capsule: dict[str, Any], record_id: str) -> dict[str, Any]:
    records = [r for r in capsule['measurement']['observations'] if r['record_id'] == record_id]
    if len(records) != 1:
        raise ValueError('capsule must contain exactly the bound observation slot')
    return records[0]


def make_carrier(capsule: dict[str, Any], data: bytes, *, record_id: str, **context: Any) -> dict[str, Any]:
    """Create a bound S01 carrier from a verified capsule; no caller-supplied PASS."""
    args = dict(context); args.setdefault('path', '<memory>')
    interpretation.verify_capsule(capsule, data, **args)
    binding = _context(data, record_id=record_id, **args)
    return {'schema': CARRIER_SCHEMA, 'context': binding,
            'observation': adapter.adapt_observation(_one_record(capsule, record_id))}


def qualify_consumer(carrier: dict[str, Any] | None, capsule: dict[str, Any] | None,
                     data: bytes, *, record_id: str | None = None, language: str,
                     profile_id: str, profile_sha256: str, task_family: str,
                     path: str = '<memory>') -> dict[str, Any]:
    """Check real carrier admission and source replay under explicit context binding.

    Missing carriers stay NOT_EVALUATED. A context mismatch is INVALID_INPUT.
    Tampering within a correctly bound carrier/capsule is a failed subcheck.
    The source/profile/build checks are computed here, not trusted input flags.
    """
    result: dict[str, Any] = {'schema': SCHEMA, 'gate': 'G6', 'status': 'INVALID_INPUT',
                              'admission': 'NOT_EVALUATED', 'replay': 'NOT_EVALUATED',
                              'context_binding': 'INVALID_INPUT', 'diagnostics': [],
                              'admission_scope': 'S01 observation plus exact S02-to-S01 correspondence when capsule supplied',
                              'provenance_scope': 'local file-set consistency; no signature or runtime authentication'}
    args = dict(language=language, profile_id=profile_id, profile_sha256=profile_sha256,
                task_family=task_family, path=path)
    try:
        if carrier is not None:
            if type(carrier) is not dict or set(carrier) != {'schema', 'context', 'observation'} or carrier['schema'] != CARRIER_SCHEMA:
                raise ValueError('untyped or incompatible S01 carrier')
            supplied_id = carrier['context']['record_id']
            if record_id is not None and supplied_id != record_id:
                raise ValueError('observation-slot identity disagrees with explicit request')
            record_id = supplied_id
        ctx = _context(data, record_id=record_id, **args)
        if carrier is not None and interpretation.canonical(carrier['context']) != interpretation.canonical(ctx):
            raise ValueError('carrier source/profile/build context mismatch')
        if capsule is not None:
            if type(capsule) is not dict or capsule.get('schema') != interpretation.SCHEMA:
                raise ValueError('untyped or incompatible S04 capsule')
            art = capsule['measurement']['artifact']
            if (any(art[k] != ctx[k] for k in ('raw_sha256', 'normalised_sha256', 'path', 'language'))
                    or capsule['profile'] != ctx['profile'] or capsule['context'] != {'task_family': task_family}
                    or interpretation.canonical(capsule['build']) != interpretation.canonical(ctx['producer_build'])):
                raise ValueError('capsule source/profile/build context mismatch')
            record = _one_record(capsule, record_id)
        else:
            record = None
    except (ValueError, TypeError, KeyError, IndexError, RecursionError) as exc:
        result['diagnostics'].append(str(exc)); return result
    result['context_binding'] = 'PASS'
    result['context_sha256'] = interpretation.digest(interpretation.canonical(ctx))
    if carrier is not None:
        try:
            consumer._validate_observation(carrier['observation'], 0)
            if record is not None and interpretation.canonical(carrier['observation']) != interpretation.canonical(adapter.adapt_observation(record)):
                raise ValueError('S01 observation differs from the explicitly bound S02 record')
            result['admission'] = 'PASS'
        except (ValueError, TypeError, KeyError, IndexError, RecursionError) as exc:
            result['admission'] = 'FAIL'; result['diagnostics'].append('admission: ' + str(exc))
    if capsule is not None:
        try:
            interpretation.verify_capsule(capsule, data, **args)
            result['replay'] = 'PASS'
        except (ValueError, TypeError, KeyError, IndexError, RecursionError) as exc:
            result['replay'] = 'FAIL'; result['diagnostics'].append('replay: ' + str(exc))
    result['status'] = consumer_full_status(result['admission'], result['replay'], same_context=True)
    return result


def compare_profiles(data: bytes, *, observation_id: str, profile_ids: tuple[str, str],
                     entity_id: str | None = None, language: str = 'python',
                     task_family: str = 'source_inspection', path: str = '<memory>') -> dict[str, Any]:
    """Execute two admitted profiles on one source; retain null differences.

    Only one versioned observed slot and an actual rule in each profile qualify.
    Differences establish a relation, not a failed G5 policy evaluation.
    """
    if len(profile_ids) != 2 or len(set(profile_ids)) != 2:
        raise ValueError('two distinct explicit profiles required')
    profiles = {p['profile_id']: p for p in interpretation.available_profiles()}
    rows, values, specs, record_ids = [], [], [], []
    for pid in profile_ids:
        if pid not in profiles:
            raise ValueError('unknown profile')
        sha = profiles[pid]['sha256']
        p = interpretation.resolve_profile(pid, sha)
        cap = interpretation.interpret_bytes(data, language=language, profile_id=pid,
                                             profile_sha256=sha, task_family=task_family, path=path)
        records = [r for r in cap['measurement']['observations'] if r['observation_id'] == observation_id
                   and (entity_id is None or r['entity']['entity_id'] == entity_id)]
        if len(records) != 1 or records[0]['applicability']['state'] != 'observed':
            return {'schema': SCHEMA, 'gate': 'G5_RELATION', 'status': 'NOT_EVALUATED',
                    'reason': 'absent, ambiguous or non-observed slot', 'profiles': rows}
        r = records[0]
        rules = [rule for rule in p['rules'] if rule['observation_id'] == observation_id]
        if len(rules) != 1:
            return {'schema': SCHEMA, 'gate': 'G5_RELATION', 'status': 'NOT_EVALUATED',
                    'reason': 'no unique declared policy rule', 'profiles': rows}
        rule = rules[0]; x = r['value']; levels = rule['threshold_set']
        expected_set = sorted({x > levels['lower'], x > levels['upper']})
        expected_status = 'no_rule_trigger' if expected_set == [False] else 'review_opportunity' if expected_set == [True] else 'abstain'
        items = [i for d in cap['dimensions'] for i in d['items']
                 if i['record_ref'] == r['record_id'] and i['rule_id'] == rule['rule_id']]
        decision = items[0]['decision'] if len(items) == 1 else None
        expected_decision = {'status': expected_status, 'possible_predicates': expected_set,
                             'nominal_predicate': x > levels['nominal'],
                             'policy_sensitivity': 'boundary_sensitive' if len(expected_set) == 2
                             else 'stable_over_declared_threshold_set'}
        conformant = (type(decision) is dict
                       and interpretation.canonical(decision) == interpretation.canonical(expected_decision))
        rows.append({'profile_id': pid, 'profile_sha256': sha, 'decision': decision,
                     'conformance': 'PASS' if conformant else 'FAIL', 'capsule_digest': cap['digest']})
        values.append(x); specs.append(r['specification_id']); record_ids.append(r['record_id'])
    if values[0] != values[1] or specs[0] != specs[1] or record_ids[0] != record_ids[1]:
        status = 'INVALID_INPUT'
    elif any(r['conformance'] != 'PASS' for r in rows):
        status = 'FAIL'
    elif rows[0]['decision'] != rows[1]['decision']:
        status = 'RELATIONAL_WITNESS'
    else:
        status = 'NO_DIFFERENCE'
    return {'schema': SCHEMA, 'gate': 'G5_RELATION', 'status': status, 'value': values[0],
            'specification_id': specs[0], 'record_id': record_ids[0], 'profiles': rows,
            'conclusion_scope': 'two declared profiles on the same observed slot; no prevalence or analyser failure'}


__all__ = ['SCHEMA', 'CARRIER_SCHEMA', 'representation_status', 'availability_status',
           'evaluate_availability', 'consumer_full_status', 'make_carrier', 'qualify_consumer', 'compare_profiles']
