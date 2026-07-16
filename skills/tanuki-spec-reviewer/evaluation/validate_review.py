#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI品質レビュー記録と対象仕様書の整合性を検証する。"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML が必要です: python3 -m pip install -r requirements.txt")

import coverage
import design_traceability_gate
import traceability_gate
import evaluate_review_items
import render_quality_evaluation

RUBRIC_AXES = {"完全性", "曖昧性の排除", "整合性", "トレーサビリティ", "実装可能性", "根拠_非ハルシネーション"}
ALLOWED_JUDGEMENTS = {"PASS", "要改善", "判断不可"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_evaluation(entry: dict, review: dict, traceability_path: Path, design_traceability_path: Path | None, report_path: Path | None) -> list[str]:
    """評価機能を使った記録だけを追加検証する（既存形式との互換性を保つ）。"""
    evaluation = entry.get("evaluation")
    if evaluation is None:
        return []
    if not isinstance(evaluation, dict):
        return ["evaluation はオブジェクトにしてください"]
    errors = []
    items = evaluation.get("item_results")
    if not isinstance(items, list):
        return ["evaluation.item_results は配列にしてください"]
    ids = [item.get("id") for item in items if isinstance(item, dict)]
    if len(ids) != len(set(ids)):
        errors.append("evaluation.item_results のIDが重複しています")
    for item in items:
        if not isinstance(item, dict):
            errors.append("evaluation.item_results の各要素はオブジェクトにしてください")
        else:
            errors.extend(evaluate_review_items.validate_item_result(item))
    summary = evaluation.get("summary")
    if summary is not None:
        required = [item for item in items if item.get("importance") == "required" and item.get("status") != "not_applicable"]
        applicable = [item for item in items if item.get("status") != "not_applicable"]
        weights = evaluate_review_items.WEIGHTS
        required_pass = sum(item.get("status") == "pass" for item in required)
        weighted_total = sum(weights.get(item.get("importance"), 0) for item in applicable)
        weighted_pass = sum(weights.get(item.get("importance"), 0) for item in applicable if item.get("status") == "pass")
        expected = {
            "applicable_count": len(applicable), "pass_count": sum(item.get("status") == "pass" for item in items),
            "needs_improvement_count": sum(item.get("status") == "needs_improvement" for item in items),
            "not_evaluable_count": sum(item.get("status") == "not_evaluable" for item in items),
            "not_applicable_count": sum(item.get("status") == "not_applicable" for item in items),
            "required_total": len(required), "required_pass_count": required_pass,
            "required_pass_rate": 100 * required_pass / len(required) if required else None,
            "weighted_pass_rate": 100 * weighted_pass / weighted_total if weighted_total else None,
        }
        for key, value in expected.items():
            if summary.get(key) != value:
                errors.append(f"evaluation.summary.{key} が項目結果の集計と一致しません")
        if "machine_verdict" not in summary or "dod_blockers" not in summary:
            errors.append("evaluation.summary.machine_verdict と dod_blockers が必要です")
    if evaluation.get("report_sha256"):
        if report_path is None:
            errors.append("evaluation.report_sha256 がある場合は --report が必要です")
        elif not report_path.is_file():
            errors.append("--report で指定した評価レポートが存在しません")
        else:
            if evaluation["report_sha256"] != sha256(report_path):
                errors.append("evaluation.report_sha256 が評価レポートと一致しません")
            try:
                if render_quality_evaluation.render(review) != report_path.read_text(encoding="utf-8"):
                    errors.append("評価レポートが正規化YAMLからの再生成結果と一致しません")
            except ValueError as error:
                errors.append(f"評価レポートを再生成できません: {error}")
    return errors


def validate(review: dict, spec_path: Path, traceability_path: Path, design_traceability_path: Path | None = None, report_path: Path | None = None) -> list[str]:
    errors = []
    entry = review.get("ai_quality_review")
    if not isinstance(entry, dict):
        return ["ai_quality_review オブジェクトがありません"]

    for key in ("date", "target", "reviewer", "generated_spec_sha256", "traceability_sha256", "traceability_gate_passed", "coverage", "rubric", "dod_passed"):
        if key not in entry:
            errors.append(f"必須項目不足: {key}")
    if errors:
        return errors
    if entry["target"] not in {"requirements", "basic_design", "detailed_design"}:
        errors.append("target が不正です")
    is_design_target = entry["target"] in {"basic_design", "detailed_design"}
    if is_design_target:
        for key in ("design_traceability_sha256", "design_traceability_gate_passed"):
            if key not in entry:
                errors.append(f"設計工程の必須項目不足: {key}")
        if design_traceability_path is None:
            errors.append("設計工程では --design-traceability が必要です")
    reviewer = entry["reviewer"]
    if not isinstance(reviewer, dict) or not reviewer.get("role") or not reviewer.get("model"):
        errors.append("reviewer.role と reviewer.model が必要です")
    if reviewer.get("independent") is not True:
        errors.append("別セッションまたは別担当の採点を reviewer.independent: true で記録してください")
    if entry["generated_spec_sha256"] != sha256(spec_path):
        errors.append("generated_spec_sha256 が対象仕様書と一致しません")
    if entry["traceability_sha256"] != sha256(traceability_path):
        errors.append("traceability_sha256 がトレーサビリティ正本と一致しません")
    traceability_failures = traceability_gate.validate(traceability_gate.load(traceability_path))
    if entry["traceability_gate_passed"] is not True:
        errors.append("traceability_gate_passed は true で記録してください")
    if traceability_failures:
        errors.append("トレーサビリティゲートが不通過です: " + " / ".join(traceability_failures))
    design_traceability_failures: list[str] = []
    if is_design_target and design_traceability_path is not None and "design_traceability_sha256" in entry:
        if entry["design_traceability_sha256"] != sha256(design_traceability_path):
            errors.append("design_traceability_sha256 が設計トレーサビリティ正本と一致しません")
        requirements, design_traceability_failures = design_traceability_gate.requirement_index(traceability_path)
        if not design_traceability_failures:
            design_traceability_failures = design_traceability_gate.validate(design_traceability_gate.load(design_traceability_path), requirements)
        if entry.get("design_traceability_gate_passed") is not True:
            errors.append("design_traceability_gate_passed は true で記録してください")
        if design_traceability_failures:
            errors.append("設計トレーサビリティゲートが不通過です: " + " / ".join(design_traceability_failures))

    document = spec_path.read_text(encoding="utf-8")
    data = yaml.safe_load(coverage.SSOT.read_text(encoding="utf-8"))
    results = coverage.evaluate(document, data, entry["target"])
    actual = coverage.summarize(results)["overall"]
    recorded = entry["coverage"]
    for key in ("required_coverage", "overall_coverage", "todo_flags"):
        if key not in recorded:
            errors.append(f"coverage.{key} がありません")
    if not errors and (
        recorded["required_coverage"] != actual["required_coverage"]
        or recorded["overall_coverage"] != actual["coverage"]
        or recorded["todo_flags"] != actual["confirmation_needed"]
    ):
        errors.append("coverage の記録値が対象仕様書の実測値と一致しません")

    rubric = entry["rubric"]
    if set(rubric) != RUBRIC_AXES:
        errors.append("rubric は6軸を過不足なく含める必要があります")
    elif any(value not in ALLOWED_JUDGEMENTS for value in rubric.values()):
        errors.append("rubric の判定値が不正です")

    structural = coverage.structural_failures(document, data, entry["target"])
    expected_dod = (
        data["meta"].get("approval_status") == "approved"
        and not structural
        and not coverage.gate_failures(results)
        and entry["traceability_gate_passed"] is True
        and not traceability_failures
        and (not is_design_target or (entry.get("design_traceability_gate_passed") is True and not design_traceability_failures))
        and all(value == "PASS" for value in rubric.values())
    )
    if entry["dod_passed"] != expected_dod:
        errors.append("dod_passed がカバレッジ・ルーブリックの判定と一致しません")
    errors.extend(validate_evaluation(entry, review, traceability_path, design_traceability_path, report_path))
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="AI品質レビュー記録を検証する")
    parser.add_argument("review", help="ai_quality_review YAMLファイル")
    parser.add_argument("--spec", required=True, help="採点対象の仕様書")
    parser.add_argument("--traceability", required=True, help="採点対象に対応する traceability.yaml")
    parser.add_argument("--design-traceability", help="設計工程に対応する design-traceability.yaml")
    parser.add_argument("--report", help="生成済み quality-evaluation.md（評価レポートのハッシュを検証する場合に指定）")
    args = parser.parse_args()
    try:
        errors = validate(yaml.safe_load(Path(args.review).read_text(encoding="utf-8")), Path(args.spec), Path(args.traceability), Path(args.design_traceability) if args.design_traceability else None, Path(args.report) if args.report else None)
    except (OSError, ValueError, yaml.YAMLError) as error:
        errors = [f"レビュー記録またはトレーサビリティ正本を読み込めません: {error}"]
    if errors:
        print("AI品質レビュー記録: 不通過")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)
    print("AI品質レビュー記録: 通過")


if __name__ == "__main__":
    main()
