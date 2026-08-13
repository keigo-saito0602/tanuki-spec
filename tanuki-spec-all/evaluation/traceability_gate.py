#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ユーザーストーリーから試験までの追跡性を決定論的に検証する。"""
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


# draft は「要件そのものが未確定」を表す。実装状態（implementation_status）とは別軸。
STATUS_VALUES = {"in_scope", "deferred", "out_of_scope", "draft"}
IMPLEMENTATION_STATUS_VALUES = {"implemented", "partial", "not_implemented"}
GAP_SEVERITY_VALUES = {"none", "minor", "critical"}
ID_PATTERNS = {
    "user_stories": re.compile(r"^US-\d{3,}$"),
    "business_flows": re.compile(r"^BF-\d{3,}$"),
    "requirements": re.compile(r"^(?:BR|FR|NFR)-\d{3,}$"),
    "acceptance_tests": re.compile(r"^AC-\d{3,}$"),
    "system_tests": re.compile(r"^ST-\d{3,}$"),
    "flow_steps": re.compile(r"^BF-\d{3,}-S\d{2,}$"),
}
FLOW_STEP_ID_PATTERN = re.compile(r"^BF-\d{3,}-S\d{2,}$")
REQUIREMENT_TYPES = {"business", "functional", "non_functional"}
SYSTEM_TEST_TYPES = {"functional", "integration", "non_functional", "performance", "security", "recovery", "usability"}
UNFILLED_RE = re.compile(r"<[^>]+>|\[要確認|\b(?:TODO|TBD)\b|[（(]未記入[）)]", re.IGNORECASE)


def nonempty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and not UNFILLED_RE.search(value)


def nonempty_list(value: object) -> bool:
    return isinstance(value, list) and bool(value) and all(nonempty_text(item) for item in value)


def records(data: dict, key: str, failures: list[str]) -> list[dict]:
    value = data.get(key)
    if not isinstance(value, list):
        failures.append(f"{key} は配列で指定してください")
        return []
    if not value:
        failures.append(f"{key} が空です")
    valid = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            failures.append(f"{key}[{index}] はオブジェクトで指定してください")
            continue
        valid.append(item)
    return valid


def validate_status(record: dict, label: str, failures: list[str]) -> bool:
    identifier = record.get("id", "<IDなし>")
    status = record.get("status")
    if status not in STATUS_VALUES:
        failures.append(f"{label} {identifier}: status は in_scope/deferred/out_of_scope/draft で指定してください")
        return False
    if status != "in_scope":
        if not nonempty_text(record.get("reason")):
            failures.append(f"{label} {identifier}: {status} には reason が必要です")
        return False
    return True


def index_by_id(items: list[dict], key: str, label: str, failures: list[str]) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for item in items:
        identifier = item.get("id")
        if not nonempty_text(identifier):
            failures.append(f"{label}: id が必要です")
            continue
        if not ID_PATTERNS[key].fullmatch(identifier):
            failures.append(f"{label} {identifier}: ID形式が不正です")
        if identifier in result:
            failures.append(f"{label} {identifier}: IDが重複しています")
        result[identifier] = item
    return result


def require_text(record: dict, field: str, label: str, failures: list[str]) -> None:
    if not nonempty_text(record.get(field)):
        failures.append(f"{label} {record.get('id', '<IDなし>')}: {field} が必要です")


def require_list(record: dict, field: str, label: str, failures: list[str]) -> list[str]:
    value = record.get(field)
    if not nonempty_list(value):
        failures.append(f"{label} {record.get('id', '<IDなし>')}: {field} は1件以上必要です")
        return []
    return value


def validate_optional_choice(record: dict, field: str, allowed: set[str], label: str, failures: list[str]) -> None:
    """任意フィールドを検証する。未記入は許し、書いてあるなら値を閉じた集合に限る。

    既存案件は実装状態を持たない。新規要件も実装前は書けない。よって必須にはしない。
    ただし書くなら値を固定しないと、表記ゆれを機械が検出できなくなる。
    """
    value = record.get(field)
    if value is None:
        return
    if value not in allowed:
        allowed_text = "/".join(sorted(allowed))
        failures.append(f"{label} {record.get('id', '<IDなし>')}: {field} は {allowed_text} で指定してください")


