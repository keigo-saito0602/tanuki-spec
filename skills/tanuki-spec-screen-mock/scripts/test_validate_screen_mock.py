#!/usr/bin/env python3
"""生成した画面モックHTMLの契約検証を確認する。"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent


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


VALIDATOR = _load("validate_screen_mock")
RENDER = _load("render_screen_mock")

import yaml  # noqa: E402

SCREENS = yaml.safe_load((SKILL_DIR / "templates" / "screens-template.yaml").read_text(encoding="utf-8"))
TOKENS_DATA = json.loads((SKILL_DIR / "templates" / "design-tokens-template.json").read_text(encoding="utf-8"))


class ValidateTest(unittest.TestCase):
    def _validate(self, html: str) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mock.html"
            path.write_text(html, encoding="utf-8")
            return VALIDATOR.validate(path)

    def setUp(self) -> None:
        self.html = RENDER.render(SCREENS, TOKENS_DATA)

    def test_generated_mock_passes(self) -> None:
        self.assertEqual([], self._validate(self.html))

    def test_script_tag_is_error(self) -> None:
        errors = self._validate(self.html.replace("</body>", "<script>alert(1)</script></body>"))
        self.assertTrue(any("script" in error for error in errors))

    def test_event_attribute_is_error(self) -> None:
        errors = self._validate(self.html.replace('<div class="app">', '<div class="app" onclick="x()">'))
        self.assertTrue(any("onclick" in error for error in errors))

    def test_external_stylesheet_is_error(self) -> None:
        errors = self._validate(
            self.html.replace("</head>", '<link rel="stylesheet" href="https://cdn.example.com/a.css"></head>')
        )
        self.assertTrue(any("外部" in error for error in errors))

    def test_missing_viewport_is_error(self) -> None:
        errors = self._validate(self.html.replace('name="viewport"', 'name="viewport-removed"'))
        self.assertTrue(any("viewport" in error for error in errors))

    def test_missing_lang_is_error(self) -> None:
        errors = self._validate(self.html.replace('<html lang="ja">', "<html>"))
        self.assertTrue(any("lang" in error for error in errors))

    def test_two_h1_is_error(self) -> None:
        errors = self._validate(self.html.replace("</body>", "<h1>余分な見出し</h1></body>"))
        self.assertTrue(any("h1" in error for error in errors))

    def test_low_contrast_token_is_error(self) -> None:
        errors = self._validate(self.html.replace("--color-text: #1c1c1c;", "--color-text: #cccccc;"))
        self.assertTrue(any("4.5" in error for error in errors))

    def test_wireframe_override_does_not_mask_root_surface(self) -> None:
        """ワイヤーモードの--color-surface: #ffffffを拾って:rootの背景色を取り違えないこと。"""
        errors = self._validate(self.html.replace("--color-surface: #ffffff;", "--color-surface: #101010;", 1))
        self.assertTrue(any("4.5" in error for error in errors))

    def test_iframe_is_error(self) -> None:
        errors = self._validate(self.html.replace("</body>", '<iframe src="data:,"></iframe></body>'))
        self.assertTrue(any("iframe" in error for error in errors))

    def test_missing_csp_is_error(self) -> None:
        errors = self._validate(self.html.replace("Content-Security-Policy", "X-Removed"))
        self.assertTrue(any("Content-Security-Policy" in error for error in errors))

    def test_pale_primary_is_error(self) -> None:
        errors = self._validate(self.html.replace("--color-primary: #1a5fb4;", "--color-primary: #fef9e7;"))
        self.assertTrue(any("primary" in error for error in errors))


