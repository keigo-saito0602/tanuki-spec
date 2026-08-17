from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

from evaluation.cc_sdd_bridge import (
    BridgeError,
    OWNER_MARKER,
    check,
    render,
    resolve_inputs,
)


class CcSddBridgeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.phase = self.root / "docs/spec/phase-1_demo"
        self.func = self.phase / "func-demo"
        self.func.mkdir(parents=True)
        self._write_sources()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _write_sources(self, requirements: list[dict] | None = None, design_ids: list[str] | None = None) -> None:
        requirements = requirements or [
            {"id": "FR-001", "status": "in_scope", "statement": "利用者が登録できる"},
            {"id": "NFR-001", "status": "draft", "statement": "安全に処理する"},
            {"id": "FR-002", "status": "deferred", "statement": "将来連携する", "reason": "次期対応"},
            {"id": "FR-003", "status": "out_of_scope", "statement": "対象外機能", "reason": "今回対象外"},
        ]
        design_ids = design_ids or ["FR-001", "NFR-001"]
        (self.func / "traceability.yaml").write_text(
            yaml.safe_dump({"version": "1.0", "requirements": requirements}, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        (self.func / "design-traceability.yaml").write_text(
            yaml.safe_dump(
                {"version": "1.0", "requirements_traceability": "traceability.yaml", "design_elements": [
                    {"id": "BD-001", "type": "basic_design", "name": "登録境界", "requirement_ids": design_ids}
                ]},
                allow_unicode=True,
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        for name in ("00_サマリ.md", "01_要件定義書.md", "02_基本設計書.md", "03_詳細設計書.md"):
            (self.func / name).write_text(f"# {name}\n\n- 要点 {name}\n", encoding="utf-8")

    def _inputs(self, spec: str = "demo"):
        return resolve_inputs(self.root, "docs/spec/phase-1_demo", "demo", spec)

    def test_render_creates_thin_cards_and_numeric_requirement_ids(self) -> None:
        paths = render(self._inputs())
        self.assertEqual([path.name for path in paths], ["spec.json", "requirements.md", "design.md"])
        requirements = (self._inputs().spec_dir / "requirements.md").read_text(encoding="utf-8")
        self.assertIn("Requirement 1: [FR-001]", requirements)
        self.assertIn("Requirement 2: [NFR-001]", requirements)
        self.assertNotIn("Requirement 3: [FR-002]", requirements)
        self.assertIn("FR-002", requirements)
        self.assertIn("01_要件定義書.md", requirements)
        self.assertIn("タスク生成前の必須読込", requirements)
        self.assertIn("traceability.yaml", requirements)
        self.assertIn("このカードの要点だけでタスクを生成してはいけません", requirements)
        design = (self._inputs().spec_dir / "design.md").read_text(encoding="utf-8")
        self.assertIn("requirement_ids: [1, 2]", design)
        self.assertIn("Requirement 1 [FR-001]", design)
        self.assertIn("02_基本設計書.md", design)
        self.assertIn("design-traceability.yaml", design)
        self.assertIn("03_詳細設計書.md", design)
        self.assertIn("このカードの要点だけでタスクを生成してはいけません", design)

    def test_regeneration_is_stable_and_approve_is_explicit(self) -> None:
        inputs = self._inputs()
        render(inputs)
        first = {name: (inputs.spec_dir / name).read_text(encoding="utf-8") for name in ("spec.json", "requirements.md", "design.md")}
        render(inputs)
        second = {name: (inputs.spec_dir / name).read_text(encoding="utf-8") for name in first}
        self.assertEqual(first, second)
        metadata = json.loads(first["spec.json"])
        self.assertFalse(metadata["approvals"]["requirements"]["approved"])
        self.assertEqual(metadata["feature_name"], "demo")
        with self.assertRaisesRegex(BridgeError, "draft要件"):
            render(inputs, approved=True)
        requirements = yaml.safe_load((self.func / "traceability.yaml").read_text(encoding="utf-8"))["requirements"]
        requirements[1]["status"] = "in_scope"
        self._write_sources(requirements=requirements)
        render(inputs, approved=True)
        approved = json.loads((inputs.spec_dir / "spec.json").read_text(encoding="utf-8"))
        self.assertTrue(approved["approvals"]["requirements"]["approved"])
        self.assertTrue(approved["approvals"]["design"]["approved"])
        self.assertFalse(approved["approvals"]["tasks"]["generated"])

    def test_check_detects_diff_and_passes_after_render(self) -> None:
        inputs = self._inputs()
        self.assertEqual(
            check(inputs),
            ["spec.json がありません", "requirements.md がありません", "design.md がありません"],
        )
        render(inputs)
        self.assertEqual(check(inputs), [])
        (inputs.spec_dir / "requirements.md").write_text("changed\n", encoding="utf-8")
        self.assertEqual(check(inputs), ["requirements.md が最新のtanuki入力と一致しません"])

    def test_check_allows_cc_sdd_managed_spec_fields_to_change(self) -> None:
        inputs = self._inputs()
        render(inputs)
        spec_path = inputs.spec_dir / "spec.json"
        metadata = json.loads(spec_path.read_text(encoding="utf-8"))

        metadata.update(
            {
                "name": "cc-sdd-renamed-feature",
                "created_at": "2026-08-17T10:00:00Z",
                "updated_at": "2026-08-17T11:00:00Z",
                "phase": "tasks",
                "ready_for_implementation": True,
            }
        )
        metadata["approvals"]["requirements"]["approved"] = True
        metadata["approvals"]["tasks"]["generated"] = True
        spec_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        self.assertEqual(check(inputs), [])

    def test_check_detects_bridge_owned_spec_fields_and_marker_corruption(self) -> None:
        inputs = self._inputs()
        render(inputs)
        spec_path = inputs.spec_dir / "spec.json"

        metadata = json.loads(spec_path.read_text(encoding="utf-8"))
        metadata["source"]["tanuki_root"] = "../別の正本"
        spec_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self.assertEqual(check(inputs), ["spec.json が最新のtanuki入力と一致しません"])

        render(inputs)
        metadata = json.loads(spec_path.read_text(encoding="utf-8"))
        metadata["bridge"]["requirement_count"] = 999
        spec_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self.assertEqual(check(inputs), ["spec.json が最新のtanuki入力と一致しません"])

        render(inputs)
        metadata = json.loads(spec_path.read_text(encoding="utf-8"))
        metadata["feature_name"] = "別の機能"
        metadata["language"] = "en"
        spec_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self.assertEqual(check(inputs), ["spec.json が最新のtanuki入力と一致しません"])

        render(inputs)
        metadata = json.loads(spec_path.read_text(encoding="utf-8"))
        metadata["generated_by"] = "not-the-bridge"
        spec_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(BridgeError, "所有マーカー"):
            check(inputs)

    def test_check_allows_tasks_and_preserves_them_when_cards_are_stale(self) -> None:
        inputs = self._inputs()
        render(inputs)
        tasks = inputs.spec_dir / "tasks.md"
        tasks.write_text("- [ ] 1. 既存タスク\n", encoding="utf-8")
        tasks_before = tasks.read_bytes()

        self.assertEqual(check(inputs), [])
        self.assertEqual(tasks.read_bytes(), tasks_before)

        requirements = yaml.safe_load(
            (self.func / "traceability.yaml").read_text(encoding="utf-8")
        )["requirements"]
        requirements[0]["statement"] = "利用者が安全に登録できる"
        self._write_sources(requirements=requirements)

        self.assertEqual(
            check(inputs),
            ["requirements.md が最新のtanuki入力と一致しません"],
        )
        self.assertEqual(tasks.read_bytes(), tasks_before)
        with self.assertRaisesRegex(BridgeError, "既存tasks.md"):
            render(inputs)
        self.assertEqual(tasks.read_bytes(), tasks_before)

    def test_existing_non_owned_directory_is_rejected(self) -> None:
        inputs = self._inputs()
        inputs.spec_dir.mkdir(parents=True)
        (inputs.spec_dir / "spec.json").write_text('{"name":"handwritten"}\n', encoding="utf-8")
        with self.assertRaises(BridgeError):
            render(inputs)

    def test_existing_tasks_is_rejected_even_when_owned(self) -> None:
        inputs = self._inputs()
        render(inputs)
        (inputs.spec_dir / "tasks.md").write_text("manual\n", encoding="utf-8")
        with self.assertRaises(BridgeError):
            render(inputs)

    @unittest.skipIf(sys.platform == "win32", "Windowsではsymlink作成権限が別途必要")
    def test_symlink_output_directory_and_files_are_rejected(self) -> None:
        inputs = self._inputs("symlink-dir")
        real = self.root / "real-spec"
        real.mkdir()
        inputs.spec_dir.parent.mkdir(parents=True, exist_ok=True)
        inputs.spec_dir.symlink_to(real, target_is_directory=True)
        with self.assertRaises(BridgeError):
            render(inputs)

        inputs = self._inputs("symlink-file")
        render(inputs)
        target = self.root / "outside.md"
        target.write_text("outside", encoding="utf-8")
        output = inputs.spec_dir / "design.md"
        output.unlink()
        output.symlink_to(target)
        with self.assertRaises(BridgeError):
            render(inputs)

    def test_requirement_id_order_is_stable_and_unknown_design_id_fails(self) -> None:
        inputs = self._inputs()
        render(inputs)
        self._write_sources(design_ids=["UNKNOWN"])
        with self.assertRaises(BridgeError):
            render(inputs)

    def test_no_active_requirement_is_rejected(self) -> None:
        self._write_sources(
            requirements=[
                {"id": "FR-001", "status": "out_of_scope", "statement": "対象外", "reason": "別案件"}
            ],
            design_ids=["FR-001"],
        )
        with self.assertRaisesRegex(BridgeError, "in_scope/draft"):
            render(self._inputs())

    def test_inputs_must_resolve_inside_phase_and_func(self) -> None:
        with self.assertRaises(BridgeError):
            resolve_inputs(self.root, "docs/spec/phase-1_demo", "..", "escape")


if __name__ == "__main__":
    unittest.main()
