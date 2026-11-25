#!/usr/bin/env python3
"""Run the selected local regression cohort for Source Review Evidence.

Uses the Python standard library and an existing Node executable. It never
installs dependencies. Existing HTTP tests bind loopback addresses only.
The JavaScript suites use protocol/DOM doubles; they do not qualify a browser
or Pyodide. Research experiments and historical release gates are not run.
JSON results are written to standard output; temporary files stay outside the
distribution. Use --list to inspect the exact selected test identities.
"""
from __future__ import annotations

import argparse
import collections
import contextlib
import hashlib
import importlib
import io
import json
import os
import pathlib
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

MODULES = (
    'test_runtime_smoke', 'test_project_mode', 'test_report_schema',
    'test_javascript_parser', 'test_false_positive_controls',
    'test_p6_formal_core_contracts', 'test_browser_security',
    'test_dynamic_ui_review', 'test_app_runtime_tools_paths',
    'test_calibration_profiles', 'test_process_control',
    'test_local_server', 'test_contract_repairs', 'test_worker_contract',
    'test_documentation_resources',
)
NODE_SUITES = ('check_worker_protocol.js', 'check_input_contracts.js')


def flatten(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item


def exclusion(identity):
    if '.PublicationOverlapTests.' in identity:
        return ('Historical component release construction is outside this '
                'distribution runtime scope; the standalone Node input suite '
                'runs separately.')
    if identity.endswith('.test_hermetic_worker_protocol_races'):
        return 'The identical Node protocol suite runs separately with its own log.'
    if identity.endswith('.test_governance_metadata_does_not_invent_authorship_or_enforcement'):
        return ('Historical component-root citation and ownership layout; '
                'current distribution metadata has a separate documentary audit.')
    return None


def select_tests(root):
    source = root / 'source'
    sys.path[:0] = [str(source / 'tests'), str(source / 'src'), str(source / 'tools')]
    tests, excluded = [], []
    for name in MODULES:
        module = importlib.import_module(name)
        for test in flatten(unittest.defaultTestLoader.loadTestsFromModule(module)):
            reason = exclusion(test.id())
            if reason:
                excluded.append({'id': test.id(), 'reason': reason})
            else:
                tests.append(test)
    return tests, excluded


class RecordedResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records = []

    def startTest(self, test):
        self.started = time.monotonic()
        super().startTest(test)

    def record(self, test, status, detail=None):
        value = {'id': test.id(), 'status': status,
                 'seconds': round(time.monotonic() - self.started, 6)}
        if detail is not None:
            value['detail'] = detail
        self.records.append(value)

    def addSuccess(self, test):
        super().addSuccess(test)
        self.record(test, 'PASS')

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.record(test, 'FAIL', self._exc_info_to_string(err, test))

    def addError(self, test, err):
        super().addError(test, err)
        self.record(test, 'ERROR', self._exc_info_to_string(err, test))

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.record(test, 'SKIP', reason)

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is not None:
            self.record(subtest, 'SUBTEST_FAILURE', self._exc_info_to_string(err, test))


def worker(root, list_only):
    diagnostics = io.StringIO()
    with contextlib.redirect_stdout(diagnostics), contextlib.redirect_stderr(diagnostics):
        tests, excluded = select_tests(root)
        identities = [test.id() for test in tests]
        result = None
        if not list_only:
            result = unittest.TextTestRunner(stream=diagnostics, verbosity=2,
                                             resultclass=RecordedResult).run(unittest.TestSuite(tests))
    selected_files = [{
        'path': 'source/tests/' + name + '.py',
        'sha256': hashlib.sha256((root / 'source/tests' / (name + '.py')).read_bytes()).hexdigest(),
    } for name in MODULES]
    output = {
        'schema': 'source-review-evidence-local-python-checks/1',
        'status': 'LISTED_NOT_EXECUTED' if list_only else (
            'PASS_SELECTED_LOCAL_REGRESSIONS_WITH_SKIPS' if result.wasSuccessful() and result.skipped else
            'PASS_SELECTED_LOCAL_REGRESSIONS' if result.wasSuccessful() else 'FAIL_SELECTED_LOCAL_REGRESSIONS'),
        'python': sys.version, 'platform': platform.platform(),
        'flags': {'isolated': sys.flags.isolated, 'no_site': sys.flags.no_site,
                  'dont_write_bytecode': sys.dont_write_bytecode},
        'selected_test_ids': identities, 'selected_methods': len(identities),
        'module_method_counts': dict(collections.Counter(i.split('.')[0] for i in identities)),
        'excluded_checks_in_selected_modules': excluded,
        'not_selected_modules': sorted(p.stem for p in (root / 'source/tests').glob('test_*.py')
                                       if p.stem not in MODULES),
        'not_selected_scope': ('Historical release/recovery/institutional packaging gates, full dependency/coverage '
                               'audits, documentation recipes and native Pyodide fixture gates have separate scope; '
                               'their presence is not a claim that they passed.'),
        'test_files': selected_files, 'diagnostics': diagnostics.getvalue(),
        'scientific_experiments_run': False, 'strict_reproduction': False,
        'native_browser_pyodide_qualification': False,
    }
    if result is not None:
        output.update(tests_run=result.testsRun, failures=len(result.failures),
                      errors=len(result.errors), skipped=len(result.skipped), records=result.records)
    return output, (0 if list_only or result.wasSuccessful() else 1)


def run_checks(root, list_only):
    execution_environment = os.environ.copy()
    for key in ('TMPDIR', 'TMP', 'TEMP'):
        execution_environment[key] = str(root.parent)
    command = [sys.executable, '-I', '-S', '-B', str(pathlib.Path(__file__).resolve()),
               '--worker', '--root', str(root)]
    if list_only:
        command.append('--list')
    try:
        process = subprocess.run(command, capture_output=True, text=True,
                                 encoding='utf-8', timeout=300, env=execution_environment)
        python_result = json.loads(process.stdout)
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        return {'status': 'FAIL_PYTHON_CHECK_PROCESS',
                'error': f'{type(exc).__name__}: {exc}'}, 2
    code = process.returncode
    node_results = []
    node = shutil.which('node')
    for name in NODE_SUITES:
        relative = 'source/tools/' + name
        if list_only:
            node_results.append({'path': relative, 'status': 'LISTED_NOT_EXECUTED',
                                 'node_available': bool(node)})
            continue
        if node is None:
            node_results.append({'path': relative, 'status': 'NOT_RUN_NODE_UNAVAILABLE'})
            code = code or 2
            continue
        try:
            completed = subprocess.run([node, str(root / relative)], cwd=root / 'source',
                                       capture_output=True, text=True, encoding='utf-8', timeout=120,
                                       env=execution_environment)
            node_results.append({'path': relative, 'status': 'PASS' if completed.returncode == 0 else 'FAIL',
                                 'returncode': completed.returncode, 'stdout': completed.stdout,
                                 'stderr': completed.stderr,
                                 'scope': 'Hermetic protocol/DOM doubles; no native browser/Pyodide execution.'})
            if completed.returncode:
                code = code or 1
        except (OSError, subprocess.TimeoutExpired) as exc:
            node_results.append({'path': relative, 'status': 'FAIL_PROCESS',
                                 'error': f'{type(exc).__name__}: {exc}'})
            code = code or 2
    output = {
        'schema': 'source-review-evidence-local-checks/1', 'version': '1.0.0',
        'status': 'LISTED_NOT_EXECUTED' if list_only and code == 0 else
                  'PASS_SELECTED_LOCAL_CHECKS' if code == 0 else 'FAIL_OR_INCOMPLETE_LOCAL_CHECKS',
        'python': python_result, 'node': node_results,
        'qualification': 'Selected local regressions only. Skipped platform checks remain unqualified.',
        'scientific_experiments_run': False, 'strict_reproduction': False,
        'native_browser_pyodide_qualification': False,
    }
    return output, (0 if code == 0 else (1 if code == 1 else 2))



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=pathlib.Path,
                        default=pathlib.Path(__file__).resolve().parents[1])
    parser.add_argument('--list', action='store_true', help='List selected checks without running test methods.')
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    root = args.root.resolve()
    if args.worker:
        try:
            output, code = worker(root, args.list)
        except Exception as exc:
            output, code = {'status': 'FAIL_CHECK_SETUP', 'error': f'{type(exc).__name__}: {exc}'}, 2
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return code
    try:
        if not (root / 'source/tests').is_dir() or root == root.parent:
            raise ValueError('Expected a distribution containing source/tests.')
        temporary_parent = pathlib.Path(tempfile.gettempdir()).resolve()
        if temporary_parent == root or root in temporary_parent.parents:
            temporary_parent = root.parent

        def ignored(directory, names):
            excluded = []
            for name in names:
                entry = pathlib.Path(directory) / name
                if name == '__pycache__' or (name == '.git' and pathlib.Path(directory) == root):
                    excluded.append(name)
                elif entry.is_symlink():
                    raise ValueError('A distribution execution copy cannot contain symbolic links.')
            return excluded

        with tempfile.TemporaryDirectory(prefix='source-review-evidence-checks-',
                                         dir=temporary_parent) as working:
            execution_root = pathlib.Path(working) / 'distribution'
            shutil.copytree(root, execution_root, ignore=ignored)
            copied_files = sum(1 for path in execution_root.rglob('*') if path.is_file())
            output, code = run_checks(execution_root, args.list)
            output['execution_copy'] = True
            output['copy_policy'] = {
                'location': 'Temporary directory outside the input distribution',
                'copied_files': copied_files,
                'excluded': ['Root .git metadata', '__pycache__ directories'],
                'symbolic_links': 'Rejected before execution',
                'source_and_evidence': 'Copied with all other distribution files',
                'cleanup': 'Temporary copy removed before returning',
            }
    except (OSError, ValueError, shutil.Error) as exc:
        output, code = {'status': 'FAIL_EXECUTION_COPY',
                        'execution_copy': False,
                        'error': f'{type(exc).__name__}: {exc}'}, 2
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
