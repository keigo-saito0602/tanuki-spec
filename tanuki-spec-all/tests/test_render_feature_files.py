from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evaluation"))
sys.path.insert(0, str(ROOT / "tests"))
import render_feature_files
from test_system_traceability_gate import complete_system_traceability


class RenderFeatureFilesTest(unittest.TestCase):
    def test_groups_by_feature_with_tags_and_steps(self):
        outputs = render_feature_files.render_all(complete_system_traceability())
        self.assertEqual(list(outputs), ["予約.feature"])
        content = outputs["予約.feature"]
        self.assertIn("Feature: 予約", content)
        self.assertIn("@AC-001 @US-001 @FR-001", content)
        self.assertIn("  Scenario: 予約確定", content)
        self.assertIn("    Given 予約データがある", content)
        self.assertIn("    When 確定ボタンを押す", content)

    def test_multiple_given_uses_and(self):
        data = complete_system_traceability()
        data["acceptance_tests"][0]["scenario"]["given"] = ["前提A", "前提B"]
        content = render_feature_files.render_all(data)["予約.feature"]
        self.assertIn("    Given 前提A\n    And 前提B", content)

    def test_examples_produce_scenario_outline(self):
        data = complete_system_traceability()
        data["acceptance_tests"][0]["scenario"]["examples"] = [
            {"枠状態": "空き", "結果": "予約確定"},
            {"枠状態": "満席", "結果": "満席エラー"},
        ]
        content = render_feature_files.render_all(data)["予約.feature"]
        self.assertIn("  Scenario Outline: 予約確定", content)
        self.assertIn("    Examples:", content)
        self.assertIn("      | 枠状態 | 結果 |", content)
        self.assertIn("      | 空き | 予約確定 |", content)

    def test_deferred_acceptance_is_excluded(self):
        data = complete_system_traceability()
        data["acceptance_tests"][0]["status"] = "deferred"
        data["acceptance_tests"][0]["reason"] = "次期対応"
        outputs = render_feature_files.render_all(data)
        self.assertNotIn("予約.feature", outputs)

    def test_feature_falls_back_to_user_story_then_default(self):
        data = complete_system_traceability()
        del data["acceptance_tests"][0]["feature"]
        self.assertIn("US-001.feature", render_feature_files.render_all(data))
        data["acceptance_tests"][0]["user_story_ids"] = []
        self.assertIn("受入シナリオ.feature", render_feature_files.render_all(data))


class RenderFeatureFilesCLITest(unittest.TestCase):
    def test_main_reads_system_traceability_and_writes_feature_files(self):
        import subprocess
        import sys
        import tempfile

        with tempfile.TemporaryDirectory() as directory_str:
            root = Path(directory_str)
            func_dir = root / "func-予約"
            func_dir.mkdir(parents=True, exist_ok=True)
            (func_dir / "traceability.yaml").write_text(
                """
version: "1.0"
user_stories:
  - id: US-001
    status: in_scope
    statement: "利用者は予約したい。なぜなら講座を受けたいから。"
requirements:
  - id: FR-001
    status: in_scope
    type: functional
    statement: "利用者は予約を確定できる"
    user_story_ids: [US-001]
    flow_step_ids: [BF-001-S01]
""",
                encoding="utf-8",
            )
            system_path = root / "system-traceability.yaml"
            system_path.write_text(
                """
version: "1.0"
func_traceability:
  - func-予約/traceability.yaml
business_flows:
  - id: BF-001
    status: in_scope
    name: "予約フロー"
    steps:
      - id: BF-001-S01
        action: "予約画面を開く"
        user_story_ids: [US-001]
acceptance_tests:
  - id: AC-001
    status: in_scope
    feature: "予約"
    user_story_ids: [US-001]
    requirement_ids: [FR-001]
    flow_step_ids: [BF-001-S01]
    scenario:
      name: "予約確定"
      given: ["予約データがある"]
      when: ["確定ボタンを押す"]
      then: ["予約が確定する"]
system_tests:
  - id: ST-001
    status: in_scope
    test_type: functional
    requirement_ids: [FR-001]
    acceptance_test_ids: [AC-001]
    preconditions: ["APIが起動している"]
    steps: ["POST /reservations"]
    expected_results: ["200が返る"]
""",
                encoding="utf-8",
            )
            output_dir = root / "features"

            result = subprocess.run(
                [sys.executable, str(ROOT / "evaluation" / "render_feature_files.py"), str(system_path), "--output-dir", str(output_dir)],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            generated = list(output_dir.glob("*.feature"))
            self.assertEqual(len(generated), 1)
            self.assertIn("AC-001", generated[0].read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
