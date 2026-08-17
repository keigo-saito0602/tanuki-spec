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

STATES_SC1 = {
    "normal": "予約可能な枠がある",
    "empty": "0件。条件を広げる案内を出す",
    "loading": "スケルトン表示",
    "error": "取得失敗。再試行ボタンを出す",
    "forbidden": "該当なし: 全員が閲覧できる画面のため",
}

STATES_SC2 = {
    "normal": "入力内容が確認できる",
    "empty": "該当なし: 一覧を経由するため0件表示はない",
    "loading": "送信中はボタンを無効化",
    "error": "取得失敗。再試行ボタンを出す",
    "forbidden": "未ログインはログイン画面へ誘導",
}

EXPLORATION_SC1 = {
    "design_question": "生徒が候補を比較して予約へ進めるか",
    "hypothesis": "日付を先に選ぶと候補を比較しやすい",
    "risk": "medium",
    "validation_task": "明日の午後の候補を探し、最初に押す場所を説明してください",
    "rationale": "既存予約画面の日付フィルタと用語を踏襲する",
    "exploration_mode": "compare",
    "alternatives": [
        {
            "id": "alt-filter-first",
            "name": "条件を先に絞る",
            "summary": "日付と講師を先頭に置く",
            "decision": "adopted",
            "reason": "候補数を減らしやすいため",
        },
        {
            "id": "alt-calendar",
            "name": "カレンダー中心",
            "summary": "月間カレンダーから日付を選ぶ",
            "decision": "rejected",
            "reason": "週単位の比較では情報密度が高いため",
        },
    ],
    "state_strategy": {
        "priority_states": ["normal", "empty", "error"],
        "rationale": "候補がない場合と取得失敗を重点的に確認する",
    },
}

