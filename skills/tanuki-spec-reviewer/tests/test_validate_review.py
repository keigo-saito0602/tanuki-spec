from __future__ import annotations

import hashlib
import sys
import tempfile
from pathlib import Path
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
TRACEABILITY = ROOT.parent / "tanuki-spec-generator" / "examples" / "sample-user-story" / "traceability.yaml"
DESIGN_TRACEABILITY = ROOT.parent / "tanuki-spec-design" / "examples" / "sample-user-story" / "design-traceability.yaml"
sys.path.insert(0, str(ROOT / "evaluation"))
import coverage
import validate_review


class ValidateReviewTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = yaml.safe_load((ROOT / "spec-items.yaml").read_text(encoding="utf-8"))

    def make_spec(self) -> Path:
        parts = [
            "---",
            "template: requirements",
            f"spec_items_version: \"{self.data['meta']['version']}\"",
            "---",
        ]
        for _, _, item in coverage.iter_items(self.data, "requirements"):
            parts.append(
                f"<!-- FILL:START {item['id']} -->\n"
                "確認済みの内容です。\n"
                f"<!-- FILL:END {item['id']} -->"
            )
        handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md", delete=False)
        handle.write("\n".join(parts))
        handle.close()
        return Path(handle.name)

    def make_review(self, spec: Path) -> dict:
        document = spec.read_text(encoding="utf-8")
        results = coverage.evaluate(document, self.data, "requirements")
        summary = coverage.summarize(results)["overall"]
        return {
            "ai_quality_review": {
                "date": "2026-07-14",
                "target": "requirements",
                "reviewer": {"role": "reviewer", "model": "test-model", "independent": True},
                "generated_spec_sha256": hashlib.sha256(spec.read_bytes()).hexdigest(),
                "traceability_sha256": hashlib.sha256(TRACEABILITY.read_bytes()).hexdigest(),
                "traceability_gate_passed": True,
                "coverage": {
                    "required_coverage": summary["required_coverage"],
                    "overall_coverage": summary["coverage"],
                    "todo_flags": summary["confirmation_needed"],
                },
                "rubric": {axis: "PASS" for axis in validate_review.RUBRIC_AXES},
                "dod_passed": False,
            }
        }

    def test_current_review_format_is_valid_when_master_is_pending(self):
        spec = self.make_spec()
        self.addCleanup(spec.unlink)
        self.assertEqual(validate_review.validate(self.make_review(spec), spec, TRACEABILITY), [])

    def test_sha256_mismatch_is_rejected(self):
        spec = self.make_spec()
        self.addCleanup(spec.unlink)
        review = self.make_review(spec)
        review["ai_quality_review"]["generated_spec_sha256"] = "0" * 64
        errors = validate_review.validate(review, spec, TRACEABILITY)
        self.assertTrue(any("generated_spec_sha256" in error for error in errors))

    def test_traceability_sha256_mismatch_is_rejected(self):
        spec = self.make_spec()
        self.addCleanup(spec.unlink)
        review = self.make_review(spec)
        review["ai_quality_review"]["traceability_sha256"] = "0" * 64
        errors = validate_review.validate(review, spec, TRACEABILITY)
        self.assertTrue(any("traceability_sha256" in error for error in errors))

    def test_design_review_requires_design_traceability(self):
        spec = self.make_spec()
        self.addCleanup(spec.unlink)
        review = self.make_review(spec)
        review["ai_quality_review"]["target"] = "basic_design"
        errors = validate_review.validate(review, spec, TRACEABILITY)
        self.assertTrue(any("設計工程の必須項目不足" in error for error in errors))
        self.assertTrue(any("--design-traceability" in error for error in errors))

    def test_design_traceability_sha256_mismatch_is_rejected(self):
        spec = self.make_spec()
        self.addCleanup(spec.unlink)
        review = self.make_review(spec)
        entry = review["ai_quality_review"]
        entry["target"] = "basic_design"
        entry["design_traceability_sha256"] = "0" * 64
        entry["design_traceability_gate_passed"] = True
        errors = validate_review.validate(review, spec, TRACEABILITY, DESIGN_TRACEABILITY)
        self.assertTrue(any("design_traceability_sha256" in error for error in errors))

    def test_evaluation_item_without_reason_is_rejected(self):
        spec = self.make_spec()
        self.addCleanup(spec.unlink)
        review = self.make_review(spec)
        review["ai_quality_review"]["evaluation"] = {
            "item_results": [{"id": "SEC-001", "status": "not_evaluable", "importance": "required", "evidence": []}]
        }
        errors = validate_review.validate(review, spec, TRACEABILITY)
        self.assertTrue(any("reason と recommended_action" in error for error in errors))
