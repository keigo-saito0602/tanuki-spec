#!/usr/bin/env python3
"""実ブラウザでの契約検査（320px横スクロール・タップ対象44px・フォーカス表現）を確認する。"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

from playwright.sync_api import sync_playwright

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPT_DIR / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


CHECKER = _load("check_browser_contract")
RENDER = _load("render_screen_mock")

import yaml  # noqa: E402

SCREENS = yaml.safe_load((SKILL_DIR / "templates" / "screens-template.yaml").read_text(encoding="utf-8"))
TOKENS_DATA = json.loads((SKILL_DIR / "templates" / "design-tokens-template.json").read_text(encoding="utf-8"))


class BrowserContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self) -> None:
        self.html = RENDER.render(SCREENS, TOKENS_DATA)

    def _check(self, html: str) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mock.html"
            path.write_text(html, encoding="utf-8")
            return CHECKER.check_with_browser(path, self.browser)

    def test_generated_mock_passes_all_three_checks(self) -> None:
        self.assertEqual([], self._check(self.html))

    def test_fixed_wide_element_causes_horizontal_scroll_error(self) -> None:
        mutated = self.html.replace(
            '<div class="box state-empty">',
            '<div class="box state-empty" style="width:900px">',
            1,
        )
        errors = self._check(mutated)
        self.assertTrue(any("横スクロール" in error and "SC-001" in error for error in errors))

    def test_tiny_button_fails_tap_target_size(self) -> None:
        mutated = self.html.replace(
            '<button type="button" class="btn">',
            '<button type="button" class="btn" '
            'style="min-height:10px;height:10px;width:10px;padding:0;display:inline-block">',
            1,
        )
        errors = self._check(mutated)
        self.assertTrue(any("タップ対象" in error for error in errors))

    def test_outline_none_on_link_fails_focus_check(self) -> None:
        mutated = self.html.replace('<a href="#">', '<a href="#" style="outline:none">', 1)
        errors = self._check(mutated)
        self.assertTrue(any("フォーカス" in error for error in errors))

    def test_low_contrast_outline_fails_focus_check(self) -> None:
        """画面内の遷移リンク（.btn-sub、背景は.screenの--color-surface: #fff）に、
        背景と同色のアウトラインを付けると3:1を満たさない。"""
        mutated = self.html.replace(
            '<a class="btn btn-sub" href="#SC-001">',
            '<a class="btn btn-sub" href="#SC-001" style="outline-color:#ffffff">',
            1,
        )
        errors = self._check(mutated)
        self.assertTrue(any("フォーカス" in error and "コントラスト" in error for error in errors))

    def test_orphan_input_outside_landmark_fails_axe_region_rule(self) -> None:
        """ランドマーク外に浮いた対話要素はaxe-coreのregionルールで検出する。"""
        mutated = self.html.replace(
            "</body>",
            '<input type="checkbox" id="orphan-checkbox"><label for="orphan-checkbox">迷子</label></body>',
            1,
        )
        errors = self._check(mutated)
        self.assertTrue(any("axe" in error.lower() or "ランドマーク" in error for error in errors))

    def test_mode_switch_label_shows_focus_when_hidden_radio_is_focused(self) -> None:
        """モード切替のラジオはopacity:0で隠しているため、対応するlabelに見えるフォーカス表現が要る。"""
        errors = self._check(self.html)
        self.assertFalse(any("ヘッダー操作" in error and "フォーカス" in error for error in errors))

    def test_axe_violation_only_on_second_screen_is_detected(self) -> None:
        """最初に表示されるのはdisplay:noneではないSC-001だけなので、SC-002だけの違反も検出できる必要がある。"""
        mutated = self.html.replace(
            '<section class="screen" id="SC-002">',
            '<section class="screen" id="SC-002"><h3></h3>',
            1,
        )
        errors = self._check(mutated)
        self.assertTrue(any("SC-002" in error and "axe" in error.lower() for error in errors))


if __name__ == "__main__":
    unittest.main()