EXPLORATION_SC2 = {
    "design_question": "入力内容を確認して迷わず確定できるか",
    "hypothesis": "確認情報と主操作を同じ画面に置けば確定できる",
    "risk": "high",
    "validation_task": "入力内容を確認し、予約を確定する操作を説明してください",
    "rationale": "確定前に誤りを確認できるよう、入力と主操作をまとめる",
    "exploration_mode": "compare",
    "alternatives": [
        {
            "id": "alt-single",
            "name": "単一画面で確定",
            "summary": "入力確認と確定を同じ画面に置く",
            "decision": "adopted",
            "reason": "操作の往復を減らせるため",
        },
        {
            "id": "alt-wizard",
            "name": "確認を別画面に分ける",
            "summary": "入力と確認を段階に分ける",
            "decision": "rejected",
            "reason": "小さな予約では遷移が増えて負荷になるため",
        },
    ],
    "state_strategy": {
        "priority_states": ["normal", "loading", "error", "forbidden"],
        "rationale": "確定処理の失敗と権限切れで二重操作が起きるため",
    },
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
            **EXPLORATION_SC1,
            "blocks": [
                {"type": "header", "nav": ["予約", "履歴"]},
                {
                    "type": "filter-bar",
                    "fields": [
                        {"label": "日付", "control": "date", "required": False},
                    ],
                },
                {"type": "empty-state", "state": "empty", "message": "0件。条件を広げる案内を出す"},
                {"type": "loading", "state": "loading"},
                {"type": "alert", "state": "error", "message": "取得失敗。再試行ボタンを出す"},
            ],
            "states": dict(STATES_SC1),
            "transitions": [{"action": "枠を選ぶ", "to": "SC-002", "kind": "forward"}],
        },
        {
            "id": "SC-002",
            "name": "予約確認",
            "purpose": "生徒が予約内容を確認して確定する",
            "actor": "生徒",
            "layout": "form",
            "trace": ["FR-002"],
            **EXPLORATION_SC2,
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
                {"type": "loading", "state": "loading"},
                {"type": "alert", "state": "error", "message": "取得失敗。再試行ボタンを出す"},
                {"type": "alert", "state": "forbidden", "message": "未ログインはログイン画面へ誘導"},
            ],
            "states": dict(STATES_SC2),
            "terminal": True,
            "transitions": [{"action": "一覧へ戻る", "to": "SC-001", "kind": "back"}],
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

    def test_missing_exploration_field_is_error(self) -> None:
        result = self._validate(lambda d: d["screens"][0].pop("design_question"))
        self.assertTrue(any("design_question" in error for error in result.errors))

    def test_placeholder_exploration_text_is_error(self) -> None:
        for value in ("未定", "TBD", "<このモックで決めたい問い>"):
            with self.subTest(value=value):
                result = self._validate(
                    lambda d, placeholder=value: d["screens"][0].__setitem__(
                        "design_question", placeholder
                    )
                )
                self.assertTrue(any("仮値" in error for error in result.errors))

    def test_decided_sentence_containing_similar_word_is_not_placeholder(self) -> None:
        result = self._validate(
            lambda d: d["screens"][0].__setitem__(
                "rationale", "未定義の状態を作らないため既存導線を継承する"
            )
        )
        self.assertEqual([], result.errors)

    def test_explanatory_sentence_containing_tag_like_text_is_not_placeholder(self) -> None:
        result = self._validate(
            lambda d: d["screens"][0].__setitem__(
                "rationale", "説明文内の<select>相当の入力部品を既存パターンに合わせる"
            )
        )
        self.assertEqual([], result.errors)

    def test_html_control_name_is_not_treated_as_a_placeholder(self) -> None:
        result = self._validate(
            lambda d: d["screens"][0]["blocks"][1]["fields"][0].__setitem__(
                "control", "<select>"
            )
        )
        self.assertEqual([], result.errors)

    def test_unknown_risk_level_is_error(self) -> None:
        result = self._validate(lambda d: d["screens"][0].__setitem__("risk", "critical"))
        self.assertTrue(any("critical" in error for error in result.errors))

    def test_compare_mode_requires_two_or_three_with_one_adopted(self) -> None:
        result = self._validate(lambda d: d["screens"][0]["alternatives"].pop())
        self.assertTrue(any("compareモード" in error and "2〜3案" in error for error in result.errors))
        result = self._validate(
            lambda d: d["screens"][0]["alternatives"][1].__setitem__("decision", "adopted")
        )
        self.assertTrue(any("ちょうど1件" in error for error in result.errors))

    def test_inherit_mode_allows_one_adopted_pattern_for_non_high_risk(self) -> None:
        def inherit(data):
            screen = data["screens"][0]
            screen["exploration_mode"] = "inherit"
            screen["inherited_from"] = "既存の生徒向け予約一覧 SC-010"
            screen["alternatives"] = [screen["alternatives"][0]]

        result = self._validate(inherit)
        self.assertEqual([], result.errors)

    def test_inherit_mode_requires_source(self) -> None:
        def inherit_without_source(data):
            screen = data["screens"][0]
            screen["exploration_mode"] = "inherit"
            screen["alternatives"] = [screen["alternatives"][0]]

        result = self._validate(inherit_without_source)
        self.assertTrue(any("inherited_from" in error for error in result.errors))

    def test_high_risk_screen_must_compare_alternatives(self) -> None:
        def inherit_high_risk(data):
            screen = data["screens"][1]
            screen["exploration_mode"] = "inherit"
            screen["inherited_from"] = "既存の確認画面"
            screen["alternatives"] = [screen["alternatives"][0]]

        result = self._validate(inherit_high_risk)
        self.assertTrue(any("risk: high" in error and "compare" in error for error in result.errors))

    def test_alternative_ids_must_be_unique(self) -> None:
        result = self._validate(
            lambda d: d["screens"][0]["alternatives"][1].__setitem__(
                "id", d["screens"][0]["alternatives"][0]["id"]
            )
        )
        self.assertTrue(any("alternatives" in error and "重複" in error for error in result.errors))

    def test_state_strategy_allows_risk_focused_subset_of_five_states(self) -> None:
        result = self._validate(
            lambda d: d["screens"][0].__setitem__(
                "state_strategy",
                {"priority_states": ["error"], "rationale": "失敗時の復旧を重点確認する"},
            )
        )
        self.assertEqual([], result.errors)

    def test_state_strategy_rejects_unknown_state(self) -> None:
        result = self._validate(
            lambda d: d["screens"][0]["state_strategy"].__setitem__("priority_states", ["expired"])
        )
        self.assertTrue(any("expired" in error for error in result.errors))

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

    def test_disallowed_state_value_is_error(self) -> None:
        result = self._validate(
            lambda d: d["screens"][0]["blocks"][2].__setitem__("state", "invalid-state")
        )
        self.assertTrue(any("invalid-state" in error for error in result.errors))

    def test_empty_state_without_state_is_error(self) -> None:
        result = self._validate(lambda d: d["screens"][0]["blocks"][2].pop("state"))
        self.assertTrue(any("empty-state" in error and "state" in error for error in result.errors))

    def test_header_with_state_is_error(self) -> None:
        result = self._validate(lambda d: d["screens"][0]["blocks"][0].__setitem__("state", "empty"))
        self.assertTrue(any("header" in error and "状態表現部品ではない" in error for error in result.errors))

    def test_empty_state_with_error_state_is_combination_error(self) -> None:
        result = self._validate(lambda d: d["screens"][0]["blocks"][2].__setitem__("state", "error"))
        self.assertTrue(any("empty-state" in error and "表せません" in error for error in result.errors))

    def test_state_without_matching_block_is_error(self) -> None:
        def mutate(d: dict) -> None:
            d["screens"][0]["blocks"] = [
                b for b in d["screens"][0]["blocks"] if b.get("type") != "empty-state"
            ]

        result = self._validate(mutate)
        self.assertTrue(any("states.empty" in error for error in result.errors))

    def test_empty_trace_is_warning_not_error(self) -> None:
        result = self._validate(lambda d: d["screens"][0].__setitem__("trace", []))
        self.assertEqual([], result.errors)
        self.assertTrue(any("trace" in warning for warning in result.warnings))

    def test_null_trace_is_error(self) -> None:
        """`trace:` と値を省いた書き方はNoneになり、レンダラが落ちるためエラーにする。"""

        result = self._validate(lambda d: d["screens"][0].__setitem__("trace", None))
        self.assertTrue(any("trace" in error for error in result.errors))

    def test_entry_screen_must_exist(self) -> None:
        result = self._validate(lambda d: d["meta"].__setitem__("entry_screens", ["SC-999"]))
        self.assertTrue(any("SC-999" in error for error in result.errors))

    def test_missing_meta_phase_is_error(self) -> None:
        result = self._validate(lambda d: d["meta"].pop("phase"))
        self.assertTrue(any("phase" in error for error in result.errors))

    def test_missing_meta_source_spec_is_error(self) -> None:
        result = self._validate(lambda d: d["meta"].pop("source_spec"))
        self.assertTrue(any("source_spec" in error for error in result.errors))

    def test_missing_meta_generated_at_is_error(self) -> None:
        result = self._validate(lambda d: d["meta"].pop("generated_at"))
        self.assertTrue(any("generated_at" in error for error in result.errors))

    def test_blank_meta_phase_is_error(self) -> None:
        """レビュー指摘の再現: 空白のみのphaseが非空文字として通過していた。"""

        result = self._validate(lambda d: d["meta"].__setitem__("phase", "   "))
        self.assertTrue(any("phase" in error for error in result.errors))

    def test_blank_meta_source_spec_is_error(self) -> None:
        result = self._validate(lambda d: d["meta"].__setitem__("source_spec", "   "))
        self.assertTrue(any("source_spec" in error for error in result.errors))

    def test_malformed_generated_at_is_error(self) -> None:
        """レビュー指摘の再現: 2026-99-99（存在しない日付）がエラーにならなかった。"""

        result = self._validate(lambda d: d["meta"].__setitem__("generated_at", "2026-99-99"))
        self.assertTrue(any("generated_at" in error for error in result.errors))

    def test_generated_at_not_matching_pattern_is_error(self) -> None:
        result = self._validate(lambda d: d["meta"].__setitem__("generated_at", "2026/07/30"))
        self.assertTrue(any("generated_at" in error for error in result.errors))

    def test_valid_generated_at_passes(self) -> None:
        result = self._validate(lambda d: d["meta"].__setitem__("generated_at", "2026-07-30"))
        self.assertEqual([], result.errors)

    def test_meta_with_only_entry_screens_has_three_errors(self) -> None:
        """レビュー指摘の再現: entry_screensしかないmetaが警告・エラーとも0件で通っていた。"""

        result = self._validate(lambda d: d.__setitem__("meta", {"entry_screens": ["SC-001"]}))
        self.assertTrue(any("phase" in error for error in result.errors))
        self.assertTrue(any("source_spec" in error for error in result.errors))
        self.assertTrue(any("generated_at" in error for error in result.errors))


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
            lambda d: d["screens"][0]["transitions"].append({"action": "詳細", "to": "SC-404", "kind": "forward"})
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
            d["screens"][1]["transitions"] = [{"action": "再読込", "to": "SC-002", "kind": "forward"}]
            d["screens"][1].pop("terminal")

        result = self._validate(mutate)
        self.assertTrue(any("SC-002" in error and "自分自身" in error for error in result.errors))


