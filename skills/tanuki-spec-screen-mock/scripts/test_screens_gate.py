#!/usr/bin/env python3
"""screens_gate.pyの検証を確認する。"""

from __future__ import annotations

import copy
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


CATALOG = _load("catalog")
GATE = _load("screens_gate")

STATES = {
    "normal": "予約可能な枠がある",
    "empty": "0件。条件を広げる案内を出す",
    "loading": "スケルトン表示",
    "error": "取得失敗。再試行ボタンを出す",
    "forbidden": "未ログインはログイン画面へ誘導",
}

VALID = {
    "meta": {
        "phase": "phase-1_公開サイト・予約",
        "source_spec": "01_要件定義書.md",
        "generated_at": "2026-07-30",
        "entry_screens": ["SC-001"],
    },
    "screens": [
        {
            "id": "SC-001",
            "name": "空き枠一覧",
            "purpose": "生徒が予約可能なレッスン枠を探す",
            "actor": "生徒",
            "layout": "list-with-filter",
            "trace": ["FR-001"],
            "blocks": [
                {"type": "header", "nav": ["予約", "履歴"]},
                {
                    "type": "filter-bar",
                    "fields": [
                        {"label": "日付", "control": "date", "required": False},
                    ],
                },
            ],
            "states": dict(STATES),
            "transitions": [{"on": "枠を選ぶ", "to": "SC-002", "kind": "forward"}],
        },
        {
            "id": "SC-002",
            "name": "予約確認",
            "purpose": "生徒が予約内容を確認して確定する",
            "actor": "生徒",
            "layout": "form",
            "trace": ["FR-002"],
            "blocks": [
                {"type": "header", "nav": ["予約"]},
                {
                    "type": "form-section",
                    "fields": [
                        {
                            "label": "連絡先",
                            "control": "text",
                            "required": True,
                            "constraint": "メール形式・100文字以内",
                            "error": "メールアドレスの形式で入力してください",
                        },
                    ],
                },
                {"type": "button-row", "buttons": ["確定する"]},
            ],
            "states": dict(STATES),
            "terminal": True,
            "transitions": [{"on": "一覧へ戻る", "to": "SC-001", "kind": "back"}],
        },
    ],
}


class SchemaTest(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = CATALOG.load_catalog()

    def _validate(self, mutate=None) -> "GATE.Result":
        data = copy.deepcopy(VALID)
        if mutate:
            mutate(data)
        return GATE.validate_schema(data, self.catalog)

    def test_valid_definition_passes(self) -> None:
        result = self._validate()
        self.assertEqual([], result.errors)
        self.assertTrue(result.ok())

    def test_missing_required_field_is_error(self) -> None:
        result = self._validate(lambda d: d["screens"][0].pop("purpose"))
        self.assertTrue(any("purpose" in error for error in result.errors))

    def test_bad_id_prefix_is_error(self) -> None:
        result = self._validate(lambda d: d["screens"][0].__setitem__("id", "S001"))
        self.assertTrue(any("S001" in error for error in result.errors))

    def test_duplicate_id_is_error(self) -> None:
        result = self._validate(lambda d: d["screens"][1].__setitem__("id", "SC-001"))
        self.assertTrue(any("重複" in error for error in result.errors))

    def test_unknown_layout_is_error(self) -> None:
        result = self._validate(lambda d: d["screens"][0].__setitem__("layout", "kanban"))
        self.assertTrue(any("kanban" in error for error in result.errors))

    def test_unknown_block_type_is_error(self) -> None:
        result = self._validate(lambda d: d["screens"][0]["blocks"].append({"type": "carousel"}))
        self.assertTrue(any("carousel" in error for error in result.errors))

    def test_missing_required_block_is_error(self) -> None:
        result = self._validate(lambda d: d["screens"][1]["blocks"].pop(2))
        self.assertTrue(any("button-row" in error for error in result.errors))

    def test_forbidden_block_is_error(self) -> None:
        result = self._validate(lambda d: d["screens"][1]["blocks"].append({"type": "pagination"}))
        self.assertTrue(any("pagination" in error for error in result.errors))

    def test_empty_trace_is_warning_not_error(self) -> None:
        result = self._validate(lambda d: d["screens"][0].__setitem__("trace", []))
        self.assertEqual([], result.errors)
        self.assertTrue(any("trace" in warning for warning in result.warnings))

    def test_entry_screen_must_exist(self) -> None:
        result = self._validate(lambda d: d["meta"].__setitem__("entry_screens", ["SC-999"]))
        self.assertTrue(any("SC-999" in error for error in result.errors))


class TransitionTest(unittest.TestCase):
    def _validate(self, mutate=None) -> "GATE.Result":
        data = copy.deepcopy(VALID)
        if mutate:
            mutate(data)
        return GATE.validate_transitions(data)

    def test_valid_transitions_pass(self) -> None:
        self.assertEqual([], self._validate().errors)

    def test_transition_to_unknown_screen_is_error(self) -> None:
        result = self._validate(
            lambda d: d["screens"][0]["transitions"].append({"on": "詳細", "to": "SC-404", "kind": "forward"})
        )
        self.assertTrue(any("SC-404" in error for error in result.errors))

    def test_unreachable_screen_is_error(self) -> None:
        def mutate(d):
            d["screens"][0]["transitions"] = []
            d["screens"][0]["terminal"] = True

        result = self._validate(mutate)
        self.assertTrue(any("SC-002" in error and "到達" in error for error in result.errors))

    def test_dead_end_without_terminal_is_error(self) -> None:
        def mutate(d):
            d["screens"][1]["transitions"] = []
            d["screens"][1].pop("terminal")

        result = self._validate(mutate)
        self.assertTrue(any("SC-002" in error and "行き止まり" in error for error in result.errors))

    def test_dead_end_with_terminal_flag_passes(self) -> None:
        def mutate(d):
            d["screens"][1]["transitions"] = []

        self.assertEqual([], self._validate(mutate).errors)

    def test_unknown_transition_kind_is_error(self) -> None:
        result = self._validate(
            lambda d: d["screens"][0]["transitions"][0].__setitem__("kind", "sideways")
        )
        self.assertTrue(any("sideways" in error for error in result.errors))

    def test_self_loop_only_is_error(self) -> None:
        def mutate(d):
            d["screens"][1]["transitions"] = [{"on": "再読込", "to": "SC-002", "kind": "forward"}]
            d["screens"][1].pop("terminal")

        result = self._validate(mutate)
        self.assertTrue(any("SC-002" in error and "自分自身" in error for error in result.errors))


if __name__ == "__main__":
    unittest.main()
