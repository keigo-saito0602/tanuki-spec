from __future__ import annotations

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evaluation"))
import view_gate


def traceability(**overrides) -> dict:
    data = {
        "version": "1.0",
        "user_stories": [{"id": "US-101", "status": "in_scope", "statement": "予約したい"}],
        "requirements": [
            {"id": "FR-101", "status": "in_scope", "type": "functional", "statement": "予約を作成する"},
            {"id": "FR-102", "status": "in_scope", "type": "functional", "statement": "予約を取り消す"},
        ],
        "acceptance_tests": [{"id": "AC-101", "status": "in_scope"}],
    }
    data.update(overrides)
    return data


COMPLETE_VIEW = """# Phase 1 サマリ

## ユーザーストーリー
正本は traceability.yaml の US-101。

## 機能要件
| ID | 要件 | 実装 | 乖離 |
| --- | --- | --- | --- |
| FR-101 | 予約を作成する | implemented | none |
| FR-102 | 予約を取り消す | partial | minor |

## 受け入れ条件
AC-101 を満たす。
"""


class ExistenceTest(unittest.TestCase):
    def test_unknown_id_is_rejected(self):
        view = COMPLETE_VIEW + "\n未知の要件 FR-999 に対応する。\n"
        failures = view_gate.validate(view, traceability())
        self.assertTrue(any("FR-999" in failure for failure in failures))

    def test_phase_prefixed_id_is_not_split(self):
        """`P1-FR-107` から `FR-107` を誤抽出しない。soil-groove に実在する表記。"""
        view = COMPLETE_VIEW + "\nP1-FR-107 はカレンダー導線。\n"
        failures = view_gate.validate(view, traceability())
        self.assertEqual(failures, [], f"Phase接頭辞つきIDを分解して誤検出している: {failures}")

    def test_complete_view_passes(self):
        self.assertEqual(view_gate.validate(COMPLETE_VIEW, traceability()), [])


class CoverageTest(unittest.TestCase):
    def test_missing_in_scope_requirement_is_rejected(self):
        view = COMPLETE_VIEW.replace("| FR-102 | 予約を取り消す | partial | minor |\n", "")
        failures = view_gate.validate(view, traceability())
        self.assertTrue(any("FR-102" in failure for failure in failures))

    def test_draft_requirement_is_not_required_in_view(self):
        data = traceability()
        data["requirements"].append(
            {"id": "FR-401", "status": "draft", "reason": "構想段階", "type": "functional", "statement": "未確定"}
        )
        self.assertEqual(view_gate.validate(COMPLETE_VIEW, data), [])

    def test_out_of_scope_requirement_is_not_required_in_view(self):
        data = traceability()
        data["requirements"].append(
            {"id": "FR-501", "status": "out_of_scope", "reason": "対象外", "type": "functional", "statement": "対象外"}
        )
        self.assertEqual(view_gate.validate(COMPLETE_VIEW, data), [])


class StateConsistencyTest(unittest.TestCase):
    def test_mismatched_implementation_status_is_rejected(self):
        data = traceability()
        data["requirements"][0]["implementation_status"] = "partial"  # ビューは implemented
        failures = view_gate.validate(COMPLETE_VIEW, data)
        self.assertTrue(any("FR-101" in f and "implementation_status" in f for f in failures))

    def test_mismatched_gap_severity_is_rejected(self):
        """gap_severity も implementation_status と同じ強さで照合する。"""
        data = traceability()
        data["requirements"][1]["gap_severity"] = "critical"  # ビューは minor
        failures = view_gate.validate(COMPLETE_VIEW, data)
        self.assertTrue(any("FR-102" in f and "gap_severity" in f for f in failures))

    def test_matching_state_passes(self):
        data = traceability()
        data["requirements"][0]["implementation_status"] = "implemented"
        data["requirements"][0]["gap_severity"] = "none"
        self.assertEqual(view_gate.validate(COMPLETE_VIEW, data), [])

    def test_state_requires_a_table_row(self):
        """状態を持つ要件が散文だけで書かれていたら落とす。"""
        data = traceability()
        data["requirements"][1]["implementation_status"] = "partial"
        view = COMPLETE_VIEW.replace("| FR-102 | 予約を取り消す | partial | minor |", "") + "\nFR-102 は取消機能。\n"
        failures = view_gate.validate(view, data)
        self.assertTrue(any("FR-102" in f and "表" in f for f in failures))

    def test_requirement_without_state_skips_the_check(self):
        self.assertEqual(view_gate.validate(COMPLETE_VIEW, traceability()), [])

    def test_state_word_in_another_column_does_not_count_as_match(self):
        """備考列に状態語が偶然含まれても、乖離列の不一致を見逃さない。"""
        data = traceability()
        data["requirements"][0]["implementation_status"] = "implemented"
        data["requirements"][0]["gap_severity"] = "critical"
        view = (
            "# サマリ\n"
            "| ID | 要件 | 実装 | 乖離 | 備考 |\n"
            "| --- | --- | --- | --- | --- |\n"
            "| FR-101 | 予約を作成する | implemented | minor | critical な影響が出うる |\n"
            "| FR-102 | 予約を取り消す | partial | minor | |\n"
        )
        failures = view_gate.validate(view, data)
        self.assertTrue(
            any("FR-101" in f and "gap_severity" in f for f in failures),
            f"備考列の語で不一致を見逃している: {failures}",
        )

    def test_exact_cell_match_is_required(self):
        """セルが期待値を含むだけでは一致とみなさない。"""
        data = traceability()
        data["requirements"][0]["gap_severity"] = "none"
        view = (
            "# サマリ\n"
            "| ID | 要件 | 実装 | 乖離 |\n"
            "| --- | --- | --- | --- |\n"
            "| FR-101 | 予約を作成する | implemented | none 相当 |\n"
            "| FR-102 | 予約を取り消す | partial | minor |\n"
        )
        failures = view_gate.validate(view, data)
        self.assertTrue(any("FR-101" in f and "gap_severity" in f for f in failures))
