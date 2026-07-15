from __future__ import annotations

import copy
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evaluation"))
import traceability_gate
import render_traceability_docs


def complete_traceability() -> dict:
    requirements = [
        {"id": "BR-001", "status": "in_scope", "type": "business", "statement": "予約受付の業務手順を標準化する", "user_story_ids": ["US-001"], "flow_step_ids": ["BF-001-S01"]},
        {"id": "FR-001", "status": "in_scope", "type": "functional", "statement": "生徒は空き枠を予約できる", "user_story_ids": ["US-001"], "flow_step_ids": ["BF-001-S01"]},
        {"id": "NFR-001", "status": "in_scope", "type": "non_functional", "statement": "予約確定は5秒以内に通知する", "user_story_ids": ["US-001"], "flow_step_ids": ["BF-001-S01"]},
    ]
    acceptance_tests = []
    system_tests = []
    for index, requirement in enumerate(requirements, start=1):
        acceptance_id = f"AC-{index:03d}"
        system_id = f"ST-{index:03d}"
        acceptance_tests.append({
            "id": acceptance_id,
            "status": "in_scope",
            "user_story_ids": ["US-001"],
            "requirement_ids": [requirement["id"]],
            "flow_step_ids": ["BF-001-S01"],
            "preconditions": ["予約可能なレッスン枠がある"],
            "steps": ["生徒が予約を確定する"],
            "expected_results": [requirement["statement"]],
        })
        system_tests.append({
            "id": system_id,
            "status": "in_scope",
            "test_type": "performance" if requirement["id"] == "NFR-001" else "functional",
            "requirement_ids": [requirement["id"]],
            "acceptance_test_ids": [acceptance_id],
            "preconditions": ["テスト用の予約枠がある"],
            "steps": ["予約APIを実行する"],
            "expected_results": ["要件を満たす結果が返る"],
        })
    return {
        "version": "1.0",
        "user_stories": [{"id": "US-001", "status": "in_scope", "statement": "生徒はレッスンを予約したい。予約漏れを防ぐため。"}],
        "business_flows": [{"id": "BF-001", "status": "in_scope", "name": "レッスン予約", "steps": [{"id": "BF-001-S01", "action": "生徒が予約を確定する", "user_story_ids": ["US-001"]}]}],
        "requirements": requirements,
        "acceptance_tests": acceptance_tests,
        "system_tests": system_tests,
    }


class TraceabilityGateTest(unittest.TestCase):
    def test_complete_chain_with_business_functional_and_nfr_passes(self):
        self.assertEqual(traceability_gate.validate(complete_traceability()), [])

    def test_missing_system_test_is_detected_as_orphan(self):
        data = complete_traceability()
        data["system_tests"] = []
        failures = traceability_gate.validate(data)
        self.assertTrue(any("要件が孤立しています: BR-001" in failure for failure in failures))
        self.assertTrue(any("受入試験が孤立しています: AC-001" in failure for failure in failures))

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
        data = {"version": "1.0", "user_stories": ["bad"], "business_flows": ["bad"], "requirements": ["bad"], "acceptance_tests": ["bad"], "system_tests": ["bad"]}
        failures = traceability_gate.validate(data)
        self.assertTrue(any("user_stories[0] はオブジェクト" in failure for failure in failures))

    def test_requirement_story_must_match_its_flow_step_story(self):
        data = complete_traceability()
        data["business_flows"][0]["steps"][0]["user_story_ids"] = ["US-002"]
        data["user_stories"].append({"id": "US-002", "status": "in_scope", "statement": "別の利用者は別の目的を達成したい。"})
        failures = traceability_gate.validate(data)
        self.assertTrue(any("要件 BR-001: 対象USと関連業務フロー手順の対象USが対応していません" in failure for failure in failures))

    def test_deferred_record_requires_reason(self):
        data = copy.deepcopy(complete_traceability())
        data["user_stories"][0]["status"] = "deferred"
        failures = traceability_gate.validate(data)
        self.assertTrue(any("deferred には reason が必要" in failure for failure in failures))

    def test_system_test_must_cover_a_requirement_of_its_acceptance_test(self):
        data = complete_traceability()
        data["system_tests"][0]["acceptance_test_ids"] = ["AC-002"]
        failures = traceability_gate.validate(data)
        self.assertTrue(any("システムテスト ST-001: 受入試験 AC-002 と対象要件が対応していません" in failure for failure in failures))

    def test_renderer_includes_requirement_and_test_ids(self):
        data = complete_traceability()
        self.assertIn("BR-001", render_traceability_docs.render_requirements(data))
        self.assertIn("AC-001", render_traceability_docs.render_acceptance(data))
        self.assertIn("ST-001", render_traceability_docs.render_system(data))

    def test_renderer_excludes_deferred_items_from_execution_documents(self):
        data = complete_traceability()
        data["requirements"].append({"id": "FR-999", "status": "deferred", "reason": "次期リリースで検討する"})
        self.assertNotIn("FR-999", render_traceability_docs.render_requirements(data))