class StateAndFieldTest(unittest.TestCase):
    def _states(self, mutate=None) -> "GATE.Result":
        data = copy.deepcopy(VALID)
        if mutate:
            mutate(data)
        return GATE.validate_states(data)

    def _fields(self, mutate=None) -> "GATE.Result":
        data = copy.deepcopy(VALID)
        if mutate:
            mutate(data)
        return GATE.validate_fields(data)

    def test_all_states_present_passes(self) -> None:
        self.assertEqual([], self._states().errors)

    def test_missing_state_key_is_error(self) -> None:
        result = self._states(lambda d: d["screens"][0]["states"].pop("loading"))
        self.assertTrue(any("loading" in error for error in result.errors))

    def test_empty_state_value_is_error(self) -> None:
        result = self._states(lambda d: d["screens"][0]["states"].__setitem__("error", ""))
        self.assertTrue(any("error" in message for message in result.errors))

    def test_not_applicable_needs_reason(self) -> None:
        result = self._states(lambda d: d["screens"][0]["states"].__setitem__("forbidden", "該当なし"))
        self.assertTrue(any("理由" in error for error in result.errors))

    def test_not_applicable_with_reason_passes(self) -> None:
        result = self._states(
            lambda d: d["screens"][0]["states"].__setitem__("forbidden", "該当なし: 全員が閲覧できる画面のため")
        )
        self.assertEqual([], result.errors)

    def test_complete_fields_have_no_warning(self) -> None:
        self.assertEqual([], self._fields().warnings)

    def test_required_field_without_error_message_is_warning(self) -> None:
        result = self._fields(lambda d: d["screens"][1]["blocks"][1]["fields"][0].pop("error"))
        self.assertEqual([], result.errors)
        self.assertTrue(any("[要確認]" in warning and "連絡先" in warning for warning in result.warnings))

    def test_required_field_without_constraint_is_warning(self) -> None:
        result = self._fields(lambda d: d["screens"][1]["blocks"][1]["fields"][0].pop("constraint"))
        self.assertTrue(any("[要確認]" in warning for warning in result.warnings))

    def test_field_without_required_flag_is_error(self) -> None:
        result = self._fields(lambda d: d["screens"][1]["blocks"][1]["fields"][0].pop("required"))
        self.assertTrue(any("required" in error for error in result.errors))

    def test_form_section_without_fields_is_error(self) -> None:
        result = self._fields(lambda d: d["screens"][1]["blocks"][1].pop("fields"))
        self.assertTrue(any("fields" in error for error in result.errors))