MINIMAL_DOC = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'">
<title>t</title>
</head>
<body>
<h1>タイトル</h1>
<section class="screen" id="SC-001">
{blocks}
</section>
</body>
</html>"""


class ElementStateMarkerTest(unittest.TestCase):
    def _validate(self, html: str) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mock.html"
            path.write_text(html, encoding="utf-8")
            return VALIDATOR.validate(path)

    def _doc(self, blocks: str) -> str:
        return MINIMAL_DOC.format(blocks=blocks)

    def test_generated_mock_has_no_state_marker_errors(self) -> None:
        html = RENDER.render(SCREENS, TOKENS_DATA)
        errors = self._validate(html)
        self.assertFalse(any("data-state" in error for error in errors))

    def test_element_with_text_only_passes(self) -> None:
        html = self._doc('<div data-state="error">エラーが発生しました</div>')
        errors = self._validate(html)
        self.assertFalse(any("data-state" in error for error in errors))

    def test_element_with_border_only_passes(self) -> None:
        html = self._doc('<div data-state="error" style="border-left:4px solid #b3261e"></div>')
        errors = self._validate(html)
        self.assertFalse(any("data-state" in error for error in errors))

    def test_element_with_icon_only_passes(self) -> None:
        html = self._doc('<div data-state="error"><span aria-hidden="true">⚠</span></div>')
        errors = self._validate(html)
        self.assertFalse(any("data-state" in error for error in errors))

    def test_zero_border_style_does_not_count_as_border_cue(self) -> None:
        """sr-onlyパターンのborder:0はダミーであり、境界線の手掛かりとして数えない。"""
        html = self._doc('<div data-state="error" style="border:0"></div>')
        errors = self._validate(html)
        self.assertTrue(any("data-state" in error for error in errors))

    def test_element_with_none_of_the_three_cues_is_error(self) -> None:
        html = self._doc('<div data-state="error"></div>')
        errors = self._validate(html)
        self.assertTrue(any("data-state" in error and "error" in error for error in errors))


class ScreenStateCrossCheckTest(unittest.TestCase):
    def setUp(self) -> None:
        self.html = RENDER.render(SCREENS, TOKENS_DATA)

    def _validate(self, html: str, screens_data: dict) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            html_path = Path(directory) / "mock.html"
            html_path.write_text(html, encoding="utf-8")
            screens_path = Path(directory) / "screens.yaml"
            screens_path.write_text(yaml.safe_dump(screens_data, allow_unicode=True), encoding="utf-8")
            return VALIDATOR.validate(html_path, screens_path)

    def test_matching_states_produce_no_cross_check_errors(self) -> None:
        errors = self._validate(self.html, SCREENS)
        self.assertEqual([], errors)

    def test_stripping_all_data_state_from_a_screen_is_reported_as_missing(self) -> None:
        mutated = self.html.replace('data-state="empty"', "").replace('data-state="loading"', "").replace(
            'data-state="error"', "", 1
        )
        errors = self._validate(mutated, SCREENS)
        self.assertTrue(any("SC-001" in error and "empty" in error for error in errors))

    def test_moving_expected_state_to_another_screen_flags_both_screens(self) -> None:
        """SC-001のdata-state="empty"をSC-002側へ付け替えると、両画面で不一致が出る。"""
        mutated = self.html.replace('data-state="empty"', 'data-state="empty-moved"', 1)
        mutated = mutated.replace(
            '<section class="screen" id="SC-002">',
            '<section class="screen" id="SC-002"><div data-state="empty" style="border:2px solid #000">moved</div>',
            1,
        )
        errors = self._validate(mutated, SCREENS)
        self.assertTrue(any("SC-001" in error and "empty" in error for error in errors))
        self.assertTrue(any("SC-002" in error and "empty" in error for error in errors))

    def test_screen_id_in_yaml_but_missing_from_html_is_error(self) -> None:
        screens_data = {"screens": SCREENS["screens"] + [{"id": "SC-999", "blocks": [{"type": "alert", "state": "error"}]}]}
        errors = self._validate(self.html, screens_data)
        self.assertTrue(any("SC-999" in error for error in errors))

    def test_screen_id_in_html_but_missing_from_yaml_is_error(self) -> None:
        screens_data = {"screens": [s for s in SCREENS["screens"] if s["id"] != "SC-E01"]}
        errors = self._validate(self.html, screens_data)
        self.assertTrue(any("SC-E01" in error for error in errors))

    def test_screens_argument_omitted_skips_cross_check(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mock.html"
            path.write_text(self.html, encoding="utf-8")
            errors = VALIDATOR.validate(path)
        self.assertEqual([], errors)


if __name__ == "__main__":
    unittest.main()
