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

    def test_not_applicable_allows_evidence_line(self):
        """根拠を書く規約と対象外判定を両立させる（GAP-017）。"""
        body = (
            "- **根拠**: [参照] `_project/profile.md`対象外リスト\n"
            "- **結論**: [対象外: 業務パッケージを導入しない。FirebaseはBaaS基盤である]"
        )
        self.assertEqual(coverage.classify_body(body, "conditional"), (False, "対象外"))

    def test_not_applicable_with_evidence_still_rejects_empty_reason(self):
        body = "- **根拠**: [参照] profile.md\n- **結論**: [対象外: ]"
        self.assertEqual(coverage.classify_body(body, "conditional"), (False, "対象外（不正）"))

    def test_not_applicable_rejects_extra_content(self):
        """対象外と書きつつ別の内容も書いてある場合は認めない。"""
        body = "- **根拠**: [参照] profile.md\n- **結論**: [対象外: 理由]\n- 補足: ただし一部は実施する"
        self.assertEqual(coverage.classify_body(body, "conditional"), (False, "対象外（不正）"))

    def test_not_applicable_allows_evidence_on_the_same_line(self):
        """表のセルは1行しか持てないため、根拠と結論が同一行に並ぶ（GAP-017）。"""
        body = "- **根拠**: [参照] `_project/profile.md`。 [対象外: 新規アプリで一括移行元がない]"
        self.assertEqual(coverage.classify_body(body, "conditional"), (False, "対象外"))

    def test_same_line_evidence_without_marker_is_filled(self):
        """同一行に根拠しかない場合、対象外にはならず通常の充足判定になる。"""
        body = "- **根拠**: [参照] profile.md。移行は将来検討する"
        self.assertEqual(coverage.classify_body(body, "conditional"), (True, "充足"))