class ValidateAllTest(unittest.TestCase):
    def test_valid_definition_passes_every_check(self) -> None:
        result = GATE.validate_all(copy.deepcopy(VALID), CATALOG.load_catalog())
        self.assertEqual([], result.errors)
        self.assertTrue(result.ok())

    def test_template_placeholders_fail_even_after_generated_at_is_filled(self) -> None:
        """日付だけを埋めても、画面判断の仮値が残ればゲートを通さない。"""
        import yaml

        template = SCRIPT_DIR.parent / "templates" / "screens-template.yaml"
        data = yaml.safe_load(template.read_text(encoding="utf-8"))
        data["meta"]["generated_at"] = "2026-07-30"
        result = GATE.validate_all(data, CATALOG.load_catalog())
        self.assertTrue(any("仮値" in error for error in result.errors))

    def test_unfilled_template_generated_at_fails_gate(self) -> None:
        """テンプレートをそのままコピーして置換を忘れても、ゲートが必ず弾くことを保証する。"""

        import yaml

        template = SCRIPT_DIR.parent / "templates" / "screens-template.yaml"
        data = yaml.safe_load(template.read_text(encoding="utf-8"))
        result = GATE.validate_all(data, CATALOG.load_catalog())
        self.assertTrue(any("generated_at" in error for error in result.errors))

    def test_template_covers_the_error_layout_with_a_stateful_alert(self) -> None:
        """error レイアウトは alert 必須、alert は state 必須。この組み合わせを見本で通す。"""

        import yaml

        template = SCRIPT_DIR.parent / "templates" / "screens-template.yaml"
        data = yaml.safe_load(template.read_text(encoding="utf-8"))
        error_screens = [s for s in data["screens"] if s.get("layout") == "error"]
        self.assertTrue(error_screens, "layout: error の見本画面がテンプレートにありません")
        for screen in error_screens:
            alerts = [b for b in screen["blocks"] if b.get("type") == "alert"]
            self.assertTrue(alerts)
            for alert in alerts:
                self.assertIn(alert.get("state"), ("error", "forbidden"))


if __name__ == "__main__":
    unittest.main()
