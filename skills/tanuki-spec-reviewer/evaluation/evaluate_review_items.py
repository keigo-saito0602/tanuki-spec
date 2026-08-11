#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""評価ルールの適用判定・集計を行う。内容の採点は行わない。"""
from __future__ import annotations

import argparse
import hashlib
import os
import tempfile
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT.parent.parent / "tanuki-spec-all"
SSOT = CORE / "spec-items.yaml"
VALID_STATUSES = {"pass", "needs_improvement", "not_evaluable", "not_applicable"}
WEIGHTS = {"required": 3, "important": 2, "normal": 1}


def load(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"YAMLオブジェクトが必要です: {path}")
    return value


def write_atomic(path: Path, data: dict) -> None:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        yaml.safe_dump(data, handle, allow_unicode=True, sort_keys=False)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def context_value(path: Path | None) -> dict:
    if path is None:
        return {"workload_types": [], "data_classifications": [], "has_stateful_workflow": False,
                "has_user_roles": False, "has_external_api": False, "deployment_required": False}
    value = load(path).get("review_context")
    if not isinstance(value, dict):
        raise ValueError("review_context オブジェクトが必要です")
    for key in ("workload_types", "data_classifications"):
        if not isinstance(value.get(key, []), list):
            raise ValueError(f"review_context.{key} は配列にしてください")
    return value


def source_ids() -> dict[str, set[str]]:
    data = load(SSOT)
    return {
        "spec_item": {item["id"] for phase in data["phases"].values() for category in phase["categories"] for item in category["items"]},
        "nonfunctional_major_item": {item["id"] for item in data["non_functional"]["major_items"]},
        "quality_characteristic": {item["id"] for item in data["quality_characteristics"]},
    }


def validate_rules(rules: dict) -> list[dict]:
    if not isinstance(rules.get("version"), str) or not isinstance(rules.get("rules"), list):
        raise ValueError("review-rules.yaml の version と rules が必要です")
    ids = source_ids()
    seen = set()
    for rule in rules["rules"]:
        if not isinstance(rule, dict) or rule.get("id") in seen:
            raise ValueError("評価ルールIDが不足または重複しています")
        seen.add(rule["id"])
        source = rule.get("source", {})
        if source.get("kind") not in ids or source.get("id") not in ids[source.get("kind")]:
            raise ValueError(f"ルール {rule['id']} の source.id が正本に存在しません")
        if rule.get("importance") not in WEIGHTS:
            raise ValueError(f"ルール {rule['id']} の importance が不正です")
    return rules["rules"]


def condition_matches(condition: dict, context: dict) -> bool:
    workload = set(context.get("workload_types", []))
    classifications = set(context.get("data_classifications", []))
    if "any_workload_types" in condition and not workload.intersection(condition["any_workload_types"]):
        return False
    if "all_workload_types" in condition and not set(condition["all_workload_types"]).issubset(workload):
        return False
    if "data_classifications_any" in condition and not classifications.intersection(condition["data_classifications_any"]):
        return False
    if "flags_all" in condition and not all(context.get(flag) is True for flag in condition["flags_all"]):
        return False
    if "flags_none" in condition and not all(context.get(flag) is False for flag in condition["flags_none"]):
        return False
    return True


def skeleton(rule: dict, applicable: bool) -> dict:
    result = {"id": rule["id"], "status": None if applicable else "not_applicable", "importance": rule["importance"], "evidence": []}
    if not applicable:
        condition = rule.get("applies_when", {})
        result["not_applicable_basis"] = {"kind": "rule_condition", "condition": yaml.safe_dump(condition, allow_unicode=True, default_flow_style=True).strip()}
        result["reason"] = "review-context.yaml の適用条件を満たさない"
    return result


def evaluation_entry(review: dict) -> dict:
    entry = review.get("ai_quality_review")
    if not isinstance(entry, dict):
        raise ValueError("ai_quality_review オブジェクトが必要です")
    return entry


