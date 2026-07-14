from __future__ import annotations

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evaluation"))
import coverage
import yaml


class CoverageTest(unittest.TestCase):
    def test_confirmation_is_not_filled(self):
        self.assertEqual(coverage.classify_body("[要確認: 保持期間を確認]", True), (False, "要確認"))

    def test_conditional_not_applicable_requires_reason(self):
        self.assertEqual(coverage.classify_body("[対象外: SaaSを採用しない]", "conditional"), (False, "対象外"))
        self.assertEqual(coverage.classify_body("[対象外: ]", "conditional"), (False, "対象外（不正）"))

    def test_required_item_cannot_be_not_applicable(self):
        self.assertEqual(coverage.classify_body("[対象外: 理由]", True), (False, "対象外（不正）"))

    def test_template_todo_is_not_filled(self):
        self.assertEqual(coverage.classify_body("（未記入）\n- 性能: TODO", True), (False, "未記入"))

    def test_old_ssot_version_is_a_structural_failure(self):
        data = yaml.safe_load((Path(__file__).resolve().parents[1] / "spec-items.yaml").read_text(encoding="utf-8"))
        failures = coverage.structural_failures("---\ntemplate: requirements\nspec_items_version: '0.0.0'\n---", data, "requirements")
        self.assertTrue(any("spec_items_version が不一致" in failure for failure in failures))
