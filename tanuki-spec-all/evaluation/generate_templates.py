#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""spec-items.yaml（SSOT）から3種の穴埋めテンプレートを生成する。

テンプレートを手書きせずSSOTから生成することで、項目定義を1箇所に集約し
（保守性要件）、資料改訂時は spec-items.yaml だけ直せばテンプレも追随する。

文書の先頭には、案件と読者に合わせて再編集する「読者向け本文」を置く。
品質項目のFILLブロックは末尾の監査用付録へ隔離し、テンプレート充足の順番を
人が読む順番にしない。各監査項目は1行のFILLブロックを持つ:

    ### [必須] 項目名
    <!-- FILL:START id -->（未記入）<!-- FILL:END id -->

記入ガイド・出典・品質観点は、項目ごとに本文へ挟むと行数が倍増し、読み手に
とっては無駄な負荷（extraneous load）になる。そのため文書末尾の「付録: 項目の
根拠一覧」へ表として集約し、記入担当のAIとレビュー時だけが参照する。

FILLマーカーは coverage.py が監査項目を切り出す境界であり、削除できない。
1行に畳んであるのは、find_body が正規表現でマーカーの内側だけを抜くため、
本文の判定に影響しないと確認済みだからである。

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


# 節の中では 必須 → 条件付 → 任意 の順に並べる。優先度の高い項目を先に読ませ、
# 読み手が節の途中で切り上げても重要な決定を取り逃さないようにする。
PRIORITY = {True: 0, "conditional": 1, False: 2}


def by_priority(items: list[dict]) -> list[dict]:
    return sorted(items, key=lambda item: PRIORITY.get(item.get("required"), 2))


def fill_block(item_id: str) -> str:
    """coverage.py が本文を切り出す境界。1行に畳んでも判定は変わらない。"""
    return f"<!-- FILL:START {item_id} -->{UNFILLED}<!-- FILL:END {item_id} -->"


def aspect_labels(item: dict, char_labels: dict) -> str:
    return "、".join(char_labels.get(a, a) for a in item.get("aspects", [])) or "―"


def render_item(item: dict, char_labels: dict, non_functional: dict, guides: list | None = None) -> list[str]:
    """項目1つ分の本文を返す。根拠は guides へ退避し、付録へ回す。"""
    iid = item["id"]
    lines = [f'### {badge(item["required"])} {item["name"]}']
    if item.get("required") == "conditional" and item.get("condition"):
        lines.append(f'- **適用条件**: {item["condition"]}')
    # 中身が本来は表になる項目は、推奨カラムを1行の記入形式として見せる。
    # 骨組みをFILL内へ置くと未記入判定が壊れるため、FILLの外に置き中は空にする。
    if item.get("table_hint"):
        lines.append(f'> 📝 **記入形式**: `{item["table_hint"]}`')
    if guides is not None:
        guides.append((iid, item["name"], item["purpose"], item.get("source", "―"), aspect_labels(item, char_labels)))
    lines.append(fill_block(iid))
    lines.append("")
    # 非機能を展開する項目は、明細を親と並列に置く。親のFILL内へ入れ子にすると、
    # 明細の見出しが親の本文と見なされ、親が空でも常に「充足」と判定されてしまう。
    if item.get("expands") == "non_functional":
        lines.extend(render_non_functional(iid, non_functional))
    return lines


def render_non_functional(parent_id: str, non_functional: dict) -> list[str]:
    """35の非機能明細を大項目ごとの節にする。

    記入済み文書では各明細に根拠と結論が入る。表のセルへ押し込むと1セルが長大になり、
    `-` は表セル内でリストとして描画されない。空テンプレートの行数より、記入後の
    可読性を優先する（設計書 2026-07-19 §5.6）。
    明細は見出しにせず太字ラベルにする。見出しにすると6階層目が生まれ、
    「見出しは3階層まで」のチャンク化原則に反するため。
    """
    lines = ["#### 非機能要件の個別明細", ""]
    lines.append("観点ごとに目標値・方式を記入する。確認指標は記入の手がかり。")
    lines.append("適用外は `[対象外: 理由]`、未定は `[要確認: 質問]` と書く。")
    lines.append("")
    for major in non_functional["major_items"]:
        lines.append(f"##### {major['label']}")
        lines.append("")
        for index, sub in enumerate(major["sub_items"], start=1):
            is_required = bool(major.get("required", True) and sub.get("required", True))
            sub_id = f"{parent_id}--{major['id']}--{index:02d}"
            mark = "［必須］" if is_required else "［任意］"
            lines.append(f"**{sub['name']}**{mark}（確認指標: {sub['metric']}）")
            lines.append(fill_block(sub_id))
            lines.append("")
    return lines


