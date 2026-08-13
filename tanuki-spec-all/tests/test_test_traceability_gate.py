from __future__ import annotations

import copy
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evaluation"))
import test_traceability_gate
import render_test_item_docs


def design_elements() -> dict[str, dict]:
    return {
        "BD-001": {"id": "BD-001", "type": "basic_design", "name": "予約APIの外部仕様", "requirement_ids": ["FR-001", "NFR-001"]},
        "DD-001": {"id": "DD-001", "type": "detailed_design", "name": "予約確定処理の内部ロジック", "requirement_ids": ["FR-001"]},
    }


def complete_test_traceability() -> dict:
    return {
        "version": "1.0",
        "test_items": [
            {
                "id": "UT-001",
                "status": "in_scope",
                "test_type": "unit",
                "design_element_ids": ["DD-001"],
                "requirement_ids": ["FR-001"],
                "preconditions": ["予約データが存在する"],
                "steps": ["予約確定処理を呼び出す"],
                "expected_results": ["予約が確定する"],
            },
            {
                "id": "IT-001",
                "status": "in_scope",
                "test_type": "integration",
                "design_element_ids": ["BD-001"],
                "requirement_ids": ["FR-001", "NFR-001"],
                "preconditions": ["APIサーバが起動している"],
                "steps": ["予約APIを呼び出す"],
                "expected_results": ["200が返る"],
            },
        ],
    }


class TestTraceabilityGateTest(unittest.TestCase):
    def test_complete_coverage_passes(self):
        self.assertEqual(test_traceability_gate.validate(complete_test_traceability(), design_elements()), [])

    def test_unknown_design_element_reference_is_rejected(self):
        data = complete_test_traceability()
        data["test_items"][0]["design_element_ids"] = ["DD-999"]
        failures = test_traceability_gate.validate(data, design_elements())
        self.assertTrue(any("参照先の設計要素が存在しません: DD-999" in failure for failure in failures))

    def test_unit_test_linked_to_basic_design_is_rejected(self):
        """UTはDDに紐づける。BDへ紐づけるのは種別違反。"""
        data = complete_test_traceability()
        data["test_items"][0]["design_element_ids"] = ["BD-001"]
        failures = test_traceability_gate.validate(data, design_elements())
        self.assertTrue(any("unit は detailed_design の設計要素に紐づけてください" in failure for failure in failures))

    def test_integration_test_linked_to_detailed_design_is_rejected(self):
        """ITはBDに紐づける。DDへ紐づけるのは種別違反。"""
        data = complete_test_traceability()
        data["test_items"][1]["design_element_ids"] = ["DD-001"]
        failures = test_traceability_gate.validate(data, design_elements())
        self.assertTrue(any("integration は basic_design の設計要素に紐づけてください" in failure for failure in failures))

    def test_requirement_id_outside_design_element_scope_is_rejected(self):
        """requirement_idsは紐づく設計要素のrequirement_idsの部分集合でなければならない。"""
        data = complete_test_traceability()
        data["test_items"][0]["requirement_ids"] = ["FR-001", "NFR-001"]  # DD-001はFR-001のみ持つ
        failures = test_traceability_gate.validate(data, design_elements())
        self.assertTrue(any("紐づく設計要素の対象外の要件が含まれています: NFR-001" in failure for failure in failures))

    def test_id_must_match_its_test_type(self):
        data = copy.deepcopy(complete_test_traceability())
        data["test_items"][0]["id"] = "IT-001"
        failures = test_traceability_gate.validate(data, design_elements())
        self.assertTrue(any("unit のID形式が不正です" in failure for failure in failures))

    def test_duplicate_id_is_rejected(self):
        data = complete_test_traceability()
        data["test_items"][1]["id"] = "UT-001"
        data["test_items"][1]["test_type"] = "unit"
        data["test_items"][1]["design_element_ids"] = ["DD-001"]
        failures = test_traceability_gate.validate(data, design_elements())
        self.assertTrue(any("IDが重複しています" in failure for failure in failures))

    def test_uncovered_detailed_design_element_is_rejected(self):
        data = complete_test_traceability()
        data["test_items"] = [data["test_items"][1]]  # UTを消してDD-001を未被覆にする
        failures = test_traceability_gate.validate(data, design_elements())
        self.assertTrue(any("設計要素がテストで被覆されていません: DD-001" in failure for failure in failures))

    def test_uncovered_basic_design_element_is_rejected(self):
        data = complete_test_traceability()
        data["test_items"] = [data["test_items"][0]]  # ITを消してBD-001を未被覆にする
        failures = test_traceability_gate.validate(data, design_elements())
        self.assertTrue(any("設計要素がテストで被覆されていません: BD-001" in failure for failure in failures))

    def test_deferred_item_requires_reason(self):
        data = complete_test_traceability()
        data["test_items"][0]["status"] = "deferred"
        failures = test_traceability_gate.validate(data, design_elements())
        self.assertTrue(any("deferred には reason が必要です" in failure for failure in failures))

    def test_renderer_includes_unit_and_integration_sections(self):
        rendered = render_test_item_docs.render(complete_test_traceability(), design_elements(), {})
        self.assertIn("## 単体テスト（UT）", rendered)
        self.assertIn("## 結合テスト（IT）", rendered)
        self.assertIn("## V字モデルカバレッジ", rendered)
        self.assertIn("UT-001", rendered)
        self.assertIn("IT-001", rendered)
        self.assertIn("DD-001", rendered)
        self.assertIn("BD-001", rendered)

    def test_renderer_shows_related_acceptance_and_system_tests(self):
        ac_st_by_requirement = {
            "FR-001": {"acceptance_test_ids": ["AC-001"], "system_test_ids": ["ST-001"]},
        }
        rendered = render_test_item_docs.render(complete_test_traceability(), design_elements(), ac_st_by_requirement)
        self.assertIn("AC-001", rendered)
        self.assertIn("ST-001", rendered)


