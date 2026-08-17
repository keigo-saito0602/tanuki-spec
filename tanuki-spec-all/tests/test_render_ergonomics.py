from __future__ import annotations

import re
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evaluation"))
import generate_templates
import render_html_views


CHAR_LABELS = {"functional": "機能性"}
NON_FUNCTIONAL = {"source": "非機能観点", "major_items": []}


def demo_item(**overrides):
    item = {
        "id": "x-demo",
        "name": "デモ項目",
        "purpose": "説明のため",
        "required": True,
        "source": "要件定義観点 S00",
        "aspects": ["functional"],
    }
    item.update(overrides)
    return item


class AuthorMetaTest(unittest.TestCase):
    def test_body_carries_no_author_meta_and_no_dead_marker(self):
        """本文には見出しとFILLブロックだけを置き、根拠は付録へ退避する。"""
        guides: list = []
        text = "\n".join(generate_templates.render_item(demo_item(), CHAR_LABELS, NON_FUNCTIONAL, guides))
        self.assertNotIn("記入ガイド", text)
        self.assertNotIn("出典", text)
        # spec-item マーカーはどのコードも読まないため出力しない
        self.assertNotIn("spec-item:", text)
        self.assertEqual(guides, [("x-demo", "デモ項目", "説明のため", "要件定義観点 S00", "機能性")])

    def test_fill_block_is_a_single_line(self):
        text = "\n".join(generate_templates.render_item(demo_item(), CHAR_LABELS, NON_FUNCTIONAL))
        self.assertIn("<!-- FILL:START x-demo -->（未記入）<!-- FILL:END x-demo -->", text)


class ItemOrderTest(unittest.TestCase):
    def test_items_are_ordered_required_then_conditional_then_optional(self):
        items = [
            {"id": "a", "required": False},
            {"id": "b", "required": True},
            {"id": "c", "required": "conditional"},
            {"id": "d", "required": True},
        ]
        # 同じ優先度どうしはSSOTの並びを保つ（安定ソート）
        self.assertEqual([i["id"] for i in generate_templates.by_priority(items)], ["b", "d", "c", "a"])


class NonFunctionalSectionTest(unittest.TestCase):
    """35の非機能明細は大項目ごとの節にする。親のFILL内へ入れ子にはしない。"""

    NF = {
        "source": "非機能観点",
        "major_items": [
            {"id": "nf-a", "label": "可用性", "required": True,
             "sub_items": [{"name": "継続性", "metric": "稼働率/RTO"}, {"name": "耐障害性", "metric": "冗長化"}]},
            {"id": "nf-mig", "label": "移行性", "required": False,
             "sub_items": [{"name": "移行方式", "metric": "展開ステップ数"}]},
        ],
    }

    def _render(self):
        return "\n".join(generate_templates.render_item(demo_item(expands="non_functional"), CHAR_LABELS, self.NF))

    def test_parent_fill_block_stays_empty_and_separate(self):
        sys.path.insert(0, str(ROOT / "evaluation"))
        import coverage

        body = coverage.find_body(self._render(), "x-demo")
        self.assertIsNotNone(body)
        self.assertNotIn("|", body, "親のFILL内に表が入り込んでいる")
        self.assertNotIn("#####", body)
        filled, status = coverage.classify_body(body, True)
        self.assertFalse(filled, "空テンプレートの親項目が充足と判定されている")
        self.assertEqual(status, "未記入")

    def test_each_major_becomes_a_section_with_bold_labels(self):
        """明細は太字ラベル＋独立行のFILL。見出しにすると6階層目が生まれるため使わない。"""
        text = self._render()
        self.assertIn("##### 可用性", text)
        self.assertNotIn("| 必須 | 項目 | 確認指標 | 記入 |", text, "表形式が残っている")
        self.assertNotIn("###### ", text, "見出し階層が6段目まで深くなっている")
        self.assertIn("**継続性**［必須］（確認指標: 稼働率/RTO）", text)
        self.assertIn(
            "<!-- FILL:START x-demo--nf-a--01 -->（未記入）<!-- FILL:END x-demo--nf-a--01 -->",
            text,
        )

    def test_optional_major_marks_children_as_optional(self):
        text = self._render()
        self.assertIn("##### 移行性", text)
        self.assertIn("**移行方式**［任意］（確認指標: 展開ステップ数）", text)

    def test_marker_ids_and_count_are_unchanged(self):
        """IDと個数が変わると既存の記入済み文書が壊れる。"""
        text = self._render()
        starts = re.findall(r"<!--\s*FILL:START\s+(x-demo--nf-[^\s]+)\s*-->", text)
        self.assertEqual(starts, ["x-demo--nf-a--01", "x-demo--nf-a--02", "x-demo--nf-mig--01"])

    def test_non_functional_children_are_not_duplicated_into_the_appendix(self):
        guides: list = []
        generate_templates.render_item(demo_item(expands="non_functional"), CHAR_LABELS, self.NF, guides)
        ids = [g[0] for g in guides]
        self.assertEqual(ids, ["x-demo"], "確認指標が表と付録で二重化している")


