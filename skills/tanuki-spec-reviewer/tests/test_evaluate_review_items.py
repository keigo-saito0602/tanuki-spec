from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "evaluation"))
import evaluate_review_items
import render_quality_evaluation


class EvaluateReviewItemsTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.review_path = Path(self.directory.name) / "review.yaml"
        self.context_path = Path(self.directory.name) / "context.yaml"
        self.traceability = ROOT.parent / "tanuki-spec-generator" / "examples" / "sample-user-story" / "traceability.yaml"
        self.design = ROOT.parent / "tanuki-spec-design" / "examples" / "sample-user-story" / "design-traceability.yaml"
        self.rules = ROOT / "templates" / "review-rules.yaml"
        self.context_path.write_text(yaml.safe_dump({"review_context": {"workload_types": ["web_ui"], "data_classifications": [], "has_user_roles": True, "deployment_required": True}}, allow_unicode=True), encoding="utf-8")
        self.review_path.write_text(yaml.safe_dump({"ai_quality_review": {"target": "basic_design", "traceability_gate_passed": True, "design_traceability_gate_passed": True, "rubric": {"完全性": "PASS", "曖昧性の排除": "PASS", "整合性": "PASS", "トレーサビリティ": "PASS", "実装可能性": "PASS", "根拠_非ハルシネーション": "PASS"}, "coverage": {"required_coverage": 100, "overall_coverage": 100, "todo_flags": 0}, "reviewer": {"model": "test", "independent": True}, "date": "2026-07-16", "generated_spec_sha256": "0" * 64, "traceability_sha256": "0" * 64, "dod_passed": False}}, allow_unicode=True, sort_keys=False), encoding="utf-8")

    def test_skeleton_applies_only_matching_rules_and_preserves_existing_fields(self):
        evaluate_review_items.emit_skeleton(self.review_path, self.context_path, self.rules, False)
        review = evaluate_review_items.load(self.review_path)["ai_quality_review"]
        items = {item["id"]: item for item in review["evaluation"]["item_results"]}
        self.assertEqual(set(items), {"UI-SCREEN-001", "UI-MESSAGE-001", "API-SPEC-001", "EXTIF-001", "DATA-ERD-001", "SEC-001", "SEC-AUTHZ-001", "BATCH-OPS-001", "NFR-AVAIL-001"})
        self.assertIsNone(items["UI-SCREEN-001"]["status"])
        self.assertEqual(items["BATCH-OPS-001"]["status"], "not_applicable")
        self.assertEqual(review["rubric"]["完全性"], "PASS")
        with self.assertRaisesRegex(ValueError, "既に存在"):
            evaluate_review_items.emit_skeleton(self.review_path, self.context_path, self.rules, False)

    def test_aggregate_and_renderer_are_reproducible(self):
        evaluate_review_items.emit_skeleton(self.review_path, self.context_path, self.rules, False)
        review = evaluate_review_items.load(self.review_path)
        for item in review["ai_quality_review"]["evaluation"]["item_results"]:
            if item["status"] is None:
                item.update({"status": "pass", "reason": "証跡を確認した", "recommended_action": None,
                             "evidence": [{"kind": "document_section", "reference": "4.2"}]})
        evaluate_review_items.write_atomic(self.review_path, review)
        evaluate_review_items.aggregate(self.review_path, self.context_path, self.rules, self.traceability, self.design, "2026-07-16T20:08:44+09:00", False)
        stored = evaluate_review_items.load(self.review_path)
        text1 = render_quality_evaluation.render(stored)
        stored["ai_quality_review"]["evaluation"]["report_sha256"] = "a" * 64
        stored["ai_quality_review"]["human_review"] = {"decision": "approved"}
        stored["ai_quality_review"]["dod_passed"] = True
        text2 = render_quality_evaluation.render(stored)
        self.assertEqual(text1, text2)
        self.assertNotIn("report_sha256", text1)
        self.assertNotIn("approved", text1)

    def test_unscored_item_cannot_be_aggregated(self):
        evaluate_review_items.emit_skeleton(self.review_path, self.context_path, self.rules, False)
        with self.assertRaisesRegex(ValueError, "status が未記入"):
            evaluate_review_items.aggregate(self.review_path, self.context_path, self.rules, self.traceability, self.design, None, False)