def validate_references(
    record: dict,
    field: str,
    targets: dict[str, dict],
    label: str,
    target_label: str,
    failures: list[str],
) -> list[str]:
    values = require_list(record, field, label, failures)
    valid = []
    for value in values:
        target = targets.get(value)
        if target is None:
            failures.append(f"{label} {record.get('id', '<IDなし>')}: {field} の参照先が存在しません: {value}")
            continue
        if target.get("status") != "in_scope":
            failures.append(f"{label} {record.get('id', '<IDなし>')}: {target_label} {value} は対象外または延期です")
            continue
        valid.append(value)
    return valid


def validate_scenario(acceptance: dict, failures: list[str]) -> None:
    """受入試験の Gherkin シナリオ（Given/When/Then）を検証する。"""
    identifier = acceptance.get("id", "<IDなし>")
    scenario = acceptance.get("scenario")
    if not isinstance(scenario, dict):
        failures.append(f"受入試験 {identifier}: scenario（Gherkinシナリオ）が必要です")
        return
    if not nonempty_text(scenario.get("name")):
        failures.append(f"受入試験 {identifier}: scenario.name が必要です")
    for field in ("given", "when", "then"):
        if not nonempty_list(scenario.get(field)):
            failures.append(f"受入試験 {identifier}: scenario.{field} は1件以上必要です")
    examples = scenario.get("examples")
    if examples is not None:
        if not isinstance(examples, list) or not examples or not all(isinstance(row, dict) and row for row in examples):
            failures.append(f"受入試験 {identifier}: scenario.examples は1件以上のオブジェクトで指定してください")
        else:
            expected_keys = set(examples[0])
            if any(set(row) != expected_keys for row in examples):
                failures.append(f"受入試験 {identifier}: scenario.examples の各行はキーを揃えてください")


def validate(data: dict) -> list[str]:
    """構造、参照、孤立した成果物を順に検出する。"""
    failures: list[str] = []
    if data.get("version") != "1.0":
        failures.append("version は 1.0 を指定してください")

    user_stories = records(data, "user_stories", failures)
    requirements = records(data, "requirements", failures)

    users = index_by_id(user_stories, "user_stories", "ユーザーストーリー", failures)
    reqs = index_by_id(requirements, "requirements", "要件", failures)

    for story in users.values():
        if validate_status(story, "ユーザーストーリー", failures):
            require_text(story, "statement", "ユーザーストーリー", failures)

    requirement_story_links: dict[str, set[str]] = {key: set() for key in users}

    for requirement in reqs.values():
        if not validate_status(requirement, "要件", failures):
            continue
        require_text(requirement, "statement", "要件", failures)
        validate_optional_choice(requirement, "implementation_status", IMPLEMENTATION_STATUS_VALUES, "要件", failures)
        validate_optional_choice(requirement, "gap_severity", GAP_SEVERITY_VALUES, "要件", failures)
        if requirement.get("type") not in REQUIREMENT_TYPES:
            failures.append(f"要件 {requirement.get('id', '<IDなし>')}: type は business/functional/non_functional で指定してください")
        story_ids = validate_references(requirement, "user_story_ids", users, "要件", "ユーザーストーリー", failures)
        flow_step_ids = requirement.get("flow_step_ids")
        if not isinstance(flow_step_ids, list) or not flow_step_ids or not all(
            isinstance(item, str) and FLOW_STEP_ID_PATTERN.fullmatch(item) for item in flow_step_ids
        ):
            failures.append(f"要件 {requirement.get('id', '<IDなし>')}: flow_step_ids は1件以上、BF-xxx-Sxx形式の配列で指定してください")
        for story_id in story_ids:
            requirement_story_links[story_id].add(requirement["id"])

    for story_id, story in users.items():
        if story.get("status") == "in_scope" and not requirement_story_links[story_id]:
            failures.append(f"ユーザーストーリーが孤立しています: {story_id} を満たす要件がありません")
    return failures


def load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("トレーサビリティ正本はYAMLオブジェクトで指定してください")
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="ユーザーストーリーから試験までのトレーサビリティを検証")
    parser.add_argument("traceability", type=Path, help="traceability.yaml のパス")
    parser.add_argument("--json", action="store_true", help="JSONで出力")
    args = parser.parse_args()
    try:
        failures = validate(load(args.traceability))
    except (OSError, ValueError, yaml.YAMLError) as error:
        failures = [f"トレーサビリティ正本を読み込めません: {error}"]
    report = {"gate_passed": not failures, "failures": failures}
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("トレーサビリティゲート: " + ("通過" if not failures else "不通過"))
        for failure in failures:
            print(f"- {failure}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
