#!/usr/bin/env python3
"""design-tokens.jsonの検証とCSS変数化を確認する。"""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("tokens", SCRIPT_DIR / "tokens.py")
assert SPEC and SPEC.loader
TOKENS = importlib.util.module_from_spec(SPEC)
sys.modules["tokens"] = TOKENS
SPEC.loader.exec_module(TOKENS)

VALID = {
    "meta": {"sources": [{"kind": "code", "ref": "tailwind.config.ts", "confidence": "confirmed"}]},
    "color": {
        "primary": {"value": "#1a73e8", "source": "code", "confidence": "confirmed"},
        "surface": {"value": "#ffffff", "source": "code", "confidence": "confirmed"},
        "text": {"value": "#202124", "source": "screenshot", "confidence": "estimated"},
        "line": {"value": "#dadce0", "source": "code", "confidence": "confirmed"},
        "accent": {"value": "#b03a00", "source": "principles", "confidence": "proposed"},
    },
    "typography": {"font_family": {"value": "system-ui, sans-serif", "confidence": "proposed"}},
    "spacing": {"unit": {"value": "8px", "confidence": "proposed"}},
    "radius": {"md": {"value": "8px", "confidence": "estimated"}},
}


class ValidateTokensTest(unittest.TestCase):
    def _validate(self, mutate=None) -> list[str]:
        data = copy.deepcopy(VALID)
        if mutate:
            mutate(data)
        return TOKENS.validate_tokens(data)

    def test_valid_tokens_pass(self) -> None:
        self.assertEqual([], self._validate())

    def test_missing_color_role_is_error(self) -> None:
        errors = self._validate(lambda d: d["color"].pop("accent"))
        self.assertTrue(any("accent" in error for error in errors))

    def test_unknown_source_is_error(self) -> None:
        errors = self._validate(lambda d: d["color"]["primary"].__setitem__("source", "guess"))
        self.assertTrue(any("guess" in error for error in errors))

    def test_unknown_confidence_is_error(self) -> None:
        errors = self._validate(lambda d: d["color"]["text"].__setitem__("confidence", "maybe"))
        self.assertTrue(any("maybe" in error for error in errors))

    def test_invalid_hex_is_error(self) -> None:
        errors = self._validate(lambda d: d["color"]["primary"].__setitem__("value", "blue"))
        self.assertTrue(any("blue" in error for error in errors))

    def test_low_contrast_text_on_surface_is_error(self) -> None:
        errors = self._validate(lambda d: d["color"]["text"].__setitem__("value", "#c8c8c8"))
        self.assertTrue(any("4.5" in error for error in errors))


class CssVariableTest(unittest.TestCase):
    def test_emits_color_variables(self) -> None:
        css = TOKENS.to_css_variables(VALID)
        self.assertIn("--color-primary: #1a73e8;", css)
        self.assertIn("--color-surface: #ffffff;", css)

    def test_emits_non_color_variables(self) -> None:
        css = TOKENS.to_css_variables(VALID)
        self.assertIn("--radius-md: 8px;", css)
        self.assertIn("--typography-font_family: system-ui, sans-serif;", css)

    def test_escapes_closing_brace(self) -> None:
        data = copy.deepcopy(VALID)
        data["typography"]["font_family"]["value"] = "evil}</style>"
        css = TOKENS.to_css_variables(data)
        self.assertNotIn("</style>", css)


class UnconfirmedTest(unittest.TestCase):
    def test_lists_only_unconfirmed_tokens(self) -> None:
        rows = TOKENS.unconfirmed(VALID)
        names = {name for name, _, _ in rows}
        self.assertIn("color.text", names)
        self.assertIn("color.accent", names)
        self.assertNotIn("color.primary", names)


class ContrastTest(unittest.TestCase):
    def test_black_on_white_is_21(self) -> None:
        self.assertAlmostEqual(21.0, TOKENS.contrast_ratio("#000000", "#ffffff"), places=1)

    def test_same_color_is_1(self) -> None:
        self.assertAlmostEqual(1.0, TOKENS.contrast_ratio("#777777", "#777777"), places=2)


class TemplateTest(unittest.TestCase):
    def test_template_file_passes_validation(self) -> None:
        template = SCRIPT_DIR.parent / "templates" / "design-tokens-template.json"
        data = json.loads(template.read_text(encoding="utf-8"))
        self.assertEqual([], TOKENS.validate_tokens(data))


if __name__ == "__main__":
    unittest.main()
