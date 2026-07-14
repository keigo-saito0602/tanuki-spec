#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""仕様書の項目充足を、FILLマーカーから決定論的に評価する。"""
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

ROOT = Path(__file__).resolve().parent.parent
SSOT = ROOT / "spec-items.yaml"
BLOCK_RE = r"<!--\s*FILL:START\s+{id}\s*-->(.*?)<!--\s*FILL:END\s+{id}\s*-->"
UNFILLED_MARKERS = ("（未記入）", "(未記入)")


def iter_items(data: dict, phase: str | None):
    for phase_key, phase_data in data["phases"].items():
        if phase and phase_key != phase:
            continue
        for category in phase_data["categories"]:
            for item in category["items"]:
                yield phase_key, phase_data["label"], item
                if item.get("expands") == "non_functional":
                    for major in data["non_functional"]["major_items"]:
                        for index, sub_item in enumerate(major["sub_items"], start=1):
                            required = bool(major.get("required", True) and sub_item.get("required", True))
                            yield phase_key, phase_data["label"], {
                                "id": f"{item['id']}--{major['id']}--{index:02d}",
                                "name": f"非機能: {major['label']} / {sub_item['name']}",
                                "required": required,
                                "source": data["non_functional"]["source"],
                            }


def clean_body(body: str) -> str:
    """テンプレート内のコメント、未記入記号、TODO行を取り除く。"""
    lines = []
    for line in body.splitlines():
        value = line.strip()
        if not value or (value.startswith("<!--") and value.endswith("-->")):
            continue
        if any(marker in value for marker in UNFILLED_MARKERS):
            continue
        if re.search(r"(?:TODO|TBD)", value, flags=re.IGNORECASE):
            continue
        lines.append(value)
    return "\n".join(lines).strip()


def classify_body(body: str, required: bool | str) -> tuple[bool, str]:
    """内容の有無だけでなく、未確定・対象外を区別して返す。"""
    core = clean_body(body)
    if not core:
        return False, "未記入"
    if "[要確認" in core:
        return False, "要確認"
    not_applicable = re.fullmatch(r"\[対象外:\s*[^\]\s][^\]]*\]", core)
    if "[対象外:" in core:
        if required == "conditional" and not_applicable:
            return False, "対象外"
        return False, "対象外（不正）"
    return True, "充足"


def find_body(doc: str, item_id: str) -> str | None:
    match = re.search(BLOCK_RE.format(id=re.escape(item_id)), doc, re.S)
    return match.group(1) if match else None


def detect_phase(doc: str) -> str | None:
    match = re.search(r"(?m)^template:\s*(\w+)", doc)
    return match.group(1) if match else None


def structural_failures(doc: str, data: dict, phase: str | None) -> list[str]:
    """テンプレートの工程・版・FILLマーカーの破損を検出する。"""
    failures = []
    detected = detect_phase(doc)
    if not detected:
        failures.append("frontmatterの template がありません")
    elif phase and detected != phase:
        failures.append(f"template工程が不一致です: 文書={detected}, 評価={phase}")
    version = re.search(r'(?m)^spec_items_version:\s*["\']?([^"\'\s]+)', doc)
    if not version:
        failures.append("frontmatterの spec_items_version がありません")
    elif version.group(1) != str(data["meta"]["version"]):
        failures.append(f"spec_items_version が不一致です: 文書={version.group(1)}, SSOT={data['meta']['version']}")

    expected = {item[2]["id"] for item in iter_items(data, phase)}
    starts = re.findall(r"<!--\s*FILL:START\s+([^\s]+)\s*-->", doc)
    ends = re.findall(r"<!--\s*FILL:END\s+([^\s]+)\s*-->", doc)
    for item_id in sorted(set(starts) | set(ends)):
        if item_id not in expected:
            failures.append(f"未知のFILLマーカー: {item_id}")
        if starts.count(item_id) != 1 or ends.count(item_id) != 1:
            failures.append(f"FILLマーカーが一対一ではありません: {item_id}")
    for item_id in sorted(expected - set(starts) - set(ends)):
        failures.append(f"FILLマーカーが欠落しています: {item_id}")
    return failures


