#!/usr/bin/env python3
"""要件・試験への対応漏れと実装タスクの依存関係を検証する。"""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

import yaml

SHARED = Path(__file__).resolve().parents[3] / "tanuki-spec-all" / "evaluation"
sys.path.insert(0, str(SHARED))
import traceability_gate

UNFILLED = re.compile(r"<[^>]+>|\[要確認|\b(?:TODO|TBD)\b", re.I)
TASK_ID = re.compile(r"^TASK-\d{3,}$")
STATUSES = {"in_scope", "deferred", "out_of_scope"}
TYPES = {"design", "data", "backend", "frontend", "integration", "test", "verification", "documentation"}


def text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and not UNFILLED.search(value)


def values(record: dict, field: str, label: str, failures: list[str]) -> list[str]:
    value = record.get(field)
    if not isinstance(value, list) or not value or not all(text(item) for item in value):
        failures.append(f"{label}: {field} は1件以上の記入が必要です")
        return []
    return value


def validate(plan: dict, trace: dict) -> list[str]:
    failures = traceability_gate.validate(trace)
    if plan.get("version") != "1.0" or not text(plan.get("release")):
        failures.append("version: 1.0 と release が必要です")
    tasks = plan.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        return failures + ["tasks は1件以上の配列で指定してください"]
    source = {key: {item["id"] for item in trace.get(key, []) if item.get("status") == "in_scope"} for key in ("requirements", "acceptance_tests", "system_tests")}
    indexed: dict[str, dict] = {}
    covered = {key: set() for key in source}
    for index, task in enumerate(tasks):
        label = f"tasks[{index}]"
        if not isinstance(task, dict):
            failures.append(f"{label} はオブジェクトで指定してください")
            continue
        task_id = task.get("id")
        if not text(task_id) or not TASK_ID.fullmatch(task_id):
            failures.append(f"{label}: TASK-xxx形式のidが必要です")
            continue
        if task_id in indexed:
            failures.append(f"{task_id}: IDが重複しています")
        indexed[task_id] = task
        status = task.get("status")
        if status not in STATUSES:
            failures.append(f"{task_id}: status が不正です")
            continue
        if status != "in_scope":
            if not text(task.get("reason")):
                failures.append(f"{task_id}: {status} にはreasonが必要です")
            continue
        if not text(task.get("title")) or task.get("type") not in TYPES:
            failures.append(f"{task_id}: title と有効なtypeが必要です")
        for field, source_key in (("requirement_ids", "requirements"), ("acceptance_test_ids", "acceptance_tests"), ("system_test_ids", "system_tests")):
            for ref in values(task, field, task_id, failures):
                if ref not in source[source_key]:
                    failures.append(f"{task_id}: {field} の参照先が存在しないか対象外です: {ref}")
                else:
                    covered[source_key].add(ref)
        values(task, "definition_of_done", task_id, failures)
        values(task, "verification", task_id, failures)
    for task_id, task in indexed.items():
        if task.get("status") != "in_scope":
            continue
        deps = task.get("depends_on", [])
        if not isinstance(deps, list) or not all(text(dep) for dep in deps):
            failures.append(f"{task_id}: depends_on は配列で指定してください")
            continue
        for dep in deps:
            if dep not in indexed or indexed[dep].get("status") != "in_scope":
                failures.append(f"{task_id}: 依存タスクが存在しないか対象外です: {dep}")
            if dep == task_id:
                failures.append(f"{task_id}: 自分自身には依存できません")
    visiting, visited = set(), set()
    def visit(task_id: str) -> None:
        if task_id in visiting:
            failures.append(f"依存関係が循環しています: {task_id}")
            return
        if task_id in visited or task_id not in indexed:
            return
        visiting.add(task_id)
        for dep in indexed[task_id].get("depends_on", []): visit(dep)
        visiting.remove(task_id); visited.add(task_id)
    for task_id in indexed: visit(task_id)
    for key, ids in source.items():
        for identifier in sorted(ids - covered[key]):
            failures.append(f"{key} がタスクから孤立しています: {identifier}")
    return failures


def main() -> None:
    parser = argparse.ArgumentParser(description="実装タスク計画を検証")
    parser.add_argument("plan", type=Path); parser.add_argument("--traceability", type=Path, required=True)
    args = parser.parse_args()
    try:
        failures = validate(yaml.safe_load(args.plan.read_text(encoding="utf-8")), traceability_gate.load(args.traceability))
    except (OSError, ValueError, yaml.YAMLError) as error:
        failures = [f"タスク計画またはトレーサビリティ正本を読み込めません: {error}"]
    print("タスク計画ゲート: " + ("通過" if not failures else "不通過"))
    for failure in failures: print(f"- {failure}")
    if failures: raise SystemExit(1)

if __name__ == "__main__": main()
