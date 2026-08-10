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

    def test_form_field_renders_constraint_and_error(self) -> None:
        block = {
            "type": "form-section",
            "fields": [
                {
                    "label": "郵便番号",
                    "control": "text",
                    "required": True,
                    "constraint": "半角数字7桁",
                    "error": "郵便番号の形式が正しくありません",
                }
            ],
        }
        html = RENDER.render_block(block)
        self.assertIn("郵便番号", html)
        self.assertIn("半角数字7桁", html)
        self.assertIn("郵便番号の形式が正しくありません", html)
        self.assertIn("field-error", html)

    def test_form_field_error_has_non_color_cue(self) -> None:
        """エラーは色だけに頼らず、aria-hiddenなアイコンでも示す。"""

        block = {
            "type": "form-section",
            "fields": [
                {
                    "label": "郵便番号",
                    "control": "text",
                    "required": True,
                    "error": "郵便番号の形式が正しくありません",
                }
            ],
        }
        html = RENDER.render_block(block)
        self.assertIn('aria-hidden="true"', html)

    def test_form_field_without_constraint_or_error_renders_label_only(self) -> None:
        block = {
            "type": "form-section",
            "fields": [{"label": "備考", "control": "text", "required": False}],
        }
        html = RENDER.render_block(block)
        self.assertIn("備考", html)

    def test_form_field_escapes_constraint_and_error(self) -> None:
        block = {
            "type": "form-section",
            "fields": [
                {
                    "label": "項目",
                    "control": "text",
                    "required": True,
                    "constraint": "<script>alert(1)</script>",
                    "error": "<script>alert(2)</script>",
                }
            ],
        }
        html = RENDER.render_block(block)
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)

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


class RenderStateBlockTest(unittest.TestCase):
    ALLOWED_STATES = {"normal", "empty", "loading", "error", "forbidden"}

    def test_block_with_state_outputs_data_state_attribute(self) -> None:
        html = RENDER.render_block({"type": "empty-state", "state": "empty", "message": "0件です"})
        self.assertIn('data-state="empty"', html)

    def test_data_state_value_is_within_allowed_vocabulary(self) -> None:
        for block, expected in (
            ({"type": "empty-state", "state": "empty"}, "empty"),
            ({"type": "loading", "state": "loading"}, "loading"),
            ({"type": "alert", "state": "error"}, "error"),
            ({"type": "alert", "state": "forbidden"}, "forbidden"),
        ):
            html = RENDER.render_block(block)
            self.assertIn(f'data-state="{expected}"', html)
            self.assertIn(expected, self.ALLOWED_STATES)

    def test_block_without_state_has_no_data_state_attribute(self) -> None:
        html = RENDER.render_block({"type": "header", "nav": ["予約"]})
        self.assertNotIn("data-state", html)

    def test_alert_shows_icon_border_class_and_kind_label(self) -> None:
        html = RENDER.render_block({"type": "alert", "state": "error", "message": "失敗しました"})
        self.assertIn("aria-hidden=\"true\"", html)
        self.assertIn("border-left", html)
        self.assertIn("エラー", html)

        html_forbidden = RENDER.render_block({"type": "alert", "state": "forbidden", "message": "権限確認"})
        self.assertIn("権限がありません", html_forbidden)
        self.assertIn("border-left", html_forbidden)

    def test_loading_has_accessible_name(self) -> None:
        html = RENDER.render_block({"type": "loading", "state": "loading"})
        self.assertIn('aria-live="polite"', html)
        self.assertIn("読み込み中", html)

    def test_empty_state_shows_heading_and_icon(self) -> None:
        html = RENDER.render_block({"type": "empty-state", "state": "empty", "message": "0件です"})
        self.assertIn("データがありません", html)
        self.assertIn("aria-hidden=\"true\"", html)


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


class RenderWithNullFieldsTest(unittest.TestCase):
    """YAMLで `trace:` と値を省くとNoneになる。Noneでも落ちないことを確かめる。"""

    NULLED = dict(
        SCREEN,
        trace=None,
        notes=None,
        transitions=None,
        blocks=None,
        states=None,
        terminal=True,
    )

    def test_render_screen_tolerates_null_sequences(self) -> None:
        html = RENDER.render_screen(self.NULLED)
        self.assertIn('id="SC-001"', html)
        self.assertIn("未対応", html)
        self.assertIn("終端画面", html)

    def test_render_diagram_and_trace_tolerate_null_sequences(self) -> None:
        screens = [self.NULLED]
        self.assertIn("終端", RENDER.render_diagram(screens))
        self.assertIn("対応する要件が書かれていません", RENDER.render_trace(screens, TOKEN_DATA))

    def test_render_block_tolerates_null_sequences(self) -> None:
        for block in (
            {"type": "header", "nav": None},
            {"type": "filter-bar", "fields": None},
            {"type": "card-grid", "item_fields": None},
            {"type": "table", "columns": None},
            {"type": "button-row", "buttons": None},
            {"type": "list", "items": None},
        ):
            with self.subTest(block=block["type"]):
                self.assertIn(block["type"], RENDER.render_block(block))

    def test_render_document_tolerates_null_meta_and_screens(self) -> None:
        html = RENDER.render({"meta": None, "screens": [self.NULLED]}, TOKEN_DATA)
        self.assertIn('id="SC-001"', html)