def escape_cell(text: str) -> str:
    """表のセルを壊す文字を無害化する。"""
    return str(text).replace("|", "\\|").replace("\n", " ")


def render_appendix(guides: list) -> list[str]:
    """項目の根拠を文書末尾へ集約する（段階的開示の付録層）。"""
    out = ["---", "", "## 付録: 項目の根拠一覧", ""]
    out.append("各項目が何のためにあるかの根拠をまとめる。記入担当のAIは、FILLを埋める前に該当IDの行を読む。")
    out.append("レビューでは、項目の網羅性や存在理由を疑うときだけ参照すればよい。")
    out.append("")
    out.append("記入は次の2行を基本とする。")
    out.append("")
    out.append("```text")
    out.append("- 結論: <決めた内容・数値・条件>          # 非機能の明細では <目標値・方式・対象外理由>")
    out.append("- 根拠: [入力] ユーザーストーリー「<該当箇所>」")
    out.append("```")
    out.append("")
    out.append(f"根拠がない項目は `[要確認: 質問]`、適用対象外は `[対象外: 理由]` と書く。")
    out.append(f"「{UNFILLED}」のまま残った項目は、カバレッジ評価で未充足として数えられる。")
    out.append("")
    out.append("| ID | 項目 | 記入ガイド | 出典 | 品質観点 |")
    out.append("| --- | --- | --- | --- | --- |")
    for iid, name, purpose, source, aspects in guides:
        cells = " | ".join(escape_cell(v) for v in (f"`{iid}`", name, purpose, source, aspects))
        out.append(f"| {cells} |")
    out.append("")
    return out


def render_phase(phase_key: str, data: dict) -> str:
    ph = data["phases"][phase_key]
    char_labels = {c["id"]: c["label"] for c in data["quality_characteristics"]}
    nf = data["non_functional"]
    guides: list = []
    out = []
    out.append("---")
    out.append(f"template: {phase_key}")
    out.append(f'spec_items_version: "{data["meta"]["version"]}"')
    out.append("status: draft")
    out.append("---")
    out.append("")
    out.append(f"# {ph['label']}書テンプレート")
    out.append("")
    out.append("<!-- AUTHOR-GUIDE:START -->")
    out.append(f"> **ゴール**: {ph['goal']}")
    if ph.get("audience"):
        out.append(f"> 👥 **読み手**: {ph['audience']}")
    if ph.get("reading_hint"):
        out.append(f"> 🧭 **読み方**: {ph['reading_hint']}")
    if ph.get("legend"):
        out.append("> 🔤 **凡例**: " + " / ".join(ph["legend"]))
    if ph.get("pbr_guide"):
        out.append("> 🔎 **第三者レビュー視点（PBR）**:")
        for guide in ph["pbr_guide"]:
            out.append(f"> - {guide}")
    out.append("> 📎 **記入方法**: 末尾の「付録: 項目の根拠一覧」を参照する。")
    out.append("<!-- AUTHOR-GUIDE:END -->")
    out.append("")
    out.append("## 読者向け本文")
    out.append("")
    out.append("<!-- AUTHOR-GUIDE:START -->")
    out.append("> **記入ガイド**: この領域は品質項目の並びを写さず、案件の読者が判断する順序へ再編集する。")
    out.append("> サマリではなく、この本文だけで要件・設計判断が完結する内容にする。低リスク部分は表へ畳み、高リスク部分を深掘りする。")
    out.append("<!-- AUTHOR-GUIDE:END -->")
    out.append("")
    out.append("<!-- HUMAN:START -->")
    out.append("[要確認: 案件と読者に合わせた本文を作成してください]")
    out.append("<!-- HUMAN:END -->")
    out.append("")
    out.append("---")
    out.append("")
    out.append("<!-- AUDIT:START -->")
    out.append("## 付録: 監査用項目")
    out.append("")
    out.append("以下はカバレッジ・根拠・トレーサビリティを検査するための領域。閲覧用HTMLでは表示しない。本文を複製せず、根拠と本文見出し・IDへの参照を記録する。")
    out.append("")
    for cat in ph["categories"]:
        out.append(f"## {cat['label']}")
        out.append("")
        for item in by_priority(cat["items"]):
            out.extend(render_item(item, char_labels, nf, guides))
        if cat.get("review_checklist"):
            out.append("> 🔍 **この節で確認すべきこと**")
            for check in cat["review_checklist"]:
                out.append(f"> - {check}")
            out.append("")
    out.extend(render_appendix(guides))
    out.append("<!-- AUDIT:END -->")
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
