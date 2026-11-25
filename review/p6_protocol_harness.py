#!/usr/bin/env python3
"""Independent Phase-6 protocol and formal-core verification harness."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import json
import platform
import sys
from dataclasses import dataclass, asdict
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable

HARNESS_VERSION = "1.0.0"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass
class Result:
    test_id: str
    status: str
    mechanism: str
    checks: int
    details: dict[str, Any]
    limitation: str = ""


def run(test_id: str, mechanism: str, fn: Callable[[], tuple[int, dict[str, Any]]], limitation: str = "") -> Result:
    try:
        checks, details = fn()
        return Result(test_id, "PASS", mechanism, checks, details, limitation)
    except Exception as exc:  # every failure is retained in the output
        return Result(test_id, "FAIL", mechanism, 1, {"error_type": type(exc).__name__, "error": str(exc)}, limitation)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--phase-dir", type=Path, required=True)
    ap.add_argument("--p3-results", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    root = args.root.resolve()
    phase = args.phase_dir.resolve()
    sys.path.insert(0, str(root / "src"))
    mk = importlib.import_module("codeprobe_measurement_kernel")
    ip = importlib.import_module("codeprobe_interpretation")
    np = importlib.import_module("codeprobe_numeric_policy")

    tests: list[Result] = []

    def threshold() -> tuple[int, dict[str, Any]]:
        checks = 0
        failures = []
        endpoint_equal = 0
        for lo in range(0, 9):
            for hi in range(lo, 11):
                for nominal in range(lo, hi + 1):
                    levels = {"lower": lo, "nominal": nominal, "upper": hi}
                    for x in range(0, 14):
                        checks += 1
                        full = sorted({x > t for t in range(lo, hi + 1)})
                        endpoints = sorted({x > t for t in {lo, nominal, hi}})
                        status = "no_rule_trigger" if full == [False] else "review_opportunity" if full == [True] else "abstain"
                        expected = {
                            "nominal_predicate": x > nominal,
                            "possible_predicates": full,
                            "status": status,
                            "policy_sensitivity": "boundary_sensitive" if len(full) == 2 else "stable_over_declared_threshold_set",
                        }
                        got = ip.threshold_decision(x, levels)
                        if got != expected or endpoints != full:
                            failures.append({"L": lo, "U": hi, "nominal": nominal, "x": x, "got": got, "expected": expected})
                        else:
                            endpoint_equal += 1
        if failures:
            raise AssertionError(f"{len(failures)} threshold counterexamples")
        return checks, {"admissible_cases": checks, "endpoint_equivalence_cases": endpoint_equal, "counterexamples": 0}

    tests.append(run("P6-T01", "Independent full-interval enumeration against the implementation endpoint decision", threshold,
                     "The loop is a bounded executable check; the protocol also carries the general monotonicity proof."))

    def witnesses() -> tuple[int, dict[str, Any]]:
        p3 = json.loads(args.p3_results.read_text(encoding="utf-8"))
        index = {t["test_id"]: t for t in p3["tests"]}
        required = ["P3-T04", "P3-T05", "P3-T06", "P3-T07", "P3-T14"]
        bad = {tid: index.get(tid, {}).get("status") for tid in required if index.get(tid, {}).get("status") != "PASS"}
        if bad:
            raise AssertionError(f"witness prerequisites failed: {bad}")
        return len(required), {"witness_tests": required, "all_pass": True, "claims":"selected failed implications only"}

    tests.append(run("P6-T02", "Revalidation of independent Phase-3 witness results", witnesses,
                     "This check verifies preserved signed audit results; it does not recreate absent CE09/CE11 runs."))

    def scale() -> tuple[int, dict[str, Any]]:
        source = b"def f(x):\n    if x:\n        return 1\n    return 0\n"
        result = mk.measure_bytes(source, language="python", path="scale.py")
        by_id = {r["observation_id"]: r for r in result["observations"] if r["entity"]["entity_kind"] == "python_callable"}
        decision = by_id["python.callable.decision_point_count"]
        complexity = by_id["python.callable.mccabe_complexity"]
        assertions = [
            mk.KERNEL_VERSION == "1.2.0",
            decision["measurement_scale"] == "ratio",
            complexity["measurement_scale"] == "ordinal",
            decision["specification_id"].endswith("/1.1.1"),
            complexity["specification_id"].endswith("/1.2.0"),
            complexity["value"] == 1 + decision["value"],
            Decimal(3) / Decimal(1) != Decimal(4) / Decimal(2),
        ]
        if not all(assertions):
            raise AssertionError(f"scale assertions={assertions}")
        return len(assertions), {"d1_d2_ratio":"3", "C1_C2_ratio":"2", "numeric_value_changed":False}

    tests.append(run("P6-T03", "Direct candidate execution plus independent affine-scale counterexample", scale))

    def identity() -> tuple[int, dict[str, Any]]:
        a = mk.measure_bytes(b"def f(x):\n    if x:\n        return 1\n    return 0\n", language="python", path="sample.py")
        b = mk.measure_bytes(b"def f(x):\n    if x:\n        return 1\n    value = 0\n    return value\n", language="python", path="sample.py")
        c = mk.measure_bytes(b"def f(x):\n    if x:\n        return 1\n    return 0\n", language="python", path="moved/sample.py")
        get = lambda result: next(r for r in result["observations"] if r["observation_id"] == "python.callable.mccabe_complexity")
        ra, rb, rc = get(a), get(b), get(c)
        assertions = [
            ra["entity"]["entity_id"] == rb["entity"]["entity_id"],
            ra["record_id"] == rb["record_id"],
            ra["source_evidence_ids"] != rb["source_evidence_ids"],
            a["measurement_digest"] != b["measurement_digest"],
            ra["record_id"] == rc["record_id"],
            a["measurement_digest"] == c["measurement_digest"],
            ra["specification_id"].endswith("/1.2.0"),
        ]
        if not all(assertions):
            raise AssertionError(f"identity assertions={assertions}")
        return len(assertions), {"content_change":"slot stable, digest changed", "path_change":"slot and digest stable"}

    tests.append(run("P6-T04", "Metamorphic identity tests over content-only and path-only changes", identity,
                     "record_id is scoped within a measurement result and is not claimed globally unique."))

    def numeric() -> tuple[int, dict[str, Any]]:
        boundary = np.compare_decimal("1000000", "1000000.000001", absolute_tolerance="1e-10", relative_tolerance="1e-12")
        outside = np.compare_decimal("1000000", "1000000.0000011", absolute_tolerance="1e-10", relative_tolerance="1e-12")
        reverse = np.compare_decimal("1000000.000001", "1000000", absolute_tolerance="1e-10", relative_tolerance="1e-12")
        exact = np.compare_decimal("5", "5", absolute_tolerance="0", relative_tolerance="0")
        binary = np.compare_binary64(1_000_000.0, 1_000_000.000001, absolute_tolerance="1e-10", relative_tolerance="1e-12")
        assertions = [
            boundary["status"] == "within_tolerance",
            outside["status"] == "outside_tolerance",
            boundary["delta"] == reverse["delta"],
            boundary["tolerance"] == reverse["tolerance"],
            exact["status"] == "within_tolerance",
            boundary["equality_rule"] == "delta <= tolerance",
            binary["status"] != "within_tolerance",
            binary["pass_admission"] == "indeterminate_boundary is not a pass",
        ]
        if not all(assertions):
            raise AssertionError(f"numeric assertions={assertions}; binary={binary}")
        return len(assertions), {"decimal_boundary":boundary, "binary64_boundary":binary}

    tests.append(run("P6-T05", "Exact Decimal arithmetic and conservative half-ULP interval diagnosis", numeric,
                     "The policy is prospective and does not relabel historical floating-point outputs."))

    def applicability() -> tuple[int, dict[str, Any]]:
        valid = mk.measure_bytes(b"x = 1\n", language="python", path="valid.py")
        zero = next(r for r in valid["observations"] if r["observation_id"] == "source.blank_line_count")
        invalid = mk.measure_bytes(b"def f(:\n", language="python", path="invalid.py")
        unavailable = next(r for r in invalid["observations"] if r["observation_id"] == "python.function_definition_count")
        assertions = [
            zero["applicability"]["state"] == "observed",
            zero["value"] == 0,
            unavailable["applicability"]["state"] == "unavailable",
            unavailable["value"] is None,
            bool(unavailable["applicability"]["reason_code"]),
        ]
        broken = dict(zero)
        broken["applicability"] = dict(zero["applicability"], state="unavailable", reason_code="X", reason="X")
        try:
            mk.validate_observation_record(broken)
        except ValueError:
            assertions.append(True)
        else:
            assertions.append(False)
        if not all(assertions):
            raise AssertionError(f"applicability assertions={assertions}")
        return len(assertions), {"observed_zero_preserved":True,"unavailable_null_preserved":True,"invalid_pair_rejected":True}

    tests.append(run("P6-T06", "Generated zero/unavailable cases and mutation rejection", applicability))

    def schemas() -> tuple[int, dict[str, Any]]:
        import jsonschema
        catalogue = json.loads((root / "research/observation-catalogue.v1.json").read_text(encoding="utf-8"))
        cat_schema = json.loads((root / "schemas/codeprobe-observation-catalogue-v1.schema.json").read_text(encoding="utf-8"))
        result_schema = json.loads((root / "schemas/codeprobe-measurement-kernel-result-v1.schema.json").read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(cat_schema).validate(catalogue)
        checks = 1
        details = {}
        for language, data, path in [
            ("python", b"def f():\n    return 1\n", "a.py"),
            ("markdown", b"# H\n\ntext\n", "a.md"),
            ("text", b"alpha\n", "a.txt"),
        ]:
            result = mk.measure_bytes(data, language=language, path=path)
            mk.verify_result_against_catalogue(result, catalogue)
            jsonschema.Draft202012Validator(result_schema).validate(result)
            checks += 2
            details[language] = {"observations":len(result["observations"]),"digest":result["measurement_digest"]}
        return checks, details

    tests.append(run("P6-T07", "JSON Schema 2020-12 validation plus kernel-to-catalogue semantic validation", schemas))

    def claims() -> tuple[int, dict[str, Any]]:
        claim_data = json.loads((phase / "APEX_P6_CodeProbe_ClaimScopeFreeze_v1.json").read_text(encoding="utf-8"))
        retained = claim_data["retained_principal_claims"]
        historic = claim_data["historical_context_claims"]
        assertions = [len(retained) == 9, len(historic) == 8]
        assertions.extend(c["principal"] == "yes" and c["status"] == "PASS_PHASE6" and c["severity"] in {"SV2","SV3"} for c in retained)
        assertions.extend(c["status"] == "UNVERIFIED_CONTEXT_ONLY" for c in historic)
        if not all(assertions):
            raise AssertionError("claim freeze is incomplete")
        return len(assertions), {"retained":len(retained),"historical_context":len(historic),"all_retained_SV2_plus":True}

    tests.append(run("P6-T08", "Machine-readable claim-scope completeness and severity check", claims,
                     "Severity status is for the frozen Phase-6 obligations; Phase 7 must integrate executable claims-as-tests."))

    def deviations() -> tuple[int, dict[str, Any]]:
        rows = list(csv.DictReader((phase / "APEX_P6_CodeProbe_DeviationLog_v1.csv").open(encoding="utf-8")))
        ids = {r["id"] for r in rows}
        required = {f"DEV-{i:02d}" for i in range(1,11)}
        if ids != required:
            raise AssertionError(f"deviation ids differ: {sorted(ids ^ required)}")
        if not all(r["consequence"] and r["handling"] for r in rows):
            raise AssertionError("deviation without consequence or handling")
        return len(rows) * 3, {"deviations":len(rows),"required_set_complete":True}

    tests.append(run("P6-T09", "Exact deviation-ID set plus consequence/handling completeness", deviations,
                     "Unknown undisclosed historical deviations cannot be ruled out; principal claims no longer depend on absent historical runs."))

    def pap() -> tuple[int, dict[str, Any]]:
        data = json.loads((phase / "APEX_P6_CodeProbe_DecisiveStudyPAP_v1.json").read_text(encoding="utf-8"))
        assertions = [
            data["status"] == "registration_ready_not_registered_not_executed",
            len(data["arms"]) == 3,
            data["pilot_sample"]["scenarios"] == 24,
            data["pilot_sample"]["minimum_projects"] >= 6,
            len(data["pilot_continuation_rules"]) == 4,
            bool(data["primary_estimand"]),
            bool(data["ground_truth"]["blinding"]),
            bool(data["analysis"]["missingness"]),
            bool(data["falsification"]),
            "ethics" in data,
            "registration_trigger" in data,
        ]
        if not all(assertions):
            raise AssertionError(f"PAP assertions={assertions}")
        return len(assertions), {"pilot_scenarios":24,"minimum_projects":data["pilot_sample"]["minimum_projects"],"continuation_rules":4}

    tests.append(run("P6-T10", "Machine-readable pre-analysis-plan completeness check", pap,
                     "Registration readiness is a document property; no study outcome is implied."))

    def radii() -> tuple[int, dict[str, Any]]:
        rows = list(csv.DictReader((phase / "APEX_P6_CodeProbe_RobustnessRadiusRegister_v2.csv").open(encoding="utf-8")))
        expected = {f"P6-C{i:02d}" for i in range(1,10)}
        got = {r["claim_id"] for r in rows}
        if got != expected:
            raise AssertionError(f"radius claims differ: {sorted(got ^ expected)}")
        if not all(r["radius"] and r["unit"] and r["overturning_event"] and r["status"] == "REPORTED" for r in rows):
            raise AssertionError("incomplete robustness row")
        return len(rows) * 4, {"claims_with_radius":len(rows),"coverage":"9/9"}

    tests.append(run("P6-T11", "Exact retained-claim join against robustness-radius register", radii,
                     "Several radii are discrete failure radii, not population sensitivity estimates."))

    def protocol_lock() -> tuple[int, dict[str, Any]]:
        protocol = json.loads((phase / "APEX_P6_CodeProbe_Protocol_v1.json").read_text(encoding="utf-8"))
        claims = json.loads((phase / "APEX_P6_CodeProbe_ClaimScopeFreeze_v1.json").read_text(encoding="utf-8"))
        retained = [c["id"] for c in claims["retained_principal_claims"]]
        assertions = [
            protocol["retained_claim_ids"] == retained,
            len(protocol["gates"]) == 6,
            protocol["claim_scope_strategy"] == "BOUNDED_CURRENT_EVIDENCE",
            protocol["status"].startswith("reconstructed_retrospective"),
            protocol["reproduction"]["network_required"] is False,
            protocol["reproduction"]["historical_ce09_ce11_required"] is False,
            "No p-value" in protocol["decision_rules"][3],
            "not a preregistration" not in protocol.get("purpose", "").lower(),
        ]
        if not all(assertions):
            raise AssertionError(f"protocol assertions={assertions}")
        return len(assertions), {"gate_count":6,"retained_claim_count":len(retained),"scope_locked":True}

    tests.append(run("P6-T12", "Cross-file claim, gate, temporal-status and reproduction lock", protocol_lock))

    failed = [r.test_id for r in tests if r.status != "PASS"]
    payload = {
        "schema":"apex-codeprobe-phase6-protocol-harness-results/v1",
        "harness_version":HARNESS_VERSION,
        "status":"PASS" if not failed else "FAIL",
        "failed_tests":failed,
        "environment":{"python":platform.python_version(),"implementation":platform.python_implementation(),"platform":platform.platform()},
        "scope":{"candidate_root":str(root),"phase_dir":str(phase),"network_policy":{"external_network_required":False,"external_network_intentional_use":False,"loopback_used_by_source_tests":False,"telemetry":"not_syscall_instrumented"},"historical_ce09_ce11_available":False},
        "input_sha256":{
            "kernel":sha256_file(root / "src/codeprobe_measurement_kernel.py"),
            "numeric_policy":sha256_file(root / "src/codeprobe_numeric_policy.py"),
            "catalogue":sha256_file(root / "research/observation-catalogue.v1.json"),
            "protocol":sha256_file(phase / "APEX_P6_CodeProbe_Protocol_v1.json"),
            "claim_scope":sha256_file(phase / "APEX_P6_CodeProbe_ClaimScopeFreeze_v1.json"),
            "p3_results":sha256_file(args.p3_results),
        },
        "tests":[asdict(r) for r in tests],
        "summary":{"tests":len(tests),"passed":sum(r.status=="PASS" for r in tests),"failed":len(failed),"checks":sum(r.checks for r in tests)},
    }
    args.output.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(payload["summary"],sort_keys=True))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