def emit_skeleton(review_path: Path, context_path: Path | None, rules_path: Path, force: bool) -> None:
    review = load(review_path)
    entry = evaluation_entry(review)
    context = context_value(context_path)
    rules = validate_rules(load(rules_path))
    evaluation = entry.setdefault("evaluation", {})
    if evaluation.get("item_results") is not None and not force:
        raise ValueError("evaluation.item_results は既に存在します。採点を破棄して作り直す場合は --force を指定してください")
    target = entry.get("target")
    selected = [rule for rule in rules if target in rule.get("applies_to_targets", [])]
    evaluation["item_results"] = [skeleton(rule, condition_matches(rule.get("applies_when", {}), context)) for rule in selected]
    evaluation["rules_version"] = load(rules_path)["version"]
    write_atomic(review_path, review)


def validate_item_result(item: dict) -> list[str]:
    errors = []
    status = item.get("status")
    if status not in VALID_STATUSES:
        errors.append(f"{item.get('id', '<IDなし>')}: status が未記入または不正です")
        return errors
    if item.get("importance") not in WEIGHTS:
        errors.append(f"{item.get('id')}: importance が不正です")
    if not isinstance(item.get("evidence"), list):
        errors.append(f"{item.get('id')}: evidence は配列にしてください")
    if status in {"needs_improvement", "not_evaluable"}:
        if not item.get("reason") or not item.get("recommended_action"):
            errors.append(f"{item.get('id')}: {status} には reason と recommended_action が必要です")
    if status == "not_applicable":
        basis = item.get("not_applicable_basis")
        if not isinstance(basis, dict) or basis.get("kind") not in {"rule_condition", "human_decision"}:
            errors.append(f"{item.get('id')}: 対象外には not_applicable_basis が必要です")
        elif basis["kind"] == "rule_condition" and not basis.get("condition"):
            errors.append(f"{item.get('id')}: rule_condition の condition が必要です")
        elif basis["kind"] == "human_decision" and (not basis.get("decided_by") or not basis.get("decided_at")):
            errors.append(f"{item.get('id')}: human_decision の decided_by と decided_at が必要です")
        if not item.get("reason"):
            errors.append(f"{item.get('id')}: 対象外理由が必要です")
    return errors


def requirement_results(traceability_path: Path, design_path: Path | None, items: list[dict]) -> list[dict]:
    trace = load(traceability_path)
    design = load(design_path) if design_path else {}
    design_elements = design.get("design_elements", [])
    acceptance = trace.get("acceptance_tests", [])
    tests = trace.get("system_tests", [])
    failed_required = {item["id"] for item in items if item.get("importance") == "required" and item.get("status") != "pass" and item.get("status") != "not_applicable"}
    results = []
    for requirement in trace.get("requirements", []):
        rid = requirement.get("id")
        design_ids = [item["id"] for item in design_elements if rid in item.get("requirement_ids", [])]
        ac_ids = [item["id"] for item in acceptance if rid in item.get("requirement_ids", [])]
        st_ids = [item["id"] for item in tests if rid in item.get("requirement_ids", [])]
        if design_path and not design_ids:
            status = "not_covered"
        elif not ac_ids and not st_ids:
            status = "not_evaluable"
        elif failed_required:
            status = "partially_covered"
        else:
            status = "covered"
        results.append({"requirement_id": rid, "status": status, "design_element_ids": design_ids,
                        "acceptance_criteria_ids": ac_ids, "test_evidence_ids": st_ids,
                        "related_evaluation_item_ids": sorted(failed_required)})
    return results