TRACEABILITY_YAML = """
version: "1.0"
user_stories:
  - id: US-001
    status: in_scope
    statement: "利用者は予約をしたい。なぜなら講座を受けたいから。"
requirements:
  - id: FR-001
    status: in_scope
    type: functional
    statement: "利用者は予約を確定できる"
    user_story_ids: [US-001]
    flow_step_ids: [BF-001-S01]
"""

DESIGN_TRACEABILITY_YAML_VALID = """
version: "1.0"
requirements_traceability: traceability.yaml
design_elements:
  - id: BD-001
    type: basic_design
    name: "予約APIの外部仕様"
    requirement_ids: [FR-001]
  - id: DD-001
    type: detailed_design
    name: "予約確定処理の内部ロジック"
    requirement_ids: [FR-001]
"""

# FR-999は traceability.yaml のどこにも存在しない要件IDである。
DESIGN_TRACEABILITY_YAML_DANGLING = """
version: "1.0"
requirements_traceability: traceability.yaml
design_elements:
  - id: BD-001
    type: basic_design
    name: "予約APIの外部仕様"
    requirement_ids: [FR-999]
  - id: DD-001
    type: detailed_design
    name: "予約確定処理の内部ロジック"
    requirement_ids: [FR-999]
"""

TEST_TRACEABILITY_YAML = """
version: "1.0"
design_traceability: design-traceability.yaml
test_items:
  - id: UT-001
    status: in_scope
    test_type: unit
    design_element_ids: [DD-001]
    requirement_ids: [FR-999]
    preconditions: ["p"]
    steps: ["s"]
    expected_results: ["r"]
  - id: IT-001
    status: in_scope
    test_type: integration
    design_element_ids: [BD-001]
    requirement_ids: [FR-999]
    preconditions: ["p"]
    steps: ["s"]
    expected_results: ["r"]
"""


