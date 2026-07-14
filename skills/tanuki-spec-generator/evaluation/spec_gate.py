#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""仕様書を実装引き渡し可能か検証する出力ゲート。"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import coverage

EVIDENCE_RE = re.compile(r"(?m)^[-*]\s*\*\*根拠\*\*:\s*(?:\[入力\]|\[参照\]).+\S")


def evidence_failures(document: str, results: list[dict]) -> list[str]:
    failures = []
    for result in results:
        if not result["filled"]:
            continue
        body = coverage.find_body(document, result["id"])
        if body is None or not EVIDENCE_RE.search(body):
            failures.append(f"根拠不足: {result['id']}（[入力] または [参照] を明記）")
    return failures


def main() -> None:
    parser = argparse.ArgumentParser(description="仕様書の出力ゲート検証")
    parser.add_argument("spec", help="記入済み仕様書(.md)のパス")
    parser.add_argument("--phase", choices=["requirements", "basic_design", "detailed_design"])
    parser.add_argument("--json", action="store_true", help="JSONで出力")
    args = parser.parse_args()

    document = Path(args.spec).read_text(encoding="utf-8")
    data = coverage.yaml.safe_load(coverage.SSOT.read_text(encoding="utf-8"))
    phase = args.phase or coverage.detect_phase(document)
    results = coverage.evaluate(document, data, phase)
    summary = coverage.summarize(results)
    failures = (
        coverage.structural_failures(document, data, phase)
        + coverage.gate_failures(results)
        + evidence_failures(document, results)
    )
    if data["meta"].get("approval_status") != "approved":
        failures.insert(0, "品質項目マスターはKEIGOの承認待ちです。承認前の仕様書は実装へ引き渡せません")
    report = {"summary": summary["overall"], "gate_passed": not failures, "failures": failures}

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("出力ゲート: " + ("通過" if not failures else "不通過"))
        print(f"必須充足率: {summary['overall']['required_coverage']}%")
        print(f"要確認: {summary['overall']['confirmation_needed']}件")
        for failure in failures:
            print(f"- {failure}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
