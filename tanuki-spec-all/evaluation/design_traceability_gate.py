#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""要件と基本・詳細設計要素の追跡性を決定論的に検証する。"""
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


ELEMENT_TYPES = {"basic_design", "detailed_design"}
ELEMENT_PATTERNS = {
    "basic_design": re.compile(r"^BD-\d{3,}$"),
    "detailed_design": re.compile(r"^DD-\d{3,}$"),
}
REQUIREMENT_PATTERN = re.compile(r"^(?:BR|FR|NFR)-\d{3,}$")
UNFILLED_RE = re.compile(r"<[^>]+>|\[要確認|\b(?:TODO|TBD)\b|[（(]未記入[）)]", re.IGNORECASE)


def nonempty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and not UNFILLED_RE.search(value)


def requirement_index(requirements_path: Path) -> tuple[dict[str, dict], list[str]]:
    """既存 traceability.yaml から設計対象の要件だけを抽出する。"""
    try:
        data = yaml.safe_load(requirements_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        return {}, [f"要件トレーサビリティ正本を読み込めません: {error}"]
    if not isinstance(data, dict) or data.get("version") != "1.0":
        return {}, ["要件トレーサビリティ正本の version は 1.0 で指定してください"]
    requirements = data.get("requirements")
    if not isinstance(requirements, list):
        return {}, ["要件トレーサビリティ正本の requirements は配列で指定してください"]
    result: dict[str, dict] = {}
    failures: list[str] = []
    for index, requirement in enumerate(requirements):
        if not isinstance(requirement, dict):
            failures.append(f"要件トレーサビリティ正本 requirements[{index}] はオブジェクトで指定してください")
            continue
        identifier = requirement.get("id")
        if not nonempty_text(identifier) or not REQUIREMENT_PATTERN.fullmatch(identifier):
            failures.append(f"要件トレーサビリティ正本 requirements[{index}] のID形式が不正です")
            continue
        if identifier in result:
            failures.append(f"要件トレーサビリティ正本の要件IDが重複しています: {identifier}")
        result[identifier] = requirement
    return result, failures


def requirements_path(data: dict, design_path: Path) -> Path:
    value = data.get("requirements_traceability", "traceability.yaml")
    if not isinstance(value, str) or not value.strip():
        raise ValueError("requirements_traceability は traceability.yaml への相対パスで指定してください")
    path = Path(value)
    if path.is_absolute():
        raise ValueError("requirements_traceability は相対パスで指定してください")
    return design_path.parent / path


def validate(data: dict, requirements: dict[str, dict]) -> list[str]:
    failures: list[str] = []
    if data.get("version") != "1.0":
        failures.append("version は 1.0 を指定してください")
    elements = data.get("design_elements")
    if not isinstance(elements, list) or not elements:
        return failures + ["design_elements は1件以上の配列で指定してください"]

    covered: set[str] = set()
    seen: set[str] = set()
    for index, element in enumerate(elements):
        label = f"設計要素[{index}]"
        if not isinstance(element, dict):
            failures.append(f"{label} はオブジェクトで指定してください")
            continue
        element_type = element.get("type")
        identifier = element.get("id")
        if element_type not in ELEMENT_TYPES:
            failures.append(f"{label}: type は basic_design/detailed_design で指定してください")
        elif not nonempty_text(identifier) or not ELEMENT_PATTERNS[element_type].fullmatch(identifier):
            failures.append(f"{label} {identifier or '<IDなし>'}: {element_type} のID形式が不正です")
        if identifier in seen:
            failures.append(f"設計要素 {identifier}: IDが重複しています")
        if isinstance(identifier, str):
            seen.add(identifier)
        if not nonempty_text(element.get("name")):
            failures.append(f"設計要素 {identifier or '<IDなし>'}: name が必要です")
        requirement_ids = element.get("requirement_ids")
        if not isinstance(requirement_ids, list) or not requirement_ids:
            failures.append(f"設計要素 {identifier or '<IDなし>'}: requirement_ids は1件以上必要です")
            continue
        for requirement_id in requirement_ids:
            if not nonempty_text(requirement_id) or not REQUIREMENT_PATTERN.fullmatch(requirement_id):
                failures.append(f"設計要素 {identifier or '<IDなし>'}: 要件ID形式が不正です: {requirement_id}")
                continue
            requirement = requirements.get(requirement_id)
            if requirement is None:
                failures.append(f"設計要素 {identifier or '<IDなし>'}: 参照先の要件が存在しません: {requirement_id}")
                continue
            if requirement.get("status") != "in_scope":
                failures.append(f"設計要素 {identifier or '<IDなし>'}: 要件 {requirement_id} は対象外または延期です")
                continue
            covered.add(requirement_id)

    for requirement_id, requirement in requirements.items():
        if requirement.get("status") == "in_scope" and requirement_id not in covered:
            failures.append(f"要件が設計で被覆されていません: {requirement_id}")
    return failures


def load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("設計トレーサビリティ正本はYAMLオブジェクトで指定してください")
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="要件と設計要素のトレーサビリティを検証")
    parser.add_argument("design_traceability", type=Path, help="design-traceability.yaml のパス")
    parser.add_argument("--json", action="store_true", help="JSONで出力")
    args = parser.parse_args()
    try:
        data = load(args.design_traceability)
        requirements, failures = requirement_index(requirements_path(data, args.design_traceability))
        if not failures:
            failures = validate(data, requirements)
    except (OSError, ValueError, yaml.YAMLError) as error:
        failures = [f"設計トレーサビリティ正本を読み込めません: {error}"]
    report = {"gate_passed": not failures, "failures": failures}
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else "設計トレーサビリティゲート: " + ("通過" if not failures else "不通過"))
    if not args.json:
        for failure in failures:
            print(f"- {failure}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
