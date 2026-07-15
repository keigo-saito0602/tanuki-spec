#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""design-traceability.yaml から要件と設計の対応表を生成する。"""
from __future__ import annotations

import argparse
from pathlib import Path

import design_traceability_gate


def cell(value: object) -> str:
    return "<br>".join(map(cell, value)) if isinstance(value, list) else str(value).replace("|", "\\|").replace("\n", "<br>")


def render(data: dict, requirements: dict[str, dict]) -> str:
    rows = []
    for element in data["design_elements"]:
        for requirement_id in element["requirement_ids"]:
            requirement = requirements.get(requirement_id, {})
            rows.append([requirement_id, requirement.get("type", ""), requirement.get("statement", ""), element["id"], element["type"], element["name"]])
    lines = ["# 設計トレーサビリティ一覧", "", "| 要件ID | 種別 | 要件 | 設計要素ID | 設計工程 | 設計要素 |", "| --- | --- | --- | --- | --- | --- |"]
    lines.extend("| " + " | ".join(cell(value) for value in row) + " |" for row in rows)
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="設計トレーサビリティ正本から対応表を生成")
    parser.add_argument("design_traceability", type=Path, help="design-traceability.yaml のパス")
    parser.add_argument("--output-dir", type=Path, required=True, help="生成先ディレクトリ")
    parser.add_argument("--check", action="store_true", help="生成物との差分だけを検証する")
    args = parser.parse_args()
    data = design_traceability_gate.load(args.design_traceability)
    requirements, failures = design_traceability_gate.requirement_index(design_traceability_gate.requirements_path(data, args.design_traceability))
    failures.extend(design_traceability_gate.validate(data, requirements))
    if failures:
        raise SystemExit("設計トレーサビリティゲート不通過のため帳票を生成できません: " + " / ".join(failures))
    output = args.output_dir / "design-traceability.md"
    content = render(data, requirements)
    if args.check:
        if not output.exists() or output.read_text(encoding="utf-8") != content:
            raise SystemExit(f"設計トレーサビリティ帳票が正本と不一致です: {output}")
        print(f"検証: {args.output_dir}")
        return
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    print(f"生成: {output}")


if __name__ == "__main__":
    main()
