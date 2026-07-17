from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evaluation"))
import generate_templates


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


class NonFunctionalTableTest(unittest.TestCase):
    """35の非機能明細は大項目ごとの表にする。親のFILL内へ入れ子にはしない。"""

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

    def test_each_major_becomes_a_table_with_child_fill_cells(self):
        text = self._render()
        self.assertIn("##### 可用性", text)
        self.assertIn("| 必須 | 項目 | 確認指標 | 記入 |", text)
        self.assertIn("| 必須 | 継続性 | 稼働率/RTO | <!-- FILL:START x-demo--nf-a--01 -->（未記入）<!-- FILL:END x-demo--nf-a--01 -->", text)
        self.assertIn("| 必須 | 耐障害性 | 冗長化 | <!-- FILL:START x-demo--nf-a--02 -->（未記入）<!-- FILL:END x-demo--nf-a--02 -->", text)

    def test_optional_major_marks_children_as_optional(self):
        text = self._render()
        self.assertIn("##### 移行性", text)
        self.assertIn("| 任意 | 移行方式 | 展開ステップ数 | <!-- FILL:START x-demo--nf-mig--01 -->", text)

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
