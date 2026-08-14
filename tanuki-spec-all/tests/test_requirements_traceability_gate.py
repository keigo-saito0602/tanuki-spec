from __future__ import annotations

import copy
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evaluation"))
import traceability_gate


def complete_traceability() -> dict:
    requirements = [
        {"id": "BR-001", "status": "in_scope", "type": "business", "statement": "予約受付の業務手順を標準化する", "user_story_ids": ["US-001"], "flow_step_ids": ["BF-001-S01"]},
        {"id": "FR-001", "status": "in_scope", "type": "functional", "statement": "生徒は空き枠を予約できる", "user_story_ids": ["US-001"], "flow_step_ids": ["BF-001-S01"]},
        {"id": "NFR-001", "status": "in_scope", "type": "non_functional", "statement": "予約確定は5秒以内に通知する", "user_story_ids": ["US-001"], "flow_step_ids": ["BF-001-S01"]},
    ]
    return {
        "version": "1.0",
        "user_stories": [{"id": "US-001", "status": "in_scope", "statement": "生徒はレッスンを予約したい。予約漏れを防ぐため。"}],
        "requirements": requirements,
    }


class TraceabilityGateTest(unittest.TestCase):
    def test_complete_chain_with_business_functional_and_nfr_passes(self):
        self.assertEqual(traceability_gate.validate(complete_traceability()), [])

    def test_unknown_story_reference_is_rejected(self):
        data = complete_traceability()
        data["requirements"][0]["user_story_ids"] = ["US-999"]
        failures = traceability_gate.validate(data)
        self.assertTrue(any("参照先が存在しません: US-999" in failure for failure in failures))

    def test_unfilled_placeholder_is_rejected(self):
        data = complete_traceability()
        data["requirements"][0]["statement"] = "<要件を記入>"
        failures = traceability_gate.validate(data)
        self.assertTrue(any("要件 BR-001: statement が必要です" in failure for failure in failures))

    def test_non_object_record_is_rejected(self):
        data = {"version": "1.0", "user_stories": ["bad"], "requirements": ["bad"]}
        failures = traceability_gate.validate(data)
        self.assertTrue(any("user_stories[0] はオブジェクト" in failure for failure in failures))

    def test_deferred_record_requires_reason(self):
        data = copy.deepcopy(complete_traceability())
        data["user_stories"][0]["status"] = "deferred"
        failures = traceability_gate.validate(data)
        self.assertTrue(any("deferred には reason が必要" in failure for failure in failures))

    def test_legacy_business_flows_key_is_rejected(self):
        """旧フラット形式（business_flows等を1ファイルに持つ）は縮小後のvalidate()が
        黙って通過させてしまう危険な後方互換の罠になる。明示的に拒否する。"""
        data = complete_traceability()
        data["business_flows"] = [{"id": "BF-001", "status": "in_scope", "name": "予約フロー", "steps": []}]
        failures = traceability_gate.validate(data)
        self.assertTrue(any("旧形式のtraceability.yaml" in failure and "business_flows" in failure for failure in failures))

    def test_legacy_acceptance_tests_key_is_rejected(self):
        data = complete_traceability()
        data["acceptance_tests"] = [{"id": "AC-001", "status": "in_scope"}]
        failures = traceability_gate.validate(data)
        self.assertTrue(any("旧形式のtraceability.yaml" in failure and "acceptance_tests" in failure for failure in failures))

    def test_legacy_system_tests_key_is_rejected(self):
        data = complete_traceability()
        data["system_tests"] = [{"id": "ST-001", "status": "in_scope"}]
        failures = traceability_gate.validate(data)
        self.assertTrue(any("旧形式のtraceability.yaml" in failure and "system_tests" in failure for failure in failures))

    def test_current_shrunk_format_without_legacy_keys_is_not_rejected(self):
        failures = traceability_gate.validate(complete_traceability())
        self.assertFalse(any("旧形式のtraceability.yaml" in failure for failure in failures))


class OptionalImplementationFieldsTest(unittest.TestCase):
    """実装状態は任意フィールド。書かなければ何も要求しない。"""

    def _requirement(self, **extra):
        return {
            "id": "FR-001",
            "status": "in_scope",
            "type": "functional",
            "statement": "システムは予約を作成する",
            "user_story_ids": ["US-001"],
            "flow_step_ids": ["BF-001-S01"],
            **extra,
        }

    def test_valid_values_are_accepted(self):
        failures: list[str] = []
        for value in ("implemented", "partial", "not_implemented"):
            traceability_gate.validate_optional_choice(
                self._requirement(implementation_status=value),
                "implementation_status",
                traceability_gate.IMPLEMENTATION_STATUS_VALUES,
                "要件",
                failures,
            )
        self.assertEqual(failures, [])

    def test_absent_field_is_accepted(self):
        failures: list[str] = []
        traceability_gate.validate_optional_choice(
            self._requirement(), "implementation_status",
            traceability_gate.IMPLEMENTATION_STATUS_VALUES, "要件", failures,
        )
        self.assertEqual(failures, [])

    def test_unknown_value_is_rejected(self):
        failures: list[str] = []
        traceability_gate.validate_optional_choice(
            self._requirement(implementation_status="implemented_with_critical_gap"),
            "implementation_status",
            traceability_gate.IMPLEMENTATION_STATUS_VALUES, "要件", failures,
        )
        self.assertEqual(len(failures), 1)
        self.assertIn("implementation_status", failures[0])

    def test_gap_severity_values(self):
        failures: list[str] = []
        for value in ("none", "minor", "critical"):
            traceability_gate.validate_optional_choice(
                self._requirement(gap_severity=value), "gap_severity",
                traceability_gate.GAP_SEVERITY_VALUES, "要件", failures,
            )
        self.assertEqual(failures, [])

    def test_draft_status_is_accepted_with_reason(self):
        self.assertIn("draft", traceability_gate.STATUS_VALUES)
        failures: list[str] = []
        record = {"id": "FR-401", "status": "draft", "reason": "Phase4構想段階のため未確定"}
        in_scope = traceability_gate.validate_status(record, "要件", failures)
        self.assertFalse(in_scope, "draft は in_scope として扱わない")
        self.assertEqual(failures, [])

    def test_draft_status_without_reason_is_rejected(self):
        failures: list[str] = []
        traceability_gate.validate_status({"id": "FR-401", "status": "draft"}, "要件", failures)
        self.assertEqual(len(failures), 1)
        self.assertIn("reason", failures[0])