def evaluate(doc: str, data: dict, phase: str | None) -> list[dict]:
    results = []
    for phase_key, phase_label, item in iter_items(data, phase):
        body = find_body(doc, item["id"])
        if body is None:
            filled, status = False, "欠落"
        else:
            filled, status = classify_body(body, item.get("required"))
        results.append({
            "phase": phase_key,
            "phase_label": phase_label,
            "id": item["id"],
            "name": item["name"],
            "required": item.get("required"),
            "filled": filled,
            "status": status,
        })
    return results


def summarize(results: list[dict]) -> dict:
    phases: dict[str, dict] = {}
    for result in results:
        phase = phases.setdefault(result["phase_label"], {
            "total": 0, "filled": 0, "required_total": 0,
            "required_filled": 0, "confirmation_needed": 0,
        })
        phase["total"] += 1
        phase["filled"] += int(result["filled"])
        phase["confirmation_needed"] += int(result["status"] == "要確認")
        if result["required"] is True:
            phase["required_total"] += 1
            phase["required_filled"] += int(result["filled"])

    total = sum(phase["total"] for phase in phases.values())
    filled = sum(phase["filled"] for phase in phases.values())
    required_total = sum(phase["required_total"] for phase in phases.values())
    required_filled = sum(phase["required_filled"] for phase in phases.values())
    return {
        "phases": phases,
        "overall": {
            "total": total,
            "filled": filled,
            "coverage": round(100 * filled / total, 1) if total else 0.0,
            "required_total": required_total,
            "required_filled": required_filled,
            "required_coverage": round(100 * required_filled / required_total, 1) if required_total else 0.0,
            "confirmation_needed": sum(phase["confirmation_needed"] for phase in phases.values()),
        },
    }


def print_report(results: list[dict], summary: dict) -> None:
    print("=" * 60)
    print(" カバレッジ評価レポート")
    print("=" * 60)
    for label, phase in summary["phases"].items():
        total = phase["total"]
        required_total = phase["required_total"]
        print(f"\n■ {label}")
        print(f"    全項目 : {phase['filled']}/{total}  充足率 {100 * phase['filled'] / total:.1f}%")
        print(f"    必須   : {phase['required_filled']}/{required_total}  必須充足率 {100 * phase['required_filled'] / required_total:.1f}%")
        print(f"    要確認 : {phase['confirmation_needed']}件")

    missing = [result for result in results if not result["filled"]]
    if missing:
        print("\n【未充足・要確認】")
        for result in missing:
            tag = "★" if result["required"] is True else "・"
            print(f"    {tag} [{result['phase_label']}] {result['name']}  ({result['status']})")
    else:
        print("\nすべての項目が充足しています。")


def gate_failures(results: list[dict]) -> list[str]:
    failures = []
    for result in results:
        if result["required"] is True and not result["filled"]:
            failures.append(f"必須未充足: {result['id']} ({result['status']})")
        if result["status"] == "要確認":
            failures.append(f"未解決の要確認: {result['id']}")
        if result["status"] == "対象外（不正）":
            failures.append(f"必須/任意項目を対象外にできません: {result['id']}")
    return failures


def main() -> None:
    parser = argparse.ArgumentParser(description="仕様書のカバレッジ評価")
    parser.add_argument("spec", help="記入済み仕様書(.md)のパス")
    parser.add_argument("--phase", choices=["requirements", "basic_design", "detailed_design"])
    parser.add_argument("--json", action="store_true", help="JSONで出力")
    parser.add_argument("--strict", action="store_true", help="必須未充足・要確認があれば終了コード1")
    args = parser.parse_args()

    document = Path(args.spec).read_text(encoding="utf-8")
    data = yaml.safe_load(SSOT.read_text(encoding="utf-8"))
    results = evaluate(document, data, args.phase or detect_phase(document))
    summary = summarize(results)
    failures = structural_failures(document, data, args.phase or detect_phase(document)) + gate_failures(results)

    if args.json:
        print(json.dumps({"summary": summary["overall"], "items": results, "gate_failures": failures}, ensure_ascii=False, indent=2))
    else:
        print_report(results, summary)
        if args.strict and failures:
            print("\n【出力ゲート不通過】")
            for failure in failures:
                print(f"    - {failure}")
    if args.strict and failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