class TableHintTest(unittest.TestCase):
    """中身が表になる項目は、推奨カラムを記入形式として本文に見せる。"""

    def test_table_hint_renders_above_empty_fill_block(self):
        sys.path.insert(0, str(ROOT / "evaluation"))
        import coverage

        text = "\n".join(generate_templates.render_item(demo_item(table_hint="| A | B | C |"), CHAR_LABELS, NON_FUNCTIONAL))
        self.assertIn("> 📝 **記入形式**: `| A | B | C |`", text)
        # 記入形式は FILL の外に置き、FILL は空のまま＝未記入判定を壊さない
        filled, status = coverage.classify_body(coverage.find_body(text, "x-demo"), True)
        self.assertFalse(filled)
        self.assertEqual(status, "未記入")

    def test_item_without_table_hint_has_no_hint_line(self):
        text = "\n".join(generate_templates.render_item(demo_item(), CHAR_LABELS, NON_FUNCTIONAL))
        self.assertNotIn("記入形式", text)


class AppendixTest(unittest.TestCase):
    def test_appendix_renders_guides_as_a_visible_table(self):
        text = "\n".join(generate_templates.render_appendix([("x-demo", "デモ項目", "説明のため", "S00", "機能性")]))
        self.assertIn("## 付録: 項目の根拠一覧", text)
        self.assertIn("| ID | 項目 | 記入ガイド | 出典 | 品質観点 |", text)
        self.assertIn("| `x-demo` | デモ項目 | 説明のため | S00 | 機能性 |", text)

    def test_pipe_in_text_does_not_break_the_table(self):
        text = "\n".join(generate_templates.render_appendix([("x", "A|B", "C|D", "S", "―")]))
        self.assertIn(r"| `x` | A\|B | C\|D | S | ― |", text)


