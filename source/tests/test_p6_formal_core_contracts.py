"""Regression tests for the Phase-6 formal-core contract repairs."""
from __future__ import annotations

import json
import unittest
from decimal import Decimal
from pathlib import Path

import codeprobe_interpretation as interpretation
import codeprobe_measurement_kernel as kernel
import codeprobe_numeric_policy as numeric_policy

ROOT = Path(__file__).resolve().parents[1]

def _callable_record(result: dict, observation_id: str) -> dict:
    return next(r for r in result["observations"] if r["observation_id"] == observation_id)

class FormalCoreContractTests(unittest.TestCase):
    def test_kernel_candidate_version_is_explicit(self) -> None:
        self.assertEqual(kernel.KERNEL_VERSION, "1.2.0")

    def test_mccabe_contract_is_ordinal_and_versioned(self) -> None:
        source = b"def f(x):\n    if x:\n        return 1\n    return 0\n"
        result = kernel.measure_bytes(source, language="python", path="sample.py")
        record = _callable_record(result, "python.callable.mccabe_complexity")
        self.assertEqual(record["measurement_scale"], "ordinal")
        self.assertTrue(record["specification_id"].endswith("/1.2.0"))
        self.assertEqual(record["value"], 2)

    def test_decision_point_count_remains_ratio(self) -> None:
        source = b"def f(x):\n    if x:\n        return 1\n    return 0\n"
        result = kernel.measure_bytes(source, language="python", path="sample.py")
        record = _callable_record(result, "python.callable.decision_point_count")
        self.assertEqual(record["measurement_scale"], "ratio")
        self.assertTrue(record["specification_id"].endswith("/1.1.1"))
        self.assertEqual(record["value"], 1)

    def test_record_id_is_stable_observation_slot_while_digest_tracks_content(self) -> None:
        source_a = b"def f(x):\n    if x:\n        return 1\n    return 0\n"
        source_b = b"def f(x):\n    if x:\n        return 1\n    value = 0\n    return value\n"
        result_a = kernel.measure_bytes(source_a, language="python", path="sample.py")
        result_b = kernel.measure_bytes(source_b, language="python", path="sample.py")
        a = _callable_record(result_a, "python.callable.mccabe_complexity")
        b = _callable_record(result_b, "python.callable.mccabe_complexity")
        self.assertEqual(a["entity"]["entity_id"], b["entity"]["entity_id"])
        self.assertEqual(a["value"], b["value"])
        self.assertEqual(a["record_id"], b["record_id"])
        self.assertNotEqual(a["source_evidence_ids"], b["source_evidence_ids"])
        self.assertNotEqual(result_a["measurement_digest"], result_b["measurement_digest"])

    def test_path_relocation_does_not_change_slot_or_content_identity(self) -> None:
        source = b"def f(x):\n    return x + 1\n"
        result_a = kernel.measure_bytes(source, language="python", path="a/sample.py")
        result_b = kernel.measure_bytes(source, language="python", path="b/sample.py")
        a = _callable_record(result_a, "python.callable.mccabe_complexity")
        b = _callable_record(result_b, "python.callable.mccabe_complexity")
        self.assertEqual(a["record_id"], b["record_id"])
        self.assertEqual(result_a["measurement_digest"], result_b["measurement_digest"])

    def test_catalogue_declares_repaired_measurement_scale(self) -> None:
        catalogue = json.loads((ROOT / "research" / "observation-catalogue.v1.json").read_text(encoding="utf-8"))
        card = next(item for item in catalogue["observations"] if item["observation_id"] == "python.callable.mccabe_complexity")
        self.assertEqual(card["measurement_scale"], "ordinal")
        self.assertEqual(card["specification_id"], "codeprobe-observation/python.callable.mccabe_complexity/1.2.0")
        self.assertEqual(card["algorithm"]["version"], "1.2.0")

    def test_scale_counterexample_is_recorded_by_contract(self) -> None:
        # d is a count with meaningful ratios. C=1+d is an affine transform;
        # ratio comparisons are therefore not invariant to the offset.
        d1, d2 = Decimal(1), Decimal(3)
        c1, c2 = Decimal(1) + d1, Decimal(1) + d2
        self.assertNotEqual(d2 / d1, c2 / c1)

    def test_decimal_boundary_policy_is_deterministic(self) -> None:
        result = numeric_policy.compare_decimal(
            "1000000", "1000000.000001",
            absolute_tolerance="1e-10", relative_tolerance="1e-12",
        )
        self.assertEqual(result["status"], "within_tolerance")
        self.assertEqual(result["equality_rule"], "delta <= tolerance")

    def test_decimal_just_outside_boundary_fails(self) -> None:
        result = numeric_policy.compare_decimal(
            "1000000", "1000000.0000011",
            absolute_tolerance="1e-10", relative_tolerance="1e-12",
        )
        self.assertEqual(result["status"], "outside_tolerance")

    def test_binary64_boundary_is_not_promoted_to_pass(self) -> None:
        result = numeric_policy.compare_binary64(
            1_000_000.0, 1_000_000.000001,
            absolute_tolerance="1e-10", relative_tolerance="1e-12",
        )
        self.assertIn(result["status"], {"outside_tolerance", "indeterminate_boundary"})
        self.assertNotEqual(result["status"], "within_tolerance")

    def test_numeric_policy_is_symmetric(self) -> None:
        left = numeric_policy.compare_decimal("3.0", "3.000000000001", absolute_tolerance="1e-10", relative_tolerance="1e-12")
        right = numeric_policy.compare_decimal("3.000000000001", "3.0", absolute_tolerance="1e-10", relative_tolerance="1e-12")
        self.assertEqual(left["status"], right["status"])
        self.assertEqual(left["delta"], right["delta"])
        self.assertEqual(left["tolerance"], right["tolerance"])

    def test_interpretation_admits_candidate_component_inventory(self) -> None:
        got = interpretation.threshold_decision(13, {"lower": 8, "nominal": 10, "upper": 12})
        self.assertEqual(got["status"], "review_opportunity")
        self.assertEqual(got["possible_predicates"], [True])

    def test_candidate_result_passes_internal_contract_validation(self) -> None:
        source = b"def f(x):\n    if x:\n        return 1\n    return 0\n"
        result = kernel.measure_bytes(source, language="python", path="sample.py")
        kernel.validate_kernel_result(result)
        schema = json.loads((ROOT / "schemas" / "codeprobe-measurement-kernel-result-v1.schema.json").read_text(encoding="utf-8"))
        mccabe = next(
            branch
            for branch in schema["$defs"]["observation"]["allOf"]
            if branch.get("if", {}).get("properties", {}).get("observation_id", {}).get("const")
            == "python.callable.mccabe_complexity"
        )
        self.assertEqual(mccabe["then"]["properties"]["measurement_scale"]["const"], "ordinal")

