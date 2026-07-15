from __future__ import annotations

import sys
from pathlib import Path
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evaluation"))
import coverage
import spec_gate


class SpecGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = yaml.safe_load((ROOT / "spec-items.yaml").read_text(encoding="utf-8"))

    def complete_requirements_document(self, with_evidence: bool) -> str:
        parts = ["---", "template: requirements", "---"]
        for _, _, item in coverage.iter_items(self.data, "requirements"):
            body = "確認済みの内容です。"
            if with_evidence:
                body = "- **根拠**: [入力] ユーザーストーリー「確認済み」\n" + body
            parts.append(f"<!-- FILL:START {item['id']} -->\n{body}\n<!-- FILL:END {item['id']} -->")
        return "\n".join(parts)

    def test_complete_document_passes_coverage_and_evidence_gate(self):
        document = self.complete_requirements_document(with_evidence=True)
        results = coverage.evaluate(document, self.data, "requirements")
        self.assertEqual(coverage.gate_failures(results), [])
        self.assertEqual(spec_gate.evidence_failures(document, results), [])

    def test_missing_evidence_is_detected(self):
        document = self.complete_requirements_document(with_evidence=False)
        results = coverage.evaluate(document, self.data, "requirements")
        self.assertGreater(len(spec_gate.evidence_failures(document, results)), 0)

    def test_marker_missing_is_not_reported_twice(self):
        results = coverage.evaluate("", self.data, "requirements")
        failures = spec_gate.actionable_gate_failures(results)
        self.assertFalse(any(failure.startswith("必須未充足:") for failure in failures))
