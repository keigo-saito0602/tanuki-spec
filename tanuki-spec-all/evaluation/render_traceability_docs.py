#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""traceability.yaml から要件対応表と試験項目書を生成する。"""
from __future__ import annotations

import argparse
from pathlib import Path

import traceability_gate


def cell(value: object) -> str:
    if isinstance(value, list):
        return "<br>".join(cell(item) for item in value)
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def table(headers: list[str], rows: list[list[object]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    lines.extend("| " + " | ".join(cell(value) for value in row) + " |" for row in rows)
    return lines


def in_scope(items: list[dict]) -> list[dict]:
    """対象外・延期は実行対象の帳票へ混在させない。"""
    return [item for item in items if item.get("status") == "in_scope"]


def render_requirements(data: dict) -> str:
    lines = ["# 要件トレーサビリティ一覧", "", "## ユーザーストーリー", ""]
    lines.extend(table(["ID", "ユーザーストーリー"], [[item["id"], item.get("statement", "")] for item in in_scope(data["user_stories"])]))
    lines.extend(["", "## 業務フロー手順", ""])
    rows = []
    for flow in in_scope(data["business_flows"]):
        for step in flow.get("steps", []):
            rows.append([step.get("id", ""), flow.get("name", ""), step.get("action", ""), step.get("user_story_ids", [])])
    lines.extend(table(["手順ID", "業務フロー", "手順", "対象US"], rows))
    lines.extend(["", "## 要件対応", ""])
    lines.extend(table(
        ["要件ID", "種別", "要件", "達成するUS", "関連フロー手順"],
        [[item["id"], item.get("type", ""), item.get("statement", ""), item.get("user_story_ids", []), item.get("flow_step_ids", [])] for item in in_scope(data["requirements"])],
    ))
    return "\n".join(lines) + "\n"


def render_acceptance(data: dict) -> str:
    lines = ["# 受入試験項目書", ""]
    rows = [[
        item["id"], item.get("user_story_ids", []), item.get("requirement_ids", []), item.get("flow_step_ids", []),
        item.get("preconditions", []), item.get("steps", []), item.get("expected_results", []),
    ] for item in in_scope(data["acceptance_tests"])]
    lines.extend(table(["ID", "対象US", "対象要件", "対象フロー手順", "前提条件", "操作", "期待結果"], rows))
    return "\n".join(lines) + "\n"


def render_system(data: dict) -> str:
    lines = ["# システムテスト項目書", ""]
    rows = [[
        item["id"], item.get("test_type", ""), item.get("requirement_ids", []), item.get("acceptance_test_ids", []),
        item.get("preconditions", []), item.get("steps", []), item.get("expected_results", []),
    ] for item in in_scope(data["system_tests"])]
    lines.extend(table(["ID", "種別", "対象要件", "対象受入試験", "前提条件", "操作", "期待結果"], rows))
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="トレーサビリティ正本から帳票を生成")
    parser.add_argument("traceability", type=Path, help="traceability.yaml のパス")
    parser.add_argument("--output-dir", type=Path, required=True, help="生成先ディレクトリ")
    parser.add_argument("--check", action="store_true", help="生成物との差分だけを検証する")
    args = parser.parse_args()
    data = traceability_gate.load(args.traceability)
    failures = traceability_gate.validate(data)
    if failures:
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit("トレーサビリティゲート不通過のため帳票を生成できません")
    outputs = {
        "requirements-traceability.md": render_requirements(data),
        "acceptance-test-cases.md": render_acceptance(data),
        "system-test-cases.md": render_system(data),
    }
    if args.check:
        mismatches = [name for name, content in outputs.items() if not (args.output_dir / name).exists() or (args.output_dir / name).read_text(encoding="utf-8") != content]
        if mismatches:
            raise SystemExit("トレーサビリティ帳票が正本と不一致です: " + ", ".join(mismatches))
        print(f"検証: {args.output_dir}")
        return
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, content in outputs.items():
        (args.output_dir / name).write_text(content, encoding="utf-8")
    print(f"生成: {args.output_dir}")


if __name__ == "__main__":
    main()
