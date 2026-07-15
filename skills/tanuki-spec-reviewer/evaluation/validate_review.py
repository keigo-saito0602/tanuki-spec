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

RUBRIC_AXES = {"完全性", "曖昧性の排除", "整合性", "トレーサビリティ", "実装可能性", "根拠_非ハルシネーション"}
ALLOWED_JUDGEMENTS = {"PASS", "要改善", "判断不可"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(review: dict, spec_path: Path, traceability_path: Path, design_traceability_path: Path | None = None) -> list[str]:
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
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="AI品質レビュー記録を検証する")
    parser.add_argument("review", help="ai_quality_review YAMLファイル")
    parser.add_argument("--spec", required=True, help="採点対象の仕様書")
    parser.add_argument("--traceability", required=True, help="採点対象に対応する traceability.yaml")
    parser.add_argument("--design-traceability", help="設計工程に対応する design-traceability.yaml")
    args = parser.parse_args()
    try:
        errors = validate(yaml.safe_load(Path(args.review).read_text(encoding="utf-8")), Path(args.spec), Path(args.traceability), Path(args.design_traceability) if args.design_traceability else None)
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
