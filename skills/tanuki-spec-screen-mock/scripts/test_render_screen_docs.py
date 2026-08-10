#!/usr/bin/env python3
"""基本設計へ貼る画面一覧・遷移表の生成を確認する。"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("render_screen_docs", SCRIPT_DIR / "render_screen_docs.py")
assert SPEC and SPEC.loader
DOCS = importlib.util.module_from_spec(SPEC)
sys.modules["render_screen_docs"] = DOCS
SPEC.loader.exec_module(DOCS)

DATA = {
    "screens": [
        {
            "id": "SC-001",
            "name": "空き枠一覧",
            "transitions": [
                {"action": "枠を選ぶ", "to": "SC-002", "kind": "forward"},
                {"action": "ログイン", "to": "SC-L01", "kind": "forward"},
            ],
        },
        {"id": "SC-002", "name": "予約確認", "terminal": True, "transitions": []},
    ]
}


class RenderTableTest(unittest.TestCase):
    def setUp(self) -> None:
        self.table = DOCS.render_table(DATA)

    def test_header_matches_bd_screen_format(self) -> None:
        self.assertIn("| 画面ID | 画面名 | 遷移元→遷移先 | 主な操作 |", self.table)

    def test_transition_uses_arrow_notation(self) -> None:
        self.assertIn("SC-001→SC-002", self.table)

    def test_multiple_transitions_are_joined(self) -> None:
        row = [line for line in self.table.splitlines() if line.startswith("| SC-001 ")][0]
        self.assertIn("SC-001→SC-L01", row)
        self.assertIn("枠を選ぶ", row)
        self.assertIn("ログイン", row)

    def test_terminal_screen_shows_dash(self) -> None:
        row = [line for line in self.table.splitlines() if line.startswith("| SC-002 ")][0]
        self.assertIn("（終端）", row)

    def test_pipe_in_name_is_escaped(self) -> None:
        table = DOCS.render_table({"screens": [{"id": "SC-001", "name": "A|B", "terminal": True, "transitions": []}]})
        self.assertNotIn("| A|B |", table)
        self.assertIn(r"A\|B", table)


if __name__ == "__main__":
    unittest.main()
