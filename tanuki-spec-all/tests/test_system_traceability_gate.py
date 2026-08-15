from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evaluation"))
import system_traceability_gate


def user_stories() -> dict[str, dict]:
    return {
        "US-001": {"id": "US-001", "status": "in_scope", "statement": "利用者は予約したい。なぜなら講座を受けたいから。"},
    }


def requirements() -> dict[str, dict]:
    return {
        "FR-001": {
            "id": "FR-001", "status": "in_scope", "type": "functional",
            "statement": "利用者は予約を確定できる", "user_story_ids": ["US-001"],
            "flow_step_ids": ["BF-001-S01"],
        },
    }


def complete_system_traceability() -> dict:
    return {
        "version": "1.0",
        "func_traceability": ["func-予約/traceability.yaml"],
        "business_flows": [
            {
                "id": "BF-001",
                "status": "in_scope",
                "name": "予約フロー",
                "steps": [{"id": "BF-001-S01", "action": "予約画面を開く", "user_story_ids": ["US-001"]}],
            }
        ],
        "acceptance_tests": [
            {
                "id": "AC-001",
                "status": "in_scope",
                "feature": "予約",
                "user_story_ids": ["US-001"],
                "requirement_ids": ["FR-001"],
                "flow_step_ids": ["BF-001-S01"],
                "scenario": {
                    "name": "予約確定",
                    "given": ["予約データがある"],
                    "when": ["確定ボタンを押す"],
                    "then": ["予約が確定する"],
                },
            }
        ],
        "system_tests": [
            {
                "id": "ST-001",
                "status": "in_scope",
                "test_type": "functional",
                "requirement_ids": ["FR-001"],
                "acceptance_test_ids": ["AC-001"],
                "preconditions": ["APIが起動している"],
                "steps": ["POST /reservations"],
                "expected_results": ["200が返る"],
            }
        ],
    }