class FullChainValidationTest(unittest.TestCase):
    """UT/ITから設計要素だけでなく、要件正本（traceability.yaml）までの鎖を検証する。"""

    def _write(self, directory: Path, design_traceability_yaml: str) -> Path:
        (directory / "traceability.yaml").write_text(TRACEABILITY_YAML, encoding="utf-8")
        (directory / "design-traceability.yaml").write_text(design_traceability_yaml, encoding="utf-8")
        test_traceability_path = directory / "test-traceability.yaml"
        test_traceability_path.write_text(TEST_TRACEABILITY_YAML, encoding="utf-8")
        return test_traceability_path

    def test_design_element_referencing_nonexistent_requirement_is_rejected(self):
        """DD-001/BD-001がFR-999（traceability.yamlに存在しない）を参照している場合は不通過にする。"""
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            path = self._write(Path(directory), DESIGN_TRACEABILITY_YAML_DANGLING)
            data = test_traceability_gate.load(path)
            elements, failures = test_traceability_gate.full_design_element_index(path, data)
            self.assertTrue(
                any("FR-999" in failure for failure in failures),
                msg=f"FR-999への参照が不正として検出されるべきです: {failures}",
            )

    def test_valid_chain_passes(self):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            path = self._write(Path(directory), DESIGN_TRACEABILITY_YAML_VALID)
            # DESIGN_TRACEABILITY_YAML_VALID は FR-001 を参照するが、TEST_TRACEABILITY_YAML は
            # FR-999 を参照しているため、この組み合わせでは test_items 側のrequirement_ids検査で落ちる。
            # ここでは design 層の鎖だけが正しく通ることを確認する。
            data = test_traceability_gate.load(path)
            elements, failures = test_traceability_gate.full_design_element_index(path, data)
            self.assertEqual(failures, [])
            self.assertIn("BD-001", elements)
            self.assertIn("DD-001", elements)


SYSTEM_TRACEABILITY_YAML = """
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
"""


