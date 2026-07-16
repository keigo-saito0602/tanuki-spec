#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ai-quality-review.yaml から再現可能な人間向け評価レポートを生成する。"""
from __future__ import annotations

import argparse
from pathlib import Path

import yaml

STATUS_LABELS = {"pass": "PASS", "needs_improvement": "要改善", "not_evaluable": "判断不可", "not_applicable": "対象外"}
REQUIREMENT_LABELS = {"covered": "充足", "partially_covered": "一部充足", "not_evaluable": "判断不可", "not_covered": "未充足"}


def normalized_entry(review: dict) -> dict:
    entry = review.get("ai_quality_review")
    if not isinstance(entry, dict):
        raise ValueError("ai_quality_review オブジェクトが必要です")
    # 生成後に変わる値を、レポート入力から先に除去する。
    entry = {key: value for key, value in entry.items() if key not in {"human_review", "dod_passed", "dod_note"}}
    evaluation = dict(entry.get("evaluation") or {})
    evaluation.pop("report_sha256", None)
    entry["evaluation"] = evaluation
    return entry


def rate(value: float | None) -> str:
    return "算出対象外" if value is None else f"{value:.1f}%"


def escape(value: object) -> str:
    return str(value or "―").replace("|", "\\|").replace("\n", "<br>")


def table(headers: list[str], rows: list[list[object]]) -> list[str]:
    result = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    result.extend("| " + " | ".join(escape(cell) for cell in row) + " |" for row in rows)
    return result


def render(review: dict) -> str:
    entry = normalized_entry(review)
    evaluation = entry["evaluation"]
    summary = evaluation.get("summary")
    if not isinstance(summary, dict) or not evaluation.get("generated_at"):
        raise ValueError("evaluation.summary と evaluation.generated_at が必要です")
    reviewer = entry.get("reviewer", {})
    reviewer_text = f"{reviewer.get('model', '―')}（独立レビュー: {'あり' if reviewer.get('independent') else 'なし'}）"
    verdict = "合格" if summary.get("machine_verdict") else "不合格（人間承認の前に解消が必要）"
    coverage = entry.get("coverage", {})
    lines = ["# 品質評価レポート", "", "## 結論", "", f"- 機械判定: {verdict}",
             f"- レビュー: {reviewer_text} / {entry.get('date', evaluation['generated_at'])}",
             f"- 必須項目PASS率: {rate(summary.get('required_pass_rate'))}（{summary.get('required_total', 0)}件中{summary.get('required_pass_count', 0)}件）",
             f"- 重み付きPASS率: {rate(summary.get('weighted_pass_rate'))}",
             f"- 必須項目の記入率: {coverage.get('required_coverage', '―')}%／全項目の記入率: {coverage.get('overall_coverage', '―')}%"]
    blockers = summary.get("dod_blockers", [])
    if blockers:
        lines.append("- 次工程へ進めない理由: " + " / ".join(blockers))
    lines += ["", "## 前回レビューからの差分", "", f"- {entry.get('diff_from_prev', '初回のため差分なし')}", "", "## 要件対応の集計", ""]
    requirements = evaluation.get("requirement_results", [])
    lines += table(["状態", "件数"], [[label, sum(item.get("status") == status for item in requirements)] for status, label in REQUIREMENT_LABELS.items()])
    lines += ["", "## 要件対応表", ""]
    lines += table(["要件ID", "設計要素", "受け入れ条件・テスト証跡", "評価", "状態"], [
        [item.get("requirement_id"), ", ".join(item.get("design_element_ids", [])), ", ".join(item.get("acceptance_criteria_ids", []) + item.get("test_evidence_ids", [])), ", ".join(item.get("related_evaluation_item_ids", [])), REQUIREMENT_LABELS.get(item.get("status"), item.get("status"))]
        for item in requirements])
    items = evaluation.get("item_results", [])
    categories: dict[str, list[dict]] = {}
    for item in items:
        categories.setdefault(item["id"].split("-", 1)[0], []).append(item)
    lines += ["", "## カテゴリ別の集計", ""]
    lines += table(["カテゴリ", "PASS", "要改善", "判断不可", "対象外"], [[category, sum(x.get("status") == "pass" for x in values), sum(x.get("status") == "needs_improvement" for x in values), sum(x.get("status") == "not_evaluable" for x in values), sum(x.get("status") == "not_applicable" for x in values)] for category, values in categories.items()])
    issues = [item for item in items if item.get("status") in {"needs_improvement", "not_evaluable"}]
    lines += ["", "## 未充足・判断不可一覧", ""]
    if issues:
        lines += table(["ID", "重要度", "判定", "根拠", "理由", "推奨対応"], [[item.get("id"), item.get("importance"), STATUS_LABELS[item.get("status")], "; ".join(str(evidence.get("reference", evidence.get("kind", ""))) for evidence in item.get("evidence", [])) or "証跡なし", item.get("reason"), item.get("recommended_action")] for item in issues])
    else:
        lines.append("- なし")
    excluded = [item for item in items if item.get("status") == "not_applicable"]
    lines += ["", "## 対象外一覧", ""]
    lines += table(["ID", "理由", "対象外の根拠"], [[item.get("id"), item.get("reason"), item.get("not_applicable_basis", {}).get("condition") or item.get("not_applicable_basis", {}).get("kind")] for item in excluded]) if excluded else ["- なし"]
    lines += ["", "## 人間レビューで確認する項目", "", "- 未充足・判断不可の推奨対応が、次工程へ進む前に解消されているか。", "- 要件対応表の設計要素・受け入れ条件・テスト証跡を、正本で辿れるか。", "", "## 証跡・入力ファイル", "", f"- 生成日時: {evaluation['generated_at']}", f"- 対象仕様書SHA-256: {entry.get('generated_spec_sha256', '―')}", f"- トレーサビリティSHA-256: {entry.get('traceability_sha256', '―')}"]
    if entry.get("design_traceability_sha256"):
        lines.append(f"- 設計トレーサビリティSHA-256: {entry['design_traceability_sha256']}")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="AI品質レビューから人間向け評価レポートを生成する")
    parser.add_argument("review")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    try:
        review = yaml.safe_load(Path(args.review).read_text(encoding="utf-8"))
        Path(args.out).write_text(render(review), encoding="utf-8")
    except (OSError, ValueError, yaml.YAMLError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
