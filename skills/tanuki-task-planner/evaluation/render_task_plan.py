#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
import yaml

def cell(value: object) -> str:
    return "<br>".join(value) if isinstance(value, list) else str(value)

def main() -> None:
    parser = argparse.ArgumentParser(description="タスク計画をMarkdownへ出力")
    parser.add_argument("plan", type=Path); parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(); data = yaml.safe_load(args.plan.read_text(encoding="utf-8"))
    lines = ["# 実装タスク計画", "", f"対象リリース: {data['release']}", "", "| ID | タスク | 種別 | 要件 | 依存 | 完了条件 | 検証 |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for task in data["tasks"]:
        if task.get("status") == "in_scope":
            lines.append("| " + " | ".join(cell(task.get(key, "")) for key in ("id", "title", "type", "requirement_ids", "depends_on", "definition_of_done", "verification")) + " |")
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")

if __name__ == "__main__": main()
