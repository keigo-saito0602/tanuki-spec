#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""設計要素（BD/DD）とUT/ITテスト項目の追跡性を決定論的に検証する。"""
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


TEST_TYPES = {"unit", "integration"}
TEST_TYPE_ID_PATTERNS = {
    "unit": re.compile(r"^UT-\d{3,}$"),
    "integration": re.compile(r"^IT-\d{3,}$"),
}
# UT は詳細設計（DD）、IT は基本設計（BD）に紐づける。
TEST_TYPE_ELEMENT_TYPES = {"unit": "detailed_design", "integration": "basic_design"}
DESIGN_ELEMENT_PATTERNS = {
    "basic_design": re.compile(r"^BD-\d{3,}$"),
    "detailed_design": re.compile(r"^DD-\d{3,}$"),
}
REQUIREMENT_PATTERN = re.compile(r"^(?:BR|FR|NFR)-\d{3,}$")
STATUS_VALUES = {"in_scope", "deferred", "out_of_scope", "draft"}
UNFILLED_RE = re.compile(r"<[^>]+>|\[要確認|\b(?:TODO|TBD)\b|[（(]未記入[）)]", re.IGNORECASE)


def nonempty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and not UNFILLED_RE.search(value)


def nonempty_list(value: object) -> bool:
    return isinstance(value, list) and bool(value) and all(nonempty_text(item) for item in value)


def design_traceability_path(data: dict, test_traceability_path: Path) -> Path:
    value = data.get("design_traceability", "design-traceability.yaml")
    if not nonempty_text(value):
        raise ValueError("design_traceability は design-traceability.yaml への相対パスで指定してください")
    path = Path(value)
    if path.is_absolute():
        raise ValueError("design_traceability は相対パスで指定してください")
    return test_traceability_path.parent / path


def design_element_index(design_traceability_path: Path) -> tuple[dict[str, dict], list[str]]:
    """design-traceability.yaml から設計要素だけを抽出する（構造チェックのみ、業務規則の再検証はしない）。"""
    try:
        data = yaml.safe_load(design_traceability_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        return {}, [f"設計トレーサビリティ正本を読み込めません: {error}"]
    if not isinstance(data, dict) or data.get("version") != "1.0":
        return {}, ["設計トレーサビリティ正本の version は 1.0 で指定してください"]
    elements = data.get("design_elements")
    if not isinstance(elements, list) or not elements:
        return {}, ["設計トレーサビリティ正本の design_elements は1件以上の配列で指定してください"]
    result: dict[str, dict] = {}
    failures: list[str] = []
    for index, element in enumerate(elements):
        if not isinstance(element, dict):
            failures.append(f"設計トレーサビリティ正本 design_elements[{index}] はオブジェクトで指定してください")
            continue
        identifier = element.get("id")
        element_type = element.get("type")
        pattern = DESIGN_ELEMENT_PATTERNS.get(element_type)
        if not nonempty_text(identifier) or pattern is None or not pattern.fullmatch(identifier):
            failures.append(f"設計トレーサビリティ正本 design_elements[{index}] のID形式が不正です")
            continue
        if identifier in result:
            failures.append(f"設計トレーサビリティ正本の設計要素IDが重複しています: {identifier}")
        result[identifier] = element
    return result, failures


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


def validate(data: dict, design_elements: dict[str, dict]) -> list[str]:
    failures: list[str] = []
    if data.get("version") != "1.0":
        failures.append("version は 1.0 を指定してください")
    items = data.get("test_items")
    if not isinstance(items, list) or not items:
        return failures + ["test_items は1件以上の配列で指定してください"]

    seen: set[str] = set()
    coverage: dict[str, set[str]] = {identifier: set() for identifier in design_elements}
    for index, item in enumerate(items):
        label = "テスト項目"
        if not isinstance(item, dict):
            failures.append(f"test_items[{index}] はオブジェクトで指定してください")
            continue
        identifier = item.get("id", "<IDなし>")
        if identifier in seen:
            failures.append(f"{label} {identifier}: IDが重複しています")
        seen.add(identifier)

        if not validate_status(item, label, failures):
            continue

        test_type = item.get("test_type")
        if test_type not in TEST_TYPES:
            failures.append(f"{label} {identifier}: test_type は unit/integration で指定してください")
            continue
        if not TEST_TYPE_ID_PATTERNS[test_type].fullmatch(str(identifier)):
            failures.append(f"{label} {identifier}: {test_type} のID形式が不正です")

        design_element_ids = item.get("design_element_ids")
        if not isinstance(design_element_ids, list) or not design_element_ids:
            failures.append(f"{label} {identifier}: design_element_ids は1件以上必要です")
            design_element_ids = []

        required_element_type = TEST_TYPE_ELEMENT_TYPES[test_type]
        linked_requirement_ids: set[str] = set()
        for design_element_id in design_element_ids:
            element = design_elements.get(design_element_id)
            if element is None:
                failures.append(f"{label} {identifier}: 参照先の設計要素が存在しません: {design_element_id}")
                continue
            if element.get("type") != required_element_type:
                failures.append(
                    f"{label} {identifier}: {test_type} は {required_element_type} の設計要素に紐づけてください"
                    f"（{design_element_id} は {element.get('type')}）"
                )
                continue
            coverage.setdefault(design_element_id, set()).add(identifier)
            linked_requirement_ids.update(element.get("requirement_ids") or [])

        requirement_ids = item.get("requirement_ids")
        if not isinstance(requirement_ids, list) or not requirement_ids:
            failures.append(f"{label} {identifier}: requirement_ids は1件以上必要です")
            requirement_ids = []
        for requirement_id in requirement_ids:
            if not nonempty_text(requirement_id) or not REQUIREMENT_PATTERN.fullmatch(requirement_id):
                failures.append(f"{label} {identifier}: 要件ID形式が不正です: {requirement_id}")
        outside_scope = sorted(set(requirement_ids) - linked_requirement_ids)
        if outside_scope:
            failures.append(
                f"{label} {identifier}: requirement_ids に紐づく設計要素の対象外の要件が含まれています: "
                + ", ".join(outside_scope)
            )

        for field in ("preconditions", "steps", "expected_results"):
            if not nonempty_list(item.get(field)):
                failures.append(f"{label} {identifier}: {field} は1件以上必要です")

    for design_element_id, covering in coverage.items():
        if not covering:
            failures.append(f"設計要素がテストで被覆されていません: {design_element_id}")
    return failures


def load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("テストトレーサビリティ正本はYAMLオブジェクトで指定してください")
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="設計要素とUT/ITのトレーサビリティを検証")
    parser.add_argument("test_traceability", type=Path, help="test-traceability.yaml のパス")
    parser.add_argument("--json", action="store_true", help="JSONで出力")
    args = parser.parse_args()
    try:
        data = load(args.test_traceability)
        design_elements, failures = design_element_index(design_traceability_path(data, args.test_traceability))
        if not failures:
            failures = validate(data, design_elements)
    except (OSError, ValueError, yaml.YAMLError) as error:
        failures = [f"テストトレーサビリティ正本を読み込めません: {error}"]
    report = {"gate_passed": not failures, "failures": failures}
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else "テストトレーサビリティゲート: " + ("通過" if not failures else "不通過"))
    if not args.json:
        for failure in failures:
            print(f"- {failure}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