class SystemTraceabilityGateTest(unittest.TestCase):
    def test_complete_coverage_passes(self):
        failures = system_traceability_gate.validate(complete_system_traceability(), user_stories(), requirements())
        self.assertEqual(failures, [])

    def test_flow_step_referencing_unknown_user_story_is_rejected(self):
        data = complete_system_traceability()
        data["business_flows"][0]["steps"][0]["user_story_ids"] = ["US-999"]
        failures = system_traceability_gate.validate(data, user_stories(), requirements())
        self.assertTrue(any("US-999" in failure for failure in failures))

    def test_business_flow_missing_name_is_rejected(self):
        data = complete_system_traceability()
        del data["business_flows"][0]["name"]
        failures = system_traceability_gate.validate(data, user_stories(), requirements())
        self.assertTrue(any("業務フロー" in failure and "name" in failure for failure in failures))

    def test_business_flow_step_id_not_prefixed_by_flow_id_is_rejected(self):
        data = complete_system_traceability()
        data["business_flows"][0]["steps"][0]["id"] = "BF-002-S01"
        failures = system_traceability_gate.validate(data, user_stories(), requirements())
        self.assertTrue(any("業務フローIDで始めて" in failure for failure in failures))

    def test_business_flow_step_missing_action_is_rejected(self):
        data = complete_system_traceability()
        del data["business_flows"][0]["steps"][0]["action"]
        failures = system_traceability_gate.validate(data, user_stories(), requirements())
        self.assertTrue(any("業務フロー手順" in failure and "action" in failure for failure in failures))

    def test_acceptance_test_referencing_unknown_requirement_is_rejected(self):
        data = complete_system_traceability()
        data["acceptance_tests"][0]["requirement_ids"] = ["FR-999"]
        failures = system_traceability_gate.validate(data, user_stories(), requirements())
        self.assertTrue(any("FR-999" in failure for failure in failures))

    def test_acceptance_test_flow_step_not_aligned_with_requirement_is_rejected(self):
        """受入試験のflow_step_idsが、紐づく要件のflow_step_idsと対応しないと拒否する。"""
        data = complete_system_traceability()
        data["business_flows"][0]["steps"].append(
            {"id": "BF-001-S02", "action": "空きを確認する", "user_story_ids": ["US-001"]}
        )
        data["acceptance_tests"][0]["flow_step_ids"] = ["BF-001-S02"]  # 要件はBF-001-S01のみ参照
        failures = system_traceability_gate.validate(data, user_stories(), requirements())
        self.assertTrue(any("業務フロー手順が対応していません" in failure for failure in failures))

    def test_system_test_missing_preconditions_is_rejected(self):
        data = complete_system_traceability()
        del data["system_tests"][0]["preconditions"]
        failures = system_traceability_gate.validate(data, user_stories(), requirements())
        self.assertTrue(any("システムテスト" in failure and "preconditions" in failure for failure in failures))

    def test_system_test_requirement_not_aligned_with_acceptance_test_is_rejected(self):
        """システムテストのrequirement_idsが、参照する受入試験のrequirement_idsと重ならないと拒否する。"""
        data = complete_system_traceability()
        data["business_flows"][0]["steps"][0]  # noop, keep BF-001-S01
        extra_requirements = {**requirements(), "FR-002": {"id": "FR-002", "status": "in_scope", "type": "functional", "statement": "他要件", "user_story_ids": ["US-001"], "flow_step_ids": []}}
        data["system_tests"][0]["requirement_ids"] = ["FR-002"]
        failures = system_traceability_gate.validate(data, user_stories(), extra_requirements)
        self.assertTrue(any("対象要件が対応していません" in failure for failure in failures))

    def test_requirement_covered_only_by_acceptance_test_is_rejected(self):
        """要件はACとSTの両方に個別にカバーされる必要がある（ORではなくANDで2種の孤立検出）。"""
        data = complete_system_traceability()
        data["system_tests"] = []
        failures = system_traceability_gate.validate(data, user_stories(), requirements())
        self.assertTrue(any("FR-001" in failure and "システムテストがありません" in failure for failure in failures))

    def test_requirement_covered_only_by_system_test_is_rejected(self):
        data = complete_system_traceability()
        data["acceptance_tests"] = []
        failures = system_traceability_gate.validate(data, user_stories(), requirements())
        self.assertTrue(any("FR-001" in failure and "受入試験がありません" in failure for failure in failures))

    def test_acceptance_test_without_system_test_is_rejected(self):
        data = complete_system_traceability()
        data["system_tests"][0]["acceptance_test_ids"] = []
        failures = system_traceability_gate.validate(data, user_stories(), requirements())
        self.assertTrue(any("AC-001" in failure and "システムテストがありません" in failure for failure in failures))

    def test_user_story_without_acceptance_test_is_rejected(self):
        data = complete_system_traceability()
        data["acceptance_tests"][0]["user_story_ids"] = []
        failures = system_traceability_gate.validate(data, user_stories(), requirements())
        self.assertTrue(any("US-001" in failure and "受入試験がありません" in failure for failure in failures))

    def test_user_story_without_requirement_is_rejected(self):
        """要件から参照されないin_scopeユーザーストーリーは孤立として拒否される（US→要件）。"""
        data = complete_system_traceability()
        us = {**user_stories(), "US-002": {"id": "US-002", "status": "in_scope", "statement": "利用者は履歴を確認したい。"}}
        failures = system_traceability_gate.validate(data, us, requirements())
        self.assertTrue(any("US-002" in failure and "を満たす要件がありません" in failure for failure in failures))

    def test_business_flow_step_without_requirement_is_rejected(self):
        """どの要件のflow_step_idsからも参照されない業務フロー手順は孤立として拒否される（業務フロー手順→要件）。"""
        data = complete_system_traceability()
        data["business_flows"][0]["steps"].append(
            {"id": "BF-001-S02", "action": "空きを確認する", "user_story_ids": ["US-001"]}
        )
        failures = system_traceability_gate.validate(data, user_stories(), requirements())
        self.assertTrue(any("BF-001-S02" in failure and "を満たす要件がありません" in failure for failure in failures))

    def test_business_flow_step_without_acceptance_test_is_rejected(self):
        """どの受入試験のflow_step_idsからも参照されない業務フロー手順は孤立として拒否される（業務フロー手順→受入試験）。"""
        data = complete_system_traceability()
        data["business_flows"][0]["steps"].append(
            {"id": "BF-001-S02", "action": "空きを確認する", "user_story_ids": ["US-001"]}
        )
        failures = system_traceability_gate.validate(data, user_stories(), requirements())
        self.assertTrue(any("BF-001-S02" in failure and "の受入試験がありません" in failure for failure in failures))

    def test_business_flow_step_id_duplicate_is_rejected(self):
        data = complete_system_traceability()
        data["business_flows"][0]["steps"].append(
            {"id": "BF-001-S01", "action": "重複した手順", "user_story_ids": ["US-001"]}
        )
        failures = system_traceability_gate.validate(data, user_stories(), requirements())
        self.assertTrue(any("BF-001-S01" in failure and "IDが重複しています" in failure for failure in failures))

    def test_requirement_flow_step_id_not_defined_in_business_flows_is_rejected(self):
        """func側requirementのflow_step_idsが実際に存在するか、対象USが一致するかを検証する。"""
        requirements_with_bad_step = {
            "FR-001": {
                "id": "FR-001", "status": "in_scope", "type": "functional",
                "statement": "利用者は予約を確定できる", "user_story_ids": ["US-001"],
                "flow_step_ids": ["BF-999-S01"],
            },
        }
        failures = system_traceability_gate.validate(complete_system_traceability(), user_stories(), requirements_with_bad_step)
        self.assertTrue(any("BF-999-S01" in failure for failure in failures))

    def test_requirement_flow_step_id_with_mismatched_user_story_is_rejected(self):
        requirements_with_mismatch = {
            "FR-001": {
                "id": "FR-001", "status": "in_scope", "type": "functional",
                "statement": "利用者は予約を確定できる", "user_story_ids": ["US-999"],
                "flow_step_ids": ["BF-001-S01"],
            },
        }
        us = {**user_stories(), "US-999": {"id": "US-999", "status": "in_scope", "statement": "別のUS"}}
        failures = system_traceability_gate.validate(complete_system_traceability(), us, requirements_with_mismatch)
        self.assertTrue(any("FR-001" in failure and "対応していません" in failure for failure in failures))

    def test_empty_business_flows_is_rejected(self):
        data = complete_system_traceability()
        data["business_flows"] = []
        failures = system_traceability_gate.validate(data, user_stories(), requirements())
        self.assertTrue(any("business_flows が空です" in failure for failure in failures))

    def test_empty_acceptance_tests_is_rejected(self):
        data = complete_system_traceability()
        data["acceptance_tests"] = []
        failures = system_traceability_gate.validate(data, user_stories(), requirements())
        self.assertTrue(any("acceptance_tests が空です" in failure for failure in failures))

    def test_empty_system_tests_is_rejected(self):
        data = complete_system_traceability()
        data["system_tests"] = []
        failures = system_traceability_gate.validate(data, user_stories(), requirements())
        self.assertTrue(any("system_tests が空です" in failure for failure in failures))

    def test_scenario_examples_with_non_dict_row_is_rejected(self):
        """examples: ["不正"]のような壊れた値は、render_feature_files.pyでTypeErrorになる前にゲートで弾く。"""
        data = complete_system_traceability()
        data["acceptance_tests"][0]["scenario"]["examples"] = ["不正"]
        failures = system_traceability_gate.validate(data, user_stories(), requirements())
        self.assertTrue(any("scenario.examples" in failure and "オブジェクト" in failure for failure in failures))

    def test_scenario_examples_with_mismatched_keys_is_rejected(self):
        data = complete_system_traceability()
        data["acceptance_tests"][0]["scenario"]["examples"] = [{"a": "1"}, {"b": "2"}]
        failures = system_traceability_gate.validate(data, user_stories(), requirements())
        self.assertTrue(any("scenario.examples の各行はキーを揃えて" in failure for failure in failures))

    def test_scenario_examples_with_consistent_keys_passes(self):
        data = complete_system_traceability()
        data["acceptance_tests"][0]["scenario"]["examples"] = [{"a": "1"}, {"a": "2"}]
        failures = system_traceability_gate.validate(data, user_stories(), requirements())
        self.assertEqual(failures, [])

    def test_deferred_requirement_referencing_undefined_flow_step_is_not_rejected(self):
        """deferredの要件はflow_step_idsの実在確認の対象外（移植元のvalidate_statusガードと同じ）。

        移植時にこのガードが抜けると、まだ存在しない業務フロー手順を参照しているだけで
        deferred要件が不通過になってしまう（偽陽性）。
        """
        reqs = requirements()
        reqs["FR-002"] = {
            "id": "FR-002", "status": "deferred", "type": "functional",
            "statement": "将来対応の要件", "reason": "今回は対象外",
            "user_story_ids": ["US-001"], "flow_step_ids": ["BF-999-S99"],
        }
        failures = system_traceability_gate.validate(complete_system_traceability(), user_stories(), reqs)
        self.assertFalse(any("BF-999-S99" in failure for failure in failures))

    def test_flow_step_covered_only_by_deferred_requirement_is_still_orphan(self):
        """業務フロー手順をdeferredの要件だけが参照している場合はカバーとしてカウントしない。

        カウントしてしまうと、本来出るべき「業務フロー手順が孤立しています」が
        抑制されてしまう（孤立検出の抜け穴）。
        """
        data = complete_system_traceability()
        data["business_flows"][0]["steps"].append(
            {"id": "BF-001-S02", "action": "空きを確認する", "user_story_ids": ["US-001"]}
        )
        reqs = requirements()
        reqs["FR-002"] = {
            "id": "FR-002", "status": "deferred", "type": "functional",
            "statement": "将来対応の要件", "reason": "今回は対象外",
            "user_story_ids": ["US-001"], "flow_step_ids": ["BF-001-S02"],
        }
        failures = system_traceability_gate.validate(data, user_stories(), reqs)
        self.assertTrue(
            any("BF-001-S02" in failure and "を満たす要件がありません" in failure for failure in failures)
        )


if __name__ == "__main__":
    unittest.main()
