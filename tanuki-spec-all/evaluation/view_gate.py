#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""サマリ層（00_サマリ.md）が正本からズレていないかを検証する。

文章表現は検査しない。凝縮した書き方はAIの裁量に委ね、IDの実在性・網羅性・
状態の一致だけを機械が担保する（設計書 2026-07-19 §5.1）。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML が必要です: python3 -m pip install -r requirements.txt")

# 先頭の否定後読みは `P1-FR-107` から `FR-107` を誤抽出しないため。soil-groove の
# 要件定義書には Phase接頭辞つきのIDが実在し、`\b` だけでは途中から拾ってしまう。
ID_RE = re.compile(r"(?<![\w-])(?:US|BR|FR|NFR|AC|ST)-\d{3,}\b")
# 網羅を求めるのは対象確定の要件だけ。draft と対象外はサマリに書かなくてよい。
REQUIRED_IN_VIEW = {"in_scope"}
STATE_FIELDS = ("implementation_status", "gap_severity")


def known_ids(data: dict) -> set[str]:
    result: set[str] = set()
    for key in ("user_stories", "business_flows", "requirements", "acceptance_tests", "system_tests"):
        for record in data.get(key) or []:
            if isinstance(record, dict) and isinstance(record.get("id"), str):
                result.add(record["id"])
    return result


def table_row(view_text: str, identifier: str) -> str | None:
    """IDを含む最初の表行を返す。散文中の言及は拾わない。"""
    pattern = re.compile(rf"\b{re.escape(identifier)}\b")
    for line in view_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("|") and pattern.search(stripped):
            return stripped
    return None


def table_cells(row: str) -> list[str]:
    """表の行をセルへ分解する。前後の | と余白を落とす。"""
    return [cell.strip() for cell in row.strip().strip("|").split("|")]


def validate(view_text: str, data: dict) -> list[str]:
    failures: list[str] = []
    known = known_ids(data)
    used = set(ID_RE.findall(view_text))

    for identifier in sorted(used - known):
        failures.append(f"サマリに正本へ存在しないIDがあります: {identifier}")

    for requirement in data.get("requirements") or []:
        if not isinstance(requirement, dict):
            continue
        identifier = requirement.get("id")
        if not isinstance(identifier, str):
            continue
        if requirement.get("status") not in REQUIRED_IN_VIEW:
            continue
        if identifier not in used:
            failures.append(f"サマリに要件が載っていません: {identifier}")
            continue
        row = table_row(view_text, identifier)
        cells = table_cells(row) if row is not None else []
        matched_cells: set[int] = set()
        for field in STATE_FIELDS:
            expected = requirement.get(field)
            if expected is None:
                continue
            if row is None:
                failures.append(f"{identifier}: {field} を持つ要件は表の行で書いてください")
                break
            hits = [i for i, cell in enumerate(cells) if cell == str(expected) and i not in matched_cells]
            if not hits:
                failures.append(
                    f"{identifier}: {field} が正本と一致しません（正本={expected}、サマリの行={row}）"
                )
                continue
            matched_cells.add(hits[0])
    return failures


def load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("トレーサビリティ正本はYAMLオブジェクトで指定してください")
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="サマリ層と正本の整合を検証")
    parser.add_argument("view", type=Path, help="00_サマリ.md のパス")
    parser.add_argument("--traceability", type=Path, required=True, help="traceability.yaml のパス")
    parser.add_argument("--json", action="store_true", help="JSONで出力")
    args = parser.parse_args()
    try:
        failures = validate(args.view.read_text(encoding="utf-8"), load(args.traceability))
    except (OSError, ValueError, yaml.YAMLError) as error:
        failures = [f"読み込めません: {error}"]
    report = {"gate_passed": not failures, "failures": failures}
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("ビュー整合ゲート: " + ("通過" if not failures else "不通過"))
        for failure in failures:
            print(f"- {failure}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
