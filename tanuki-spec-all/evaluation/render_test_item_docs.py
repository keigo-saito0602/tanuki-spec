#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test-traceability.yaml からテスト項目書（UT/IT/V字カバレッジ）を生成する。

既存の AC（受入試験・UAT）と ST（システムテスト）は traceability.yaml が正本であり、
ここでは再定義せず参照表示だけする。
"""
from __future__ import annotations

import argparse
from pathlib import Path

import test_traceability_gate


def cell(value: object) -> str:
    if isinstance(value, list):
        return "<br>".join(cell(item) for item in value)
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def table(headers: list[str], rows: list[list[object]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    lines.extend("| " + " | ".join(cell(value) for value in row) + " |" for row in rows)
    return lines


def in_scope(items: list[dict]) -> list[dict]:
    return [item for item in items if item.get("status") == "in_scope"]


def render_test_section(heading: str, items: list[dict], test_type: str) -> list[str]:
    rows = [
        [
            item["id"],
            item.get("design_element_ids", []),
            item.get("requirement_ids", []),
            item.get("preconditions", []),
            item.get("steps", []),
            item.get("expected_results", []),
        ]
        for item in in_scope(items)
        if item.get("test_type") == test_type
    ]
    lines = [heading, ""]
    lines.extend(table(["ID", "対象設計要素", "対象要件", "前提条件", "操作", "期待結果"], rows))
    lines.append("")
    return lines


def render_v_model_coverage(design_elements: dict[str, dict], items: list[dict], ac_st_by_requirement: dict) -> list[str]:
    covering: dict[str, list[str]] = {identifier: [] for identifier in design_elements}
    for item in in_scope(items):
        for design_element_id in item.get("design_element_ids") or []:
            if design_element_id in covering:
                covering[design_element_id].append(item["id"])

    rows = []
    for identifier, element in design_elements.items():
        requirement_ids = element.get("requirement_ids") or []
        acceptance_ids: list[str] = []
        system_ids: list[str] = []
        for requirement_id in requirement_ids:
            related = ac_st_by_requirement.get(requirement_id, {})
            acceptance_ids.extend(related.get("acceptance_test_ids", []))
            system_ids.extend(related.get("system_test_ids", []))
        rows.append([
            identifier,
            element.get("type", ""),
            requirement_ids,
            sorted(covering.get(identifier, [])),
            sorted(set(acceptance_ids)),
            sorted(set(system_ids)),
        ])
    lines = ["## V字モデルカバレッジ", ""]
    lines.extend(table(["設計要素ID", "設計工程", "対応要件", "対応UT/IT", "対応AC(UAT)", "対応ST"], rows))
    lines.append("")
    return lines


def render(data: dict, design_elements: dict[str, dict], ac_st_by_requirement: dict) -> str:
    items = data.get("test_items") or []
    lines = ["# テスト項目書", ""]
    lines.extend(render_test_section("## 単体テスト（UT）", items, "unit"))
    lines.extend(render_test_section("## 結合テスト（IT）", items, "integration"))
    lines.extend(render_v_model_coverage(design_elements, items, ac_st_by_requirement))
    return "\n".join(lines) + "\n"


def acceptance_and_system_index(traceability_path: Path) -> dict:
    """traceability.yaml のAC/STを要件ID単位で束ねる。AC/STはここでは再定義しない。"""
    import yaml

    data = yaml.safe_load(traceability_path.read_text(encoding="utf-8"))
    index: dict[str, dict] = {}
    for acceptance in (data.get("acceptance_tests") or []):
        if not isinstance(acceptance, dict) or acceptance.get("status") != "in_scope":
            continue
        for requirement_id in acceptance.get("requirement_ids") or []:
            index.setdefault(requirement_id, {}).setdefault("acceptance_test_ids", []).append(acceptance["id"])
    for system in (data.get("system_tests") or []):
        if not isinstance(system, dict) or system.get("status") != "in_scope":
            continue
        for requirement_id in system.get("requirement_ids") or []:
            index.setdefault(requirement_id, {}).setdefault("system_test_ids", []).append(system["id"])
    return index


def main() -> None:
    parser = argparse.ArgumentParser(description="テストトレーサビリティ正本からテスト項目書を生成")
    parser.add_argument("test_traceability", type=Path, help="test-traceability.yaml のパス")
    parser.add_argument("--output-dir", type=Path, required=True, help="生成先ディレクトリ（<phase>/tests）")
    parser.add_argument("--check", action="store_true", help="生成物との差分だけを検証する")
    args = parser.parse_args()

    data = test_traceability_gate.load(args.test_traceability)
    design_traceability_path = test_traceability_gate.design_traceability_path(data, args.test_traceability)
    design_elements, failures = test_traceability_gate.design_element_index(design_traceability_path)
    if not failures:
        failures = test_traceability_gate.validate(data, design_elements)
    if failures:
        raise SystemExit("テストトレーサビリティゲート不通過のためテスト項目書を生成できません: " + " / ".join(failures))

    design_data = test_traceability_gate.load(design_traceability_path)
    import design_traceability_gate

    requirements_path = design_traceability_gate.requirements_path(design_data, design_traceability_path)
    ac_st_by_requirement = acceptance_and_system_index(requirements_path)

    content = render(data, design_elements, ac_st_by_requirement)
    output = args.output_dir / "04_テスト項目書.md"
    if args.check:
        if not output.exists() or output.read_text(encoding="utf-8") != content:
            raise SystemExit(f"テスト項目書が正本と不一致です: {output}")
        print(f"検証: {output}")
        return
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    print(f"生成: {output}")


if __name__ == "__main__":
    main()