class RenderNavTest(unittest.TestCase):
    def test_lists_every_screen(self) -> None:
        html = RENDER.render_nav([SCREEN, dict(SCREEN, id="SC-002", name="予約確認")])
        self.assertIn('href="#SC-001"', html)
        self.assertIn('href="#SC-002"', html)
        self.assertIn("予約確認", html)


TOKEN_DATA = {
    "color": {
        "primary": {"value": "#1a73e8", "source": "code", "confidence": "confirmed"},
        "surface": {"value": "#ffffff", "source": "code", "confidence": "confirmed"},
        "text": {"value": "#202124", "source": "screenshot", "confidence": "estimated"},
        "line": {"value": "#dadce0", "source": "code", "confidence": "confirmed"},
        "accent": {"value": "#b03a00", "source": "principles", "confidence": "proposed"},
    },
    "radius": {"md": {"value": "8px", "source": "code", "confidence": "confirmed"}},
}

SCREENS_DATA = {
    "meta": {"phase": "phase-1_予約", "entry_screens": ["SC-001"]},
    "screens": [SCREEN, dict(SCREEN, id="SC-002", name="予約確認", transitions=[], terminal=True, notes=[])],
}


class RenderDiagramTest(unittest.TestCase):
    def test_lists_each_transition_as_a_row(self) -> None:
        html = RENDER.render_diagram(SCREENS_DATA["screens"])
        self.assertIn("SC-001", html)
        self.assertIn("SC-002", html)
        self.assertIn("枠を選ぶ", html)

    def test_marks_terminal_screen(self) -> None:
        html = RENDER.render_diagram(SCREENS_DATA["screens"])
        self.assertIn("終端", html)


class RenderTraceTest(unittest.TestCase):
    def test_maps_requirement_to_screens(self) -> None:
        html = RENDER.render_trace(SCREENS_DATA["screens"], TOKEN_DATA)
        self.assertIn("FR-001", html)

    def test_lists_unconfirmed_tokens(self) -> None:
        html = RENDER.render_trace(SCREENS_DATA["screens"], TOKEN_DATA)
        self.assertIn("color.text", html)
        self.assertIn("color.accent", html)

    def test_lists_screen_notes(self) -> None:
        html = RENDER.render_trace(SCREENS_DATA["screens"], TOKEN_DATA)
        self.assertIn("残席0の枠を出すか", html)


class RenderDocumentTest(unittest.TestCase):
    def setUp(self) -> None:
        self.html = RENDER.render(SCREENS_DATA, TOKEN_DATA)

    def test_no_marker_remains(self) -> None:
        for marker in ("<!--TITLE-->", "<!--TOKENS-->", "<!--NAV-->", "<!--SCREENS-->", "<!--DIAGRAM-->", "<!--TRACE-->"):
            self.assertNotIn(marker, self.html)

    def test_injects_token_variables(self) -> None:
        self.assertIn("--color-primary: #1a73e8;", self.html)

    def test_contains_no_script_or_external_reference(self) -> None:
        self.assertNotIn("<script", self.html)
        self.assertNotIn("onclick", self.html)
        self.assertNotIn("http://", self.html)

    def test_malicious_token_name_cannot_escape_style_block(self) -> None:
        """トークン名にタグを仕込んでも<style>から抜け出せない。

        値だけをサニタイズしていた頃は、design-tokens.jsonのキー名が生のまま
        <style>へ入り、scriptタグを出力できた。
        """

        poisoned = {
            "color": dict(
                TOKEN_DATA["color"],
                **{"primary</style><script>alert(1)</script>": {"value": "#1a73e8", "confidence": "confirmed"}},
            ),
        }
        html = RENDER.render(SCREENS_DATA, poisoned)
        self.assertNotIn("<script", html)
        self.assertNotIn("</style>", html.split("</style>", 1)[1])

    def test_malicious_token_value_cannot_escape_style_block(self) -> None:
        poisoned = {"color": {"primary": {"value": "#fff}</style><script>alert(1)</script>", "confidence": "confirmed"}}}
        html = RENDER.render(SCREENS_DATA, poisoned)
        self.assertNotIn("<script", html)

    def test_surface_token_paints_the_screen_and_box_background(self) -> None:
        """コントラスト検証が見る--color-surfaceを、実際の背景色にも使う。

        `.screen`と`.box`が#fff固定だと、暗い配色のトークンで
        「文字とsurfaceのコントラストは十分」と判定しつつ実画面は白背景になる。
        """

        for rule in (".screen {", ".box {"):
            declaration = self.html.split(rule, 1)[1].split("}", 1)[0]
            self.assertIn("background: var(--color-surface, #fff)", declaration)

    def test_contains_every_screen_section(self) -> None:
        self.assertIn('id="SC-001"', self.html)
        self.assertIn('id="SC-002"', self.html)


if __name__ == "__main__":
    unittest.main()