class SystemTraceabilityFieldTest(unittest.TestCase):
    """test-traceability.yamlのsystem_traceabilityフィールドの検証。"""

    def _write_valid_chain(self, directory: Path) -> Path:
        func_dir = directory / "func-予約"
        func_dir.mkdir(parents=True, exist_ok=True)
        (directory / "traceability.yaml").write_text(TRACEABILITY_YAML, encoding="utf-8")
        (func_dir / "traceability.yaml").write_text(TRACEABILITY_YAML, encoding="utf-8")
        (directory / "design-traceability.yaml").write_text(DESIGN_TRACEABILITY_YAML_VALID, encoding="utf-8")
        (directory / "system-traceability.yaml").write_text(SYSTEM_TRACEABILITY_YAML, encoding="utf-8")
        test_traceability_path = func_dir / "test-traceability.yaml"
        content = TEST_TRACEABILITY_YAML.replace(
            'design_traceability: design-traceability.yaml',
            'design_traceability: ../design-traceability.yaml\nsystem_traceability: ../system-traceability.yaml',
        ).replace("[FR-999]", "[FR-001]")
        test_traceability_path.write_text(content, encoding="utf-8")
        return test_traceability_path

    def test_missing_system_traceability_field_is_rejected(self):
        import tempfile

        with tempfile.TemporaryDirectory() as directory_str:
            path = self._write_valid_chain(Path(directory_str))
            data = test_traceability_gate.load(path)
            del data["system_traceability"]
            failures = test_traceability_gate.validate_system_traceability(path, data, {"FR-001"})
            self.assertTrue(any("system_traceability" in failure for failure in failures))

    def test_system_traceability_pointing_to_missing_file_is_rejected(self):
        import tempfile

        with tempfile.TemporaryDirectory() as directory_str:
            path = self._write_valid_chain(Path(directory_str))
            data = test_traceability_gate.load(path)
            data["system_traceability"] = "../does-not-exist.yaml"
            failures = test_traceability_gate.validate_system_traceability(path, data, {"FR-001"})
            self.assertTrue(any("存在しません" in failure or "読み込めません" in failure for failure in failures))

    def test_system_traceability_in_different_phase_is_rejected(self):
        """解決先が対象test-traceability.yamlと同じphase直下でなければ拒否する。"""
        import tempfile

        with tempfile.TemporaryDirectory() as directory_str:
            root = Path(directory_str)
            path = self._write_valid_chain(root)
            other_phase = root.parent / (root.name + "-other")
            other_phase.mkdir(parents=True, exist_ok=True)
            (other_phase / "system-traceability.yaml").write_text(SYSTEM_TRACEABILITY_YAML, encoding="utf-8")
            data = test_traceability_gate.load(path)
            data["system_traceability"] = "../../" + other_phase.name + "/system-traceability.yaml"
            failures = test_traceability_gate.validate_system_traceability(path, data, {"FR-001"})
            self.assertTrue(any("同じphase" in failure for failure in failures))

    def test_system_traceability_not_registering_this_func_is_rejected(self):
        """system-traceability.yaml側のfunc_traceabilityに対象funcが登録されていなければ拒否する。"""
        import tempfile

        with tempfile.TemporaryDirectory() as directory_str:
            path = self._write_valid_chain(Path(directory_str))
            system_path = path.parent.parent / "system-traceability.yaml"
            system_data = test_traceability_gate.load(system_path)
            system_data["func_traceability"] = ["func-別の機能/traceability.yaml"]
            system_path.write_text(__import__("yaml").safe_dump(system_data, allow_unicode=True), encoding="utf-8")
            data = test_traceability_gate.load(path)
            failures = test_traceability_gate.validate_system_traceability(path, data, {"FR-001"})
            self.assertTrue(any("登録されていません" in failure for failure in failures))

    def test_system_traceability_gate_failure_is_rejected(self):
        """③ 参照先ファイルは存在し・同じphase・func登録済みだが、system-traceability.yaml
        自体の中身がsystem_traceability_gate.validate()を通過しない場合は拒否する。

        業務フロー手順BF-001-S01のuser_story_idsを存在しないUS-999に壊し、
        他の条件（①②⑤⑥）は満たしたまま③だけを不通過にする。
        """
        import tempfile

        with tempfile.TemporaryDirectory() as directory_str:
            path = self._write_valid_chain(Path(directory_str))
            system_path = path.parent.parent / "system-traceability.yaml"
            broken_system_yaml = SYSTEM_TRACEABILITY_YAML.replace(
                "        user_story_ids: [US-001]",
                "        user_story_ids: [US-999]",
            )
            self.assertNotEqual(broken_system_yaml, SYSTEM_TRACEABILITY_YAML)
            system_path.write_text(broken_system_yaml, encoding="utf-8")
            data = test_traceability_gate.load(path)
            failures = test_traceability_gate.validate_system_traceability(path, data, {"FR-001"})
            self.assertTrue(any("通過していません" in failure for failure in failures))

    def test_unresolvable_requirement_id_is_rejected(self):
        """対象funcの要件IDがsystem-traceability.yaml側の要件索引で解決できることを検証する。"""
        import tempfile

        with tempfile.TemporaryDirectory() as directory_str:
            path = self._write_valid_chain(Path(directory_str))
            data = test_traceability_gate.load(path)
            failures = test_traceability_gate.validate_system_traceability(path, data, {"FR-999-不在"})
            self.assertTrue(any("FR-999-不在" in failure for failure in failures))

    def test_valid_system_traceability_passes(self):
        import tempfile

        with tempfile.TemporaryDirectory() as directory_str:
            path = self._write_valid_chain(Path(directory_str))
            data = test_traceability_gate.load(path)
            failures = test_traceability_gate.validate_system_traceability(path, data, {"FR-001"})
            self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
