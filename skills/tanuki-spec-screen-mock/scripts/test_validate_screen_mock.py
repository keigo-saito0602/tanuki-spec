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


if __name__ == "__main__":
    unittest.main()
