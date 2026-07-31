#!/usr/bin/env python3
"""画面本体のレンダリングを確認する。"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPT_DIR / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    # exec_moduleの前にsys.modulesへ登録する。`from __future__ import annotations`が
    # 効いたモジュール内のdataclassは、dataclasses._is_type()が
    # sys.modules[cls.__module__]を引くため、未登録だとAttributeErrorで落ちる。
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


RENDER = _load("render_screen_mock")

SCREEN = {
    "id": "SC-001",
    "name": "空き枠一覧",
    "purpose": "生徒が予約可能なレッスン枠を探す",
    "actor": "生徒",
    "layout": "list-with-filter",
    "trace": ["FR-001", "FR-002"],
    "blocks": [
        {"type": "header", "nav": ["予約", "履歴"]},
        {"type": "filter-bar", "fields": [{"label": "日付", "control": "date", "required": False}]},
        {"type": "card-grid", "item_label": "レッスン枠", "item_fields": ["日時", "講師名"]},
    ],
    "states": {
        "normal": "枠がある",
        "empty": "0件の案内",
        "loading": "スケルトン",
        "error": "再試行ボタン",
        "forbidden": "該当なし: 全員が閲覧できる",
    },
    "transitions": [{"action": "枠を選ぶ", "to": "SC-002", "kind": "forward"}],
    "notes": ["[要確認] 残席0の枠を出すか"],
}


class RenderBlockTest(unittest.TestCase):
    def test_header_renders_nav_items(self) -> None:
        html = RENDER.render_block(SCREEN["blocks"][0])
        self.assertIn("予約", html)
        self.assertIn("履歴", html)

    def test_filter_bar_renders_field_labels(self) -> None:
        html = RENDER.render_block(SCREEN["blocks"][1])
        self.assertIn("日付", html)

    def test_card_grid_renders_item_fields(self) -> None:
        html = RENDER.render_block(SCREEN["blocks"][2])
        self.assertIn("日時", html)
        self.assertIn("講師名", html)

    def test_unknown_block_type_renders_placeholder(self) -> None:
        html = RENDER.render_block({"type": "kpi-tile"})
        self.assertIn("kpi-tile", html)

    def test_escapes_html_in_input(self) -> None:
        html = RENDER.render_block({"type": "header", "nav": ["<script>alert(1)</script>"]})
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)


class RenderScreenTest(unittest.TestCase):
    def test_section_has_screen_id(self) -> None:
        html = RENDER.render_screen(SCREEN)
        self.assertIn('id="SC-001"', html)

    def test_shows_name_and_purpose(self) -> None:
        html = RENDER.render_screen(SCREEN)
        self.assertIn("空き枠一覧", html)
        self.assertIn("生徒が予約可能なレッスン枠を探す", html)

    def test_shows_trace_ids(self) -> None:
        html = RENDER.render_screen(SCREEN)
        self.assertIn("FR-001", html)
        self.assertIn("FR-002", html)

    def test_transition_links_to_target_anchor(self) -> None:
        html = RENDER.render_screen(SCREEN)
        self.assertIn('href="#SC-002"', html)
        self.assertIn("枠を選ぶ", html)

    def test_shows_five_states(self) -> None:
        html = RENDER.render_screen(SCREEN)
        for value in SCREEN["states"].values():
            self.assertIn(value, html)

    def test_shows_notes_as_badge(self) -> None:
        html = RENDER.render_screen(SCREEN)
        self.assertIn("[要確認] 残席0の枠を出すか", html)


class RenderNavTest(unittest.TestCase):
    def test_lists_every_screen(self) -> None:
        html = RENDER.render_nav([SCREEN, dict(SCREEN, id="SC-002", name="予約確認")])
        self.assertIn('href="#SC-001"', html)
        self.assertIn('href="#SC-002"', html)
        self.assertIn("予約確認", html)


if __name__ == "__main__":
    unittest.main()