def aggregate(review_path: Path, context_path: Path | None, rules_path: Path, traceability_path: Path, design_path: Path | None, now: str | None, force: bool) -> None:
    review = load(review_path)
    entry = evaluation_entry(review)
    context_value(context_path)
    rules = validate_rules(load(rules_path))
    evaluation = entry.get("evaluation")
    if not isinstance(evaluation, dict) or not isinstance(evaluation.get("item_results"), list):
        raise ValueError("先に --emit-skeleton を実行してください")
    rule_ids = {rule["id"] for rule in rules if entry.get("target") in rule.get("applies_to_targets", [])}
    items = evaluation["item_results"]
    if {item.get("id") for item in items} != rule_ids:
        raise ValueError("item_results が現在の対象ルールと一致しません。--emit-skeleton --force で作り直してください")
    errors = [error for item in items for error in validate_item_result(item)]
    if errors:
        raise ValueError("\n".join(errors))
    applicable = [item for item in items if item["status"] != "not_applicable"]
    required = [item for item in applicable if item["importance"] == "required"]
    count = lambda status: sum(item["status"] == status for item in items)
    weighted_total = sum(WEIGHTS[item["importance"]] for item in applicable)
    weighted_pass = sum(WEIGHTS[item["importance"]] for item in applicable if item["status"] == "pass")
    required_pass = sum(item["status"] == "pass" for item in required)
    coverage = entry.get("coverage", {})
    base_machine = (load(SSOT)["meta"].get("approval_status") == "approved"
                    and coverage.get("required_coverage") == 100 and coverage.get("overall_coverage") == 100 and coverage.get("todo_flags") == 0
                    and entry.get("traceability_gate_passed") is True
                    and (entry.get("target") not in {"basic_design", "detailed_design"} or entry.get("design_traceability_gate_passed") is True)
                    and all(value == "PASS" for value in entry.get("rubric", {}).values()))
    blockers = [f"{item['id']}: {item.get('reason', item['status'])}" for item in required if item["status"] != "pass"]
    evaluation["summary"] = {"applicable_count": len(applicable), "pass_count": count("pass"),
        "needs_improvement_count": count("needs_improvement"), "not_evaluable_count": count("not_evaluable"),
        "not_applicable_count": count("not_applicable"), "required_total": len(required), "required_pass_count": required_pass,
        "required_pass_rate": 100 * required_pass / len(required) if required else None,
        "weighted_pass_rate": 100 * weighted_pass / weighted_total if weighted_total else None,
        "machine_verdict": bool(base_machine and required_pass == len(required)), "dod_blockers": blockers}
    evaluation["requirement_results"] = requirement_results(traceability_path, design_path, items)
    if not evaluation.get("generated_at") or force:
        evaluation["generated_at"] = now or datetime.now().astimezone().isoformat(timespec="seconds")
    write_atomic(review_path, review)


def write_report_hash(review_path: Path, report_path: Path) -> None:
    review = load(review_path)
    evaluation = evaluation_entry(review).get("evaluation")
    if not isinstance(evaluation, dict) or not evaluation.get("summary"):
        raise ValueError("先に --aggregate を実行してください")
    if not report_path.is_file():
        raise ValueError("評価レポートが存在しません")
    evaluation["report_sha256"] = hashlib.sha256(report_path.read_bytes()).hexdigest()
    write_atomic(review_path, review)


def main() -> None:
    parser = argparse.ArgumentParser(description="評価項目の雛形作成・検証・集計を行う（採点はしない）")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--emit-skeleton", action="store_true")
    mode.add_argument("--aggregate", action="store_true")
    mode.add_argument("--write-report-hash", action="store_true")
    parser.add_argument("review")
    parser.add_argument("--context")
    parser.add_argument("--rules")
    parser.add_argument("--traceability")
    parser.add_argument("--design-traceability")
    parser.add_argument("--report")
    parser.add_argument("--now")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--in-place", action="store_true", help="互換性のため受け付ける。常に入力ファイルを部分更新する")
    args = parser.parse_args()
    try:
        review = Path(args.review)
        if not review.is_file():
            raise ValueError("既存の ai-quality-review.yaml が必要です")
        if args.emit_skeleton:
            if not args.rules:
                raise ValueError("--rules が必要です")
            emit_skeleton(review, Path(args.context) if args.context else None, Path(args.rules), args.force)
        elif args.aggregate:
            if not args.rules or not args.traceability:
                raise ValueError("--aggregate には --rules と --traceability が必要です")
            aggregate(review, Path(args.context) if args.context else None, Path(args.rules), Path(args.traceability), Path(args.design_traceability) if args.design_traceability else None, args.now, args.force)
        else:
            if not args.report:
                raise ValueError("--write-report-hash には --report が必要です")
            write_report_hash(review, Path(args.report))
    except (OSError, ValueError, yaml.YAMLError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
