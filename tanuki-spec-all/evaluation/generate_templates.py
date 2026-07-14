#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""spec-items.yaml（SSOT）から3種の穴埋めテンプレートを生成する。

テンプレートを手書きせずSSOTから生成することで、項目定義を1箇所に集約し
（保守性要件）、資料改訂時は spec-items.yaml だけ直せばテンプレも追随する。

各項目は次の形式で出力する（カバレッジ評価が突き合わせるマーカー付き）:

    ### [必須] 項目名  <!-- spec-item: id -->
    - **記入ガイド**: purpose
    - **出典**: source ／ **品質観点**: aspects
    <!-- FILL:START id -->
    （未記入）
    <!-- FILL:END id -->

使い方:
    python3 evaluation/generate_templates.py
    # → templates/ に3ファイルを出力
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML が必要です: pip install pyyaml")

ROOT = Path(__file__).resolve().parent.parent
SSOT = ROOT / "spec-items.yaml"
TEMPLATES = ROOT / "templates"

UNFILLED = "（未記入）"  # カバレッジ評価が「未記入」と判定する番兵

PHASE_FILES = {
    "requirements": "requirements-template.md",
    "basic_design": "basic-design-template.md",
    "detailed_design": "detailed-design-template.md",
}


def badge(required) -> str:
    return {True: "[必須]", False: "[任意]", "conditional": "[条件付]"}.get(required, "[任意]")


def render_item(item: dict, char_labels: dict, non_functional: dict) -> list[str]:
    iid = item["id"]
    lines = [f'### {badge(item["required"])} {item["name"]}  <!-- spec-item: {iid} -->']
    lines.append(f'- **記入ガイド**: {item["purpose"]}')
    if item.get("required") == "conditional" and item.get("condition"):
        lines.append(f'- **適用条件**: {item["condition"]}')
    aspects = "、".join(char_labels.get(a, a) for a in item.get("aspects", [])) or "―"
    lines.append(f'- **出典**: {item.get("source", "―")} ／ **品質観点**: {aspects}')
    lines.append("<!-- 記入例: - 結論: <決めた内容・数値・条件>\\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->")
    lines.append(f"<!-- FILL:START {iid} -->")
    lines.append(UNFILLED)
    # 非機能を展開する項目は、チェックリストの雛形を添える
    if item.get("expands") == "non_functional":
        lines.append("")
        lines.append("#### 非機能要件の個別明細")
        lines.append("")
        for mj in non_functional["major_items"]:
            for index, sub in enumerate(mj["sub_items"], start=1):
                is_required = bool(mj.get("required", True) and sub.get("required", True))
                badge_text = "[必須]" if is_required else "[任意]"
                sub_id = f"{iid}--{mj['id']}--{index:02d}"
                lines.append(f"##### {badge_text} {mj['label']} / {sub['name']}  <!-- spec-item: {sub_id} -->")
                lines.append(f"- **確認指標**: {sub['metric']}")
                lines.append("<!-- 記入例: - 結論: <目標値・方式・対象外理由>\\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->")
                lines.append(f"<!-- FILL:START {sub_id} -->")
                lines.append(UNFILLED)
                lines.append(f"<!-- FILL:END {sub_id} -->")
                lines.append("")
    lines.append(f"<!-- FILL:END {iid} -->")
    lines.append("")
    return lines


def render_phase(phase_key: str, data: dict) -> str:
    ph = data["phases"][phase_key]
    char_labels = {c["id"]: c["label"] for c in data["quality_characteristics"]}
    nf = data["non_functional"]
    out = []
    out.append("---")
    out.append(f"template: {phase_key}")
    out.append(f'spec_items_version: "{data["meta"]["version"]}"')
    out.append("status: draft")
    out.append("---")
    out.append("")
    out.append(f"# {ph['label']}書テンプレート")
    out.append("")
    out.append(f"> **ゴール**: {ph['goal']}")
    out.append("> 各項目の `<!-- FILL:START ... -->` と `END` の間に内容を記入する。")
    out.append(f"> 「{UNFILLED}」のまま残っている項目はカバレッジ評価で未充足として数えられる。")
    out.append("")
    for cat in ph["categories"]:
        out.append(f"## {cat['label']}")
        out.append("")
        for item in cat["items"]:
            out.extend(render_item(item, char_labels, nf))
    return "\n".join(out) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="SSOTから仕様書テンプレートを生成する")
    parser.add_argument("--check", action="store_true", help="コミット済みテンプレートとの差分だけを検証する")
    args = parser.parse_args()
    data = yaml.safe_load(SSOT.read_text(encoding="utf-8"))
    if not args.check:
        TEMPLATES.mkdir(exist_ok=True)
    mismatches = []
    for phase_key, fname in PHASE_FILES.items():
        content = render_phase(phase_key, data)
        target = TEMPLATES / fname
        if args.check:
            if not target.exists() or target.read_text(encoding="utf-8") != content:
                mismatches.append(f"templates/{fname}")
        else:
            target.write_text(content, encoding="utf-8")
        n = sum(len(c["items"]) for c in data["phases"][phase_key]["categories"])
        print(f"{'検証' if args.check else '生成'}: templates/{fname}  ({n}項目)")
    if mismatches:
        print("SSOTとテンプレートが不一致です: " + ", ".join(mismatches), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
