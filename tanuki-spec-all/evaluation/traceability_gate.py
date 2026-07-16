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


STATUS_VALUES = {"in_scope", "deferred", "out_of_scope"}
ID_PATTERNS = {
    "user_stories": re.compile(r"^US-\d{3,}$"),
    "business_flows": re.compile(r"^BF-\d{3,}$"),
    "requirements": re.compile(r"^(?:BR|FR|NFR)-\d{3,}$"),
    "acceptance_tests": re.compile(r"^AC-\d{3,}$"),
    "system_tests": re.compile(r"^ST-\d{3,}$"),
    "flow_steps": re.compile(r"^BF-\d{3,}-S\d{2,}$"),
}
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
        failures.append(f"{label} {identifier}: status は in_scope/deferred/out_of_scope で指定してください")
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
    business_flows = records(data, "business_flows", failures)
    requirements = records(data, "requirements", failures)
    acceptance_tests = records(data, "acceptance_tests", failures)
    system_tests = records(data, "system_tests", failures)

    users = index_by_id(user_stories, "user_stories", "ユーザーストーリー", failures)
    flows = index_by_id(business_flows, "business_flows", "業務フロー", failures)
    reqs = index_by_id(requirements, "requirements", "要件", failures)
    acceptances = index_by_id(acceptance_tests, "acceptance_tests", "受入試験", failures)
    systems = index_by_id(system_tests, "system_tests", "システムテスト", failures)

    flow_steps: dict[str, dict] = {}
    for flow_id, flow in flows.items():
        if not validate_status(flow, "業務フロー", failures):
            continue
        require_text(flow, "name", "業務フロー", failures)
        steps = flow.get("steps")
        if not isinstance(steps, list) or not steps:
            failures.append(f"業務フロー {flow_id}: steps は1件以上必要です")
            continue
        for step in steps:
            if not isinstance(step, dict):
                failures.append(f"業務フロー {flow_id}: steps の要素はオブジェクトで指定してください")
                continue
            step_id = step.get("id")
            if not nonempty_text(step_id) or not ID_PATTERNS["flow_steps"].fullmatch(step_id):
                failures.append(f"業務フロー {flow_id}: 手順IDの形式が不正です")
                continue
            if not step_id.startswith(f"{flow_id}-"):
                failures.append(f"業務フロー {flow_id}: 手順ID {step_id} は業務フローIDで始めてください")
            if step_id in flow_steps:
                failures.append(f"業務フロー手順 {step_id}: IDが重複しています")
            # 手順の対象状態は親業務フローに従う。
            flow_steps[step_id] = {**step, "status": flow["status"]}
            require_text(step, "action", "業務フロー手順", failures)
            validate_references(step, "user_story_ids", users, "業務フロー手順", "ユーザーストーリー", failures)

    for story in users.values():
        if validate_status(story, "ユーザーストーリー", failures):
            require_text(story, "statement", "ユーザーストーリー", failures)

    requirement_story_links: dict[str, set[str]] = {key: set() for key in users}
    requirement_step_links: dict[str, set[str]] = {key: set() for key in flow_steps}
    acceptance_story_links: dict[str, set[str]] = {key: set() for key in users}
    acceptance_step_links: dict[str, set[str]] = {key: set() for key in flow_steps}
    acceptance_requirement_links: dict[str, set[str]] = {key: set() for key in reqs}
    system_requirement_links: dict[str, set[str]] = {key: set() for key in reqs}
    system_acceptance_links: dict[str, set[str]] = {key: set() for key in acceptances}
    requirement_targets: dict[str, dict[str, set[str]]] = {}
    acceptance_targets: dict[str, dict[str, set[str]]] = {}

    for requirement in reqs.values():
        if not validate_status(requirement, "要件", failures):
            continue
        require_text(requirement, "statement", "要件", failures)
        if requirement.get("type") not in REQUIREMENT_TYPES:
            failures.append(f"要件 {requirement.get('id', '<IDなし>')}: type は business/functional/non_functional で指定してください")
        story_ids = validate_references(requirement, "user_story_ids", users, "要件", "ユーザーストーリー", failures)
        step_ids = validate_references(requirement, "flow_step_ids", flow_steps, "要件", "業務フロー手順", failures)
        requirement_targets[requirement["id"]] = {"stories": set(story_ids), "steps": set(step_ids)}
        flow_story_ids = set().union(*(set(flow_steps[step_id].get("user_story_ids", [])) for step_id in step_ids)) if step_ids else set()
        if story_ids and step_ids and not set(story_ids) & flow_story_ids:
            failures.append(f"要件 {requirement['id']}: 対象USと関連業務フロー手順の対象USが対応していません")
        for story_id in story_ids:
            requirement_story_links[story_id].add(requirement["id"])
        for step_id in step_ids:
            requirement_step_links[step_id].add(requirement["id"])

    for acceptance in acceptances.values():
        if not validate_status(acceptance, "受入試験", failures):
            continue
        validate_scenario(acceptance, failures)
        story_ids = validate_references(acceptance, "user_story_ids", users, "受入試験", "ユーザーストーリー", failures)
        requirement_ids = validate_references(acceptance, "requirement_ids", reqs, "受入試験", "要件", failures)
        step_ids = validate_references(acceptance, "flow_step_ids", flow_steps, "受入試験", "業務フロー手順", failures)
        acceptance_targets[acceptance["id"]] = {"stories": set(story_ids), "requirements": set(requirement_ids), "steps": set(step_ids)}
        flow_story_ids = set().union(*(set(flow_steps[step_id].get("user_story_ids", [])) for step_id in step_ids)) if step_ids else set()
        if story_ids and step_ids and not set(story_ids) & flow_story_ids:
            failures.append(f"受入試験 {acceptance['id']}: 対象USと対象業務フロー手順の対象USが対応していません")
        for story_id in story_ids:
            acceptance_story_links[story_id].add(acceptance["id"])
        for requirement_id in requirement_ids:
            acceptance_requirement_links[requirement_id].add(acceptance["id"])
            requirement_target = requirement_targets.get(requirement_id, {"stories": set(), "steps": set()})
            if not acceptance_targets[acceptance["id"]]["stories"] & requirement_target["stories"]:
                failures.append(f"受入試験 {acceptance['id']}: 要件 {requirement_id} と対象USが対応していません")
            if not acceptance_targets[acceptance["id"]]["steps"] & requirement_target["steps"]:
                failures.append(f"受入試験 {acceptance['id']}: 要件 {requirement_id} と対象業務フロー手順が対応していません")
        for step_id in step_ids:
            acceptance_step_links[step_id].add(acceptance["id"])

    for system in systems.values():
        if not validate_status(system, "システムテスト", failures):
            continue
        if system.get("test_type") not in SYSTEM_TEST_TYPES:
            failures.append(f"システムテスト {system.get('id', '<IDなし>')}: test_type が不正です")
        for field in ("preconditions", "steps", "expected_results"):
            require_list(system, field, "システムテスト", failures)
        requirement_ids = validate_references(system, "requirement_ids", reqs, "システムテスト", "要件", failures)
        acceptance_ids = validate_references(system, "acceptance_test_ids", acceptances, "システムテスト", "受入試験", failures)
        for requirement_id in requirement_ids:
            system_requirement_links[requirement_id].add(system["id"])
        for acceptance_id in acceptance_ids:
            system_acceptance_links[acceptance_id].add(system["id"])
            acceptance_requirement_ids = acceptance_targets.get(acceptance_id, {"requirements": set()})["requirements"]
            if not set(requirement_ids) & acceptance_requirement_ids:
                failures.append(f"システムテスト {system['id']}: 受入試験 {acceptance_id} と対象要件が対応していません")

    for story_id, story in users.items():
        if story.get("status") == "in_scope" and not requirement_story_links[story_id]:
            failures.append(f"ユーザーストーリーが孤立しています: {story_id} を満たす要件がありません")
        if story.get("status") == "in_scope" and not acceptance_story_links[story_id]:
            failures.append(f"ユーザーストーリーが孤立しています: {story_id} の受入試験がありません")
    for step_id in flow_steps:
        if not requirement_step_links[step_id]:
            failures.append(f"業務フロー手順が孤立しています: {step_id} を満たす要件がありません")
        if not acceptance_step_links[step_id]:
            failures.append(f"業務フロー手順が孤立しています: {step_id} の受入試験がありません")
    for requirement_id, requirement in reqs.items():
        if requirement.get("status") == "in_scope" and not acceptance_requirement_links[requirement_id]:
            failures.append(f"要件が孤立しています: {requirement_id} の受入試験がありません")
        if requirement.get("status") == "in_scope" and not system_requirement_links[requirement_id]:
            failures.append(f"要件が孤立しています: {requirement_id} のシステムテストがありません")
    for acceptance_id, acceptance in acceptances.items():
        if acceptance.get("status") == "in_scope" and not system_acceptance_links[acceptance_id]:
            failures.append(f"受入試験が孤立しています: {acceptance_id} のシステムテストがありません")
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
