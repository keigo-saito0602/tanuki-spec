from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evaluation"))
sys.path.insert(0, str(ROOT / "tests"))
import render_feature_files
from test_requirements_traceability_gate import complete_traceability


class RenderFeatureFilesTest(unittest.TestCase):
    def test_groups_by_feature_with_tags_and_steps(self):
        outputs = render_feature_files.render_all(complete_traceability())
        self.assertEqual(list(outputs), ["レッスン予約.feature"])
        content = outputs["レッスン予約.feature"]
        self.assertIn("Feature: レッスン予約", content)
        self.assertIn("@AC-001 @US-001 @BR-001", content)
        self.assertIn("  Scenario: 予約シナリオ1", content)
        self.assertIn("    Given 生徒がログイン済みである", content)
        self.assertIn("    When 生徒が予約を確定する", content)

    def test_multiple_given_uses_and(self):
        data = complete_traceability()
        data["acceptance_tests"][0]["scenario"]["given"] = ["前提A", "前提B"]
        content = render_feature_files.render_all(data)["レッスン予約.feature"]
        self.assertIn("    Given 前提A\n    And 前提B", content)

    def test_examples_produce_scenario_outline(self):
        data = complete_traceability()
        data["acceptance_tests"][0]["scenario"]["examples"] = [
            {"枠状態": "空き", "結果": "予約確定"},
            {"枠状態": "満席", "結果": "満席エラー"},
        ]
        content = render_feature_files.render_all(data)["レッスン予約.feature"]
        self.assertIn("  Scenario Outline: 予約シナリオ1", content)
        self.assertIn("    Examples:", content)
        self.assertIn("      | 枠状態 | 結果 |", content)
        self.assertIn("      | 空き | 予約確定 |", content)

    def test_deferred_acceptance_is_excluded(self):
        data = complete_traceability()
        data["acceptance_tests"][0]["status"] = "deferred"
        data["acceptance_tests"][0]["reason"] = "次期対応"
        content = render_feature_files.render_all(data)["レッスン予約.feature"]
        self.assertNotIn("AC-001", content)

    def test_feature_falls_back_to_user_story_then_default(self):
        data = complete_traceability()
        del data["acceptance_tests"][0]["feature"]
        self.assertIn("US-001.feature", render_feature_files.render_all(data))
        data["acceptance_tests"][0]["user_story_ids"] = []
        self.assertIn("受入シナリオ.feature", render_feature_files.render_all(data))


if __name__ == "__main__":
    unittest.main()
