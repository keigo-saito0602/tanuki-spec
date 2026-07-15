from __future__ import annotations

import copy
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evaluation"))
import design_traceability_gate
import render_design_traceability_docs


def requirements() -> dict[str, dict]:
    return {
        "BR-001": {"id": "BR-001", "status": "in_scope", "type": "business", "statement": "予約業務を標準化する"},
        "FR-001": {"id": "FR-001", "status": "in_scope", "type": "functional", "statement": "利用者は予約を確定できる"},
        "NFR-001": {"id": "NFR-001", "status": "in_scope", "type": "non_functional", "statement": "予約は5秒以内に完了する"},
    }


def complete_design_traceability() -> dict:
    return {
        "version": "1.0",
        "design_elements": [
            {"id": "BD-001", "type": "basic_design", "name": "予約画面とAPIの外部仕様", "requirement_ids": ["BR-001", "FR-001"]},
            {"id": "DD-001", "type": "detailed_design", "name": "予約確定処理と性能制御", "requirement_ids": ["NFR-001"]},
        ],
    }


class DesignTraceabilityGateTest(unittest.TestCase):
    def test_complete_design_coverage_passes(self):
        self.assertEqual(design_traceability_gate.validate(complete_design_traceability(), requirements()), [])

    def test_uncovered_in_scope_requirement_is_rejected(self):
        data = complete_design_traceability()
        data["design_elements"][1]["requirement_ids"] = []
        failures = design_traceability_gate.validate(data, requirements())
        self.assertTrue(any("要件が設計で被覆されていません: NFR-001" in failure for failure in failures))

    def test_unknown_requirement_reference_is_rejected(self):
        data = complete_design_traceability()
        data["design_elements"][0]["requirement_ids"] = ["FR-999"]
        failures = design_traceability_gate.validate(data, requirements())
        self.assertTrue(any("参照先の要件が存在しません: FR-999" in failure for failure in failures))

    def test_element_id_must_match_its_design_phase(self):
        data = copy.deepcopy(complete_design_traceability())
        data["design_elements"][0]["id"] = "DD-001"
        failures = design_traceability_gate.validate(data, requirements())
        self.assertTrue(any("basic_design のID形式が不正" in failure for failure in failures))

    def test_renderer_includes_requirement_and_design_element_ids(self):
        rendered = render_design_traceability_docs.render(complete_design_traceability(), requirements())
        self.assertIn("FR-001", rendered)
        self.assertIn("BD-001", rendered)
        self.assertIn("DD-001", rendered)
