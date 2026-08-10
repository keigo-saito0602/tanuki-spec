#!/usr/bin/env python3
"""component-catalog.yamlの読み込みを検証する。"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("catalog", SCRIPT_DIR / "catalog.py")
assert SPEC and SPEC.loader
CATALOG = importlib.util.module_from_spec(SPEC)
# exec_moduleの前にsys.modulesへ登録する。`from __future__ import annotations`が
# 効いたモジュール内のdataclassは、dataclasses._is_type()が
# sys.modules[cls.__module__]を引くため、未登録だとAttributeErrorで落ちる。
sys.modules["catalog"] = CATALOG
SPEC.loader.exec_module(CATALOG)


class LoadCatalogTest(unittest.TestCase):
    def _load(self, source: str):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.yaml"
            path.write_text(source, encoding="utf-8")
            return CATALOG.load_catalog(path)

    def test_default_catalog_loads(self) -> None:
        catalog = CATALOG.load_catalog()
        self.assertIn("form", catalog.layouts)
        self.assertIn("header", catalog.blocks)

    def test_form_layout_requires_button_row(self) -> None:
        catalog = CATALOG.load_catalog()
        self.assertIn("button-row", catalog.layouts["form"].required)

    def test_unknown_block_in_required_is_rejected(self) -> None:
        source = "blocks:\n  - header\nlayouts:\n  detail:\n    required: [missing-block]\n    forbidden: []\n"
        with self.assertRaises(CATALOG.CatalogError) as caught:
            self._load(source)
        self.assertIn("missing-block", str(caught.exception))

    def test_block_listed_as_required_and_forbidden_is_rejected(self) -> None:
        source = "blocks:\n  - header\nlayouts:\n  detail:\n    required: [header]\n    forbidden: [header]\n"
        with self.assertRaises(CATALOG.CatalogError) as caught:
            self._load(source)
        self.assertIn("必須と禁止", str(caught.exception))

    def test_missing_layouts_key_is_rejected(self) -> None:
        with self.assertRaises(CATALOG.CatalogError):
            self._load("blocks:\n  - header\n")

    def test_default_catalog_has_state_fields(self) -> None:
        catalog = CATALOG.load_catalog()
        self.assertIn("empty-state", catalog.state_required)
        self.assertIn("loading", catalog.blocks)
        self.assertEqual(frozenset({"error", "forbidden"}), catalog.state_components["alert"])

    _BASE = (
        "blocks:\n  - header\n  - empty-state\n  - alert\n  - loading\n"
        "layouts:\n  detail:\n    required: [header]\n    forbidden: []\n"
    )

    def test_empty_state_required_is_rejected(self) -> None:
        source = self._BASE + "state_required: []\nstate_components: {}\n"
        with self.assertRaises(CATALOG.CatalogError) as caught:
            self._load(source)
        self.assertIn("state_required", str(caught.exception))

    def test_state_required_with_unknown_block_is_rejected(self) -> None:
        source = (
            self._BASE
            + "state_required: [empty-state, unknown-block]\n"
            + "state_components:\n  empty-state: [empty]\n  unknown-block: [empty]\n"
        )
        with self.assertRaises(CATALOG.CatalogError) as caught:
            self._load(source)
        self.assertIn("unknown-block", str(caught.exception))

    def test_state_required_with_duplicate_is_rejected(self) -> None:
        source = (
            self._BASE
            + "state_required: [empty-state, empty-state]\n"
            + "state_components:\n  empty-state: [empty]\n"
        )
        with self.assertRaises(CATALOG.CatalogError) as caught:
            self._load(source)
        self.assertIn("重複", str(caught.exception))

    def test_state_components_key_mismatch_is_rejected(self) -> None:
        source = (
            self._BASE
            + "state_required: [empty-state, alert, loading]\n"
            + "state_components:\n  empty-state: [empty]\n  alert: [error, forbidden]\n"
        )
        with self.assertRaises(CATALOG.CatalogError) as caught:
            self._load(source)
        self.assertIn("state_components", str(caught.exception))

    def test_state_components_unknown_value_is_rejected(self) -> None:
        source = (
            self._BASE
            + "state_required: [empty-state]\n"
            + "state_components:\n  empty-state: [unknown-state]\n"
        )
        with self.assertRaises(CATALOG.CatalogError) as caught:
            self._load(source)
        self.assertIn("unknown-state", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
