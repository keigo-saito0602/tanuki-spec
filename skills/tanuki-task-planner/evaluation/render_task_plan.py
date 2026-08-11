#!/usr/bin/env python3
from __future__ import annotations
import argparse
import re
from pathlib import Path
import yaml

TYPE_ORDER = ("design", "data", "backend", "frontend", "integration", "test", "verification", "documentation")
MERMAID_UNSAFE = re.compile(r'["\[\]()|\n]')


def sanitize(text: str) -> str:
    """Mermaidのノード定義・矢印記法と衝突する文字を取り除く。"""
    return MERMAID_UNSAFE.sub("", str(text))


def cell(value: object) -> str:
    return "<br>".join(value) if isinstance(value, list) else str(value)


def in_scope_tasks(tasks: list[dict]) -> list[dict]:
    return [task for task in tasks if task.get("status") == "in_scope"]


def is_workable(task: dict, indexed: dict[str, dict]) -> bool:
    progress = task.get("progress")
    if progress not in (None, "todo"):
        return False
    for dep in task.get("depends_on") or []:
        if indexed.get(dep, {}).get("progress") != "done":
            return False
    return True


def render_workable_list(tasks: list[dict]) -> list[str]:
    scoped = in_scope_tasks(tasks)
    indexed = {task["id"]: task for task in scoped}
    workable = [task for task in scoped if is_workable(task, indexed)]
    lines = ["## 着手可能なタスク", ""]
    if not workable:
        lines.append("着手可能なタスクはありません")
    else:
        for task in workable:
            lines.append(f"- {task['id']} {sanitize(task.get('title', ''))}")
    lines.append("")
    return lines


def render_mindmap(tasks: list[dict], release: str) -> list[str]:
    scoped = in_scope_tasks(tasks)
    grouped: dict[str, list[dict]] = {}
    for task in scoped:
        grouped.setdefault(task.get("type", "その他"), []).append(task)
    lines = ["## WBS", "", "```mermaid", "mindmap", f"  root(({sanitize(release)}))"]
    for type_name in TYPE_ORDER:
        group = grouped.pop(type_name, None)
        if not group:
            continue
        lines.append(f"    {type_name}")
        for task in group:
            lines.append(f"      {task['id']} {sanitize(task.get('title', ''))}")
    for type_name, group in grouped.items():
        lines.append(f"    {sanitize(type_name)}")
        for task in group:
            lines.append(f"      {task['id']} {sanitize(task.get('title', ''))}")
    lines += ["```", ""]
    return lines


def render_flowchart(tasks: list[dict]) -> list[str]:
    scoped = in_scope_tasks(tasks)
    lines = ["## 依存関係", "", "```mermaid", "flowchart TD"]
    for task in scoped:
        lines.append(f"  {task['id']}[{sanitize(task.get('title', ''))}]")
    for task in scoped:
        for dep in task.get("depends_on") or []:
            lines.append(f"  {dep} --> {task['id']}")
    lines += ["```", ""]
    return lines


def render_gantt_or_reason(tasks: list[dict]) -> list[str]:
    scoped = in_scope_tasks(tasks)
    dated = [task for task in scoped if task.get("start_date")]
    lines = ["## ガント", ""]
    if not dated:
        lines += ["start_date が未設定のためガントを生成しません", ""]
        return lines
    missing_duration = sorted(task["id"] for task in scoped if not task.get("duration"))
    if missing_duration:
        lines += [f"duration が未設定のタスクがあるためガントを生成しません: {', '.join(missing_duration)}", ""]
        return lines
    durationed = {task["id"] for task in scoped if task.get("duration")}
    lines += ["```mermaid", "gantt"]
    for task in scoped:
        duration = task.get("duration")
        if not duration:
            continue
        start_date = task.get("start_date")
        deps = [dep for dep in (task.get("depends_on") or []) if dep in durationed]
        if start_date:
            schedule = start_date
        elif deps:
            schedule = "after " + " ".join(deps)
        else:
            continue
        lines.append(f"  {sanitize(task.get('title', ''))} :{task['id']}, {schedule}, {duration}")
    lines += ["```", ""]
    return lines


def render_table(tasks: list[dict]) -> list[str]:
    lines = ["## タスク一覧", "", "| ID | タスク | 種別 | 要件 | 依存 | 完了条件 | 検証 |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for task in in_scope_tasks(tasks):
        lines.append("| " + " | ".join(cell(task.get(key, "")) for key in ("id", "title", "type", "requirement_ids", "depends_on", "definition_of_done", "verification")) + " |")
    return lines


def build_document(data: dict) -> str:
    tasks = data.get("tasks") or []
    lines = ["# 実装タスク計画", "", f"対象リリース: {data['release']}", ""]
    lines += render_workable_list(tasks)
    lines += render_mindmap(tasks, data["release"])
    lines += render_flowchart(tasks)
    lines += render_gantt_or_reason(tasks)
    lines += render_table(tasks)
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="タスク計画をMarkdownへ出力")
    parser.add_argument("plan", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = yaml.safe_load(args.plan.read_text(encoding="utf-8"))
    args.output.write_text(build_document(data), encoding="utf-8")


if __name__ == "__main__":
    main()
