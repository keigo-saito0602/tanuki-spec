from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evaluation"))
import generate_templates


CHAR_LABELS = {"functional": "機能性"}
NON_FUNCTIONAL = {"source": "非機能観点", "major_items": []}


class AuthorMetaTest(unittest.TestCase):
    def test_author_meta_is_hidden_in_html_comment(self):
        item = {
            "id": "x-demo",
            "name": "デモ項目",
            "purpose": "説明のため",
            "required": True,
            "source": "要件定義観点 S00",
            "aspects": ["functional"],
        }
        text = "\n".join(generate_templates.render_item(item, CHAR_LABELS, NON_FUNCTIONAL))
        self.assertNotIn("- **記入ガイド**:", text)
        self.assertNotIn("- **出典**:", text)
        self.assertIn(
            "<!-- 記入ガイド: 説明のため ／ 出典: 要件定義観点 S00 ／ 品質観点: 機能性 -->",
            text,
        )
        self.assertIn("<!-- FILL:START x-demo -->", text)
        self.assertIn("<!-- FILL:END x-demo -->", text)


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