class DocumentHeaderTest(unittest.TestCase):
    def _minimal_data(self):
        return {
            "meta": {"version": "9.9.9"},
            "quality_characteristics": [{"id": "functional", "label": "機能性"}],
            "non_functional": {"source": "非機能観点", "major_items": []},
            "phases": {
                "demo": {
                    "label": "デモ",
                    "goal": "デモ用",
                    "audience": "非技術者（クライアント・経営視点）",
                    "reading_hint": "まずサマリだけ読む2パス読み",
                    "legend": ["**太字** = 決定事項", "⚠️ = リスク", "❓ = 未決事項"],
                    "pbr_guide": ["実装者視点で確認: 実装可能な粒度か"],
                    "categories": [
                        {
                            "id": "demo-cat",
                            "label": "デモ節",
                            "items": [{"id": "demo-x", "name": "項目", "purpose": "p", "required": True, "source": "s", "aspects": ["functional"]}],
                        }
                    ],
                }
            },
        }

    def test_header_renders_audience_legend_and_pbr(self):
        text = generate_templates.render_phase("demo", self._minimal_data())
        self.assertIn("👥 **読み手**: 非技術者（クライアント・経営視点）", text)
        self.assertIn("🧭 **読み方**: まずサマリだけ読む2パス読み", text)
        self.assertIn("🔤 **凡例**:", text)
        self.assertIn("🔎 **第三者レビュー視点（PBR）**", text)
        self.assertIn("実装者視点で確認: 実装可能な粒度か", text)

    def test_human_body_precedes_audit_items(self):
        text = generate_templates.render_phase("demo", self._minimal_data())
        self.assertLess(text.index("## 読者向け本文"), text.index("## 付録: 監査用項目"))
        self.assertLess(text.index("## 付録: 監査用項目"), text.index("### [必須] 項目"))
        self.assertIn("<!-- HUMAN:START -->", text)
        self.assertIn("<!-- FILL:START demo-x -->", text)
        self.assertEqual(text.count("<!-- AUTHOR-GUIDE:START -->"), 2)
        self.assertEqual(text.count("<!-- AUTHOR-GUIDE:END -->"), 2)
        self.assertIn("<!-- AUDIT:START -->", text)
        self.assertIn("<!-- AUDIT:END -->", text)

    def test_reader_view_hides_audit_template_fields(self):
        text = generate_templates.render_phase("demo", self._minimal_data())
        reader_text = render_html_views.strip_reader_only_content(text)
        self.assertIn("## 読者向け本文", reader_text)
        self.assertNotIn("## 付録: 監査用項目", reader_text)
        self.assertNotIn("FILL:START", reader_text)
        self.assertNotIn("### [必須] 項目", reader_text)

    def test_reader_view_preserves_content_inside_human_markers(self):
        text = (
            "# 要件\n\n<!-- HUMAN:START -->\n"
            "## 読者向け本文\n予約を完了できる。\n"
            "<!-- HUMAN:END -->\n"
        )

        reader_text = render_html_views.strip_reader_only_content(text)

        self.assertIn("## 読者向け本文", reader_text)
        self.assertIn("予約を完了できる。", reader_text)
        self.assertNotIn("HUMAN:START", reader_text)

    def test_reader_view_preserves_business_quote_with_guide_words(self):
        text = """# 方針

> **ゴール**: 3か月で予約完了率を10%改善する。
> 月次レビューで未達なら是正する。
"""
        reader_text = render_html_views.strip_reader_only_content(text)
        self.assertIn("予約完了率を10%改善", reader_text)
        self.assertIn("月次レビュー", reader_text)

    def test_reader_view_removes_structured_legacy_header_guide(self):
        text = """# 要件

> **ゴール**: 外部仕様を確定する
> 👥 **読み手**: 第三者の技術者
> 🧭 **読み方**: 2パスで確認する
> 🔤 **凡例**: 決定 / 未決
> 📎 **記入方法**: 末尾の付録を参照する

## 読者向け本文
予約を扱う。
"""
        reader_text = render_html_views.strip_reader_only_content(text)
        self.assertNotIn("外部仕様を確定", reader_text)
        self.assertNotIn("第三者の技術者", reader_text)
        self.assertIn("予約を扱う", reader_text)

    def test_reader_body_requires_content_between_human_markers(self):
        self.assertFalse(
            render_html_views.reader_body_complete(
                "<!-- HUMAN:START -->\n\n<!-- HUMAN:END -->"
            )
        )
        self.assertFalse(
            render_html_views.reader_body_complete(
                "<!-- HUMAN:START -->\n"
                "[要確認: 案件と読者に合わせた本文を作成してください]\n"
                "<!-- HUMAN:END -->"
            )
        )
        self.assertTrue(
            render_html_views.reader_body_complete(
                "<!-- HUMAN:START -->\n予約を完了できる。\n<!-- HUMAN:END -->"
            )
        )
        self.assertFalse(
            render_html_views.reader_body_complete(
                "# 要件\n\n[要確認: 案件と読者に合わせた本文を作成してください]\n"
            )
        )

    def test_multiple_human_blocks_cannot_hide_an_unfilled_body(self):
        text = (
            "<!-- HUMAN:START -->\n"
            "[要確認: 案件と読者に合わせた本文を作成してください]\n"
            "<!-- HUMAN:END -->\n"
            "<!-- HUMAN:START -->\n予約を完了できる。\n<!-- HUMAN:END -->\n"
        )

        self.assertFalse(render_html_views.reader_body_complete(text))
        self.assertTrue(
            any(
                "1つだけ" in issue
                for issue in render_html_views.validate_document_markers(text)
            )
        )

    def test_nested_human_marker_is_rejected_without_deleting_its_body(self):
        text = (
            "<!-- AUTHOR-GUIDE:START -->\n"
            "<!-- HUMAN:START -->\n読者向け本文。\n<!-- HUMAN:END -->\n"
            "<!-- AUTHOR-GUIDE:END -->\n"
        )

        self.assertTrue(render_html_views.validate_document_markers(text))
        self.assertIn(
            "読者向け本文。",
            render_html_views.strip_reader_only_content(text),
        )

    def test_unterminated_html_comment_does_not_hide_following_markdown(self):
        text = "# 要件\n\n本文。\n\n<!-- 未終端コメント\n\n## 後続節\n後続の本文。\n"
        reader_text = render_html_views.strip_reader_only_content(text)
        self.assertIn("## 後続節", reader_text)
        self.assertIn("後続の本文", reader_text)
        self.assertTrue(render_html_views.validate_document_markers(text))

    def test_marker_mismatch_and_unterminated_marker_are_reported(self):
        mismatched = "<!-- AUTHOR-GUIDE:START -->\n本文。\n<!-- HUMAN:END -->\n"
        self.assertTrue(render_html_views.validate_document_markers(mismatched))
        unterminated = "<!-- AUDIT:START -->\n本文。\n"
        self.assertTrue(render_html_views.validate_document_markers(unterminated))

    def test_marker_notation_in_code_fence_is_preserved_and_ignored(self):
        text = """# 記法例

```markdown
<!-- AUTHOR-GUIDE:START -->
<!-- AUDIT:END -->
<!-- 未終端コメント
```

## 本文
実際の本文。
"""
        reader_text = render_html_views.strip_reader_only_content(text)
        self.assertIn("<!-- AUTHOR-GUIDE:START -->", reader_text)
        self.assertIn("<!-- 未終端コメント", reader_text)
        self.assertEqual([], render_html_views.validate_document_markers(text))

    def test_legacy_audit_tail_preserves_section_after_evidence_appendix(self):
        text = """# 要件

## 読者向け本文
表示する本文。

## 付録: 監査用項目
表示しない。

## 業務要件
表示しない監査項目。

## 付録: 項目の根拠一覧
表示しない根拠。

## 変更履歴
この節は表示する。
"""
        reader_text = render_html_views.strip_reader_only_content(text)
        self.assertNotIn("表示しない監査項目", reader_text)
        self.assertNotIn("表示しない根拠", reader_text)
        self.assertIn("## 変更履歴", reader_text)
        self.assertIn("この節は表示する", reader_text)


class ReviewChecklistTest(unittest.TestCase):
    def test_category_review_checklist_renders_as_blockquote(self):
        data = {
            "meta": {"version": "9.9.9"},
            "quality_characteristics": [{"id": "functional", "label": "機能性"}],
            "non_functional": {"source": "非機能観点", "major_items": []},
            "phases": {
                "demo": {
                    "label": "デモ",
                    "goal": "デモ用",
                    "categories": [
                        {
                            "id": "demo-cat",
                            "label": "デモ節",
                            "review_checklist": ["観点A", "観点B"],
                            "items": [{"id": "demo-x", "name": "項目", "purpose": "p", "required": True, "source": "s", "aspects": ["functional"]}],
                        }
                    ],
                }
            },
        }
        text = generate_templates.render_phase("demo", data)
        self.assertIn("> 🔍 **この節で確認すべきこと**", text)
        self.assertIn("> - 観点A", text)
        self.assertIn("> - 観点B", text)


if __name__ == "__main__":
    unittest.main()
