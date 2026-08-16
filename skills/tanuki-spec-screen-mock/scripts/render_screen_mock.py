#!/usr/bin/env python3
"""screens.yamlとdesign-tokens.jsonから単一HTMLの画面モックを合成する。

YAMLは `trace:` と書いて値を省くとNoneになる。dict.getの既定値はキーが無いときにしか
働かないため、`get("trace", [])` ではNoneが素通りしてイテレートで落ちる。配列・辞書を
受け取る箇所はすべて `screen.get("trace") or []` の形でNoneを既定値へ寄せる。
"""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = SKILL_DIR / "assets" / "screen-mock.html"

STATE_LABELS = {
    "normal": "通常",
    "empty": "空",
    "loading": "読込中",
    "error": "エラー",
    "forbidden": "権限なし",
}
KIND_CLASS = {"forward": "btn", "back": "btn btn-sub", "cancel": "btn btn-sub"}

# alert の種別文言・アイコン・境界線。色以外でエラーと権限なしを見分けるための手掛かり。
# 境界線はborder-styleも変えており、色覚だけに頼らない形で区別できる。
ALERT_KIND_LABEL = {"error": "エラー", "forbidden": "権限がありません"}
ALERT_ICON = {"error": "⚠", "forbidden": "🔒"}
ALERT_BORDER = {"error": "6px double #b3261e", "forbidden": "4px dashed #5f6368"}

# 視覚的には隠すがスクリーンリーダーには読ませる（sr-onlyパターン）ためのインライン指定。
# 共有CSS（assets/screen-mock.html）には手を入れず、部品側で完結させる。
VISUALLY_HIDDEN_STYLE = (
    "position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;"
    "clip:rect(0,0,0,0);white-space:nowrap;border:0"
)


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _labelled(kind: str, body: str, state: Any = None) -> str:
    state_attr = f' data-state="{esc(state)}"' if isinstance(state, str) and state else ""
    return f'<div class="blk"{state_attr}><div class="blk-label">{esc(kind)}</div>{body}</div>'


def _render_field(field: dict) -> str:
    label = esc(field.get("label", "項目"))
    required = "<strong>（必須）</strong>" if field.get("required") else ""
    constraint = field.get("constraint")
    hint = f'<div class="hint">{esc(constraint)}</div>' if isinstance(constraint, str) and constraint else ""
    error = field.get("error")
    error_html = (
        f'<div class="field-error" style="border-left:4px solid #b3261e;padding-left:.5rem">'
        f'<span aria-hidden="true">⚠</span> {esc(error)}</div>'
        if isinstance(error, str) and error
        else ""
    )
    return f'<div class="box">{label}{required}{hint}{error_html}</div>'


def render_block(block: Any) -> str:
    if not isinstance(block, dict):
        return ""
    kind = block.get("type", "unknown")

    if kind == "header":
        items = "".join(f'<a href="#">{esc(item)}</a>' for item in (block.get("nav") or []))
        return _labelled(kind, f'<div class="bar">{items or "ナビゲーション"}</div>')

    if kind in ("filter-bar", "form-section"):
        cells = "".join(_render_field(field) for field in (block.get("fields") or []) if isinstance(field, dict))
        return _labelled(kind, f'<div class="grid">{cells}</div>')

    if kind == "card-grid":
        label = esc(block.get("item_label", "項目"))
        fields = "".join(f"<div>{esc(name)}</div>" for name in (block.get("item_fields") or []))
        card = f'<div class="box"><strong>{label}</strong>{fields}</div>'
        return _labelled(kind, f'<div class="grid">{card * 3}</div>')

    if kind == "table":
        columns = block.get("columns") or ["列1", "列2"]
        head = "".join(f'<th scope="col">{esc(name)}</th>' for name in columns)
        body = "".join("<td>—</td>" for _ in columns)
        table = (
            f'<div class="tbl-wrap" tabindex="0"><table><caption>{esc(block.get("caption", "一覧"))}</caption>'
            f"<thead><tr>{head}</tr></thead><tbody><tr>{body}</tr><tr>{body}</tr></tbody></table></div>"
        )
        return _labelled(kind, table)

    if kind == "button-row":
        buttons = block.get("buttons") or ["操作"]
        rendered = "".join(
            f'<button type="button" class="btn{"" if index == 0 else " btn-sub"}">{esc(name)}</button>'
            for index, name in enumerate(buttons)
        )
        return _labelled(kind, f"<div>{rendered}</div>")

    if kind == "list":
        items = "".join(f'<li class="box">{esc(item)}</li>' for item in (block.get("items") or ["項目"]))
        return _labelled(kind, f'<ul style="list-style:none;padding:0;margin:0">{items}</ul>')

    if kind == "empty-state":
        state = block.get("state")
        message = block.get("message") or block.get("text") or ""
        body = (
            '<div class="box state-empty">'
            '<span class="state-icon" aria-hidden="true">🗂</span>'
            '<strong class="state-heading">データがありません</strong>'
            f'<p class="state-message">{esc(message)}</p>'
            "</div>"
        )
        return _labelled(kind, body, state)

    if kind == "loading":
        state = block.get("state")
        message = block.get("message") or "しばらくお待ちください"
        body = (
            f'<div class="box state-loading" aria-hidden="true"><span class="state-spinner"></span>{esc(message)}</div>'
            f'<p aria-live="polite" style="{VISUALLY_HIDDEN_STYLE}">読み込み中</p>'
        )
        return _labelled(kind, body, state)

    if kind == "alert":
        state = block.get("state")
        kind_label = ALERT_KIND_LABEL.get(state, "通知")
        icon = ALERT_ICON.get(state, "ℹ")
        border = ALERT_BORDER.get(state, "4px solid #5f6368")
        message = block.get("message") or block.get("text") or ""
        state_class = f" alert-{esc(state)}" if isinstance(state, str) and state else ""
        body = (
            f'<div class="box alert{state_class}" style="border-left:{border};padding-left:.8rem">'
            f'<span class="state-icon" aria-hidden="true">{icon}</span> '
            f'<strong class="state-kind">{esc(kind_label)}</strong>'
            f'<p class="state-message">{esc(message)}</p>'
            "</div>"
        )
        return _labelled(kind, body, state)

    text = block.get("text") or block.get("label") or kind
    return _labelled(kind, f'<div class="box">{esc(text)}</div>')


def _render_exploration(screen: dict) -> str:
    """画面を採用判断と検証課題まで含めてレビューできるようにする。"""

    strategy = screen.get("state_strategy") or {}
    priority_states = "／".join(
        STATE_LABELS.get(str(state), str(state)) for state in (strategy.get("priority_states") or [])
    ) or "未記入"
    exploration_mode = screen.get("exploration_mode", "未記入")
    mode_label = {"compare": "比較検討", "inherit": "既存パターンを継承"}.get(
        str(exploration_mode), str(exploration_mode)
    )
    inherited_from = screen.get("inherited_from")
    inherited_row = (
        f"<dt>継承元</dt><dd>{esc(inherited_from)}</dd>"
        if isinstance(inherited_from, str) and inherited_from.strip()
        else ""
    )
    rows = []
    for alternative in screen.get("alternatives") or []:
        if not isinstance(alternative, dict):
            continue
        decision = alternative.get("decision", "未記入")
        decision_label = {"adopted": "採用", "rejected": "却下"}.get(str(decision), str(decision))
        rows.append(
            f"<tr><th scope=\"row\">{esc(alternative.get('name', ''))}</th>"
            f"<td>{esc(alternative.get('summary', ''))}</td>"
            f"<td>{esc(decision_label)}</td>"
            f"<td>{esc(alternative.get('reason', ''))}</td></tr>"
        )
    alternatives = "".join(rows) or '<tr><td colspan="4">比較案が未記入です</td></tr>'
    return f"""<div class="exploration">
    <h3>デザイン探索と検証</h3>
    <dl>
      <dt>デザイン問い</dt><dd>{esc(screen.get('design_question', '未記入'))}</dd>
      <dt>仮説</dt><dd>{esc(screen.get('hypothesis', '未記入'))}</dd>
      <dt>リスク</dt><dd>{esc(screen.get('risk', '未記入'))}</dd>
      <dt>検証タスク</dt><dd>{esc(screen.get('validation_task', '未記入'))}</dd>
      <dt>採用根拠</dt><dd>{esc(screen.get('rationale', '未記入'))}</dd>
      <dt>探索方法</dt><dd>{esc(mode_label)}</dd>
      {inherited_row}
      <dt>重点状態</dt><dd>{esc(priority_states)}</dd>
      <dt>状態設計の理由</dt><dd>{esc(strategy.get('rationale', '未記入'))}</dd>
    </dl>
    <div class="tbl-wrap" tabindex="0"><table><caption>採用案と代替案</caption>
      <thead><tr><th scope="col">案</th><th scope="col">概要</th><th scope="col">採否</th><th scope="col">理由</th></tr></thead>
      <tbody>{alternatives}</tbody>
    </table></div>
  </div>"""


def render_screen(screen: Any) -> str:
    if not isinstance(screen, dict):
        return ""
    screen_id = esc(screen.get("id", "SC-000"))
    blocks = "".join(render_block(block) for block in (screen.get("blocks") or []))

    states = screen.get("states") or {}
    state_rows = "".join(
        f"<tr><th scope=\"row\">{esc(STATE_LABELS.get(key, key))}</th><td>{esc(states.get(key, '未記入'))}</td></tr>"
        for key in STATE_LABELS
    )

    links = "".join(
        f'<a class="{KIND_CLASS.get(t.get("kind"), "btn btn-sub")}" href="#{esc(t.get("to"))}">'
        f'{esc(t.get("action", "遷移"))} → {esc(t.get("to"))}</a> '
        for t in (screen.get("transitions") or [])
        if isinstance(t, dict)
    )
    trace = "／".join(esc(item) for item in (screen.get("trace") or [])) or "未対応"
    notes = "".join(
        f'<p><span class="badge badge-check">要確認</span> {esc(note)}</p>'
        for note in (screen.get("notes") or [])
    )

    return f"""<section class="screen" id="{screen_id}">
  <div class="screen-head">
    <h2>{screen_id} {esc(screen.get('name', ''))}</h2>
    <p>{esc(screen.get('purpose', ''))}／操作者: {esc(screen.get('actor', ''))}</p>
  </div>
  {_render_exploration(screen)}
  <div class="canvas">{blocks}</div>
  <div class="meta">
    <dl>
      <dt>対応要件</dt><dd>{trace}</dd>
      <dt>遷移</dt><dd>{links or '終端画面'}</dd>
    </dl>
    <div class="tbl-wrap" tabindex="0"><table><caption>この画面の5状態</caption><tbody>{state_rows}</tbody></table></div>
    {notes}
  </div>
</section>"""


def render_nav(screens: Any) -> str:
    if not isinstance(screens, list):
        return ""
    links = "".join(
        f'<a href="#{esc(s.get("id"))}">{esc(s.get("id"))} {esc(s.get("name", ""))}</a>'
        for s in screens
        if isinstance(s, dict)
    )
    return f"<h2>画面一覧</h2>{links}"


def render_diagram(screens: Any) -> str:
    rows: list[str] = []
    for screen in screens if isinstance(screens, list) else []:
        if not isinstance(screen, dict):
            continue
        transitions = screen.get("transitions") or []
        if not transitions:
            rows.append(
                f'<tr><th scope="row">{esc(screen.get("id"))} {esc(screen.get("name", ""))}</th>'
                f"<td>終端</td><td>—</td></tr>"
            )
            continue
        for transition in transitions:
            if not isinstance(transition, dict):
                continue
            rows.append(
                f'<tr><th scope="row">{esc(screen.get("id"))} {esc(screen.get("name", ""))}</th>'
                f'<td>{esc(transition.get("action", ""))}</td>'
                f'<td><a href="#{esc(transition.get("to"))}">{esc(transition.get("to"))}</a></td></tr>'
            )
    body = "".join(rows) or '<tr><td colspan="3">遷移がありません</td></tr>'
    return (
        '<div class="tbl-wrap" tabindex="0"><table><caption>遷移元・操作・遷移先の一覧</caption>'
        '<thead><tr><th scope="col">遷移元</th><th scope="col">操作</th><th scope="col">遷移先</th></tr></thead>'
        f"<tbody>{body}</tbody></table></div>"
    )


def render_trace(screens: Any, token_data: Any) -> str:
    from tokens import unconfirmed

    mapping: dict[str, list[str]] = {}
    notes: list[str] = []
    for screen in screens if isinstance(screens, list) else []:
        if not isinstance(screen, dict):
            continue
        for requirement in (screen.get("trace") or []):
            mapping.setdefault(str(requirement), []).append(str(screen.get("id")))
        for note in (screen.get("notes") or []):
            notes.append(f"{screen.get('id')}: {note}")

    trace_rows = "".join(
        f'<tr><th scope="row">{esc(requirement)}</th><td>{esc("／".join(ids))}</td></tr>'
        for requirement, ids in sorted(mapping.items())
    ) or '<tr><td colspan="2">対応する要件が書かれていません</td></tr>'

    token_rows = "".join(
        f'<tr><th scope="row">{esc(name)}</th><td>{esc(source)}</td><td>{esc(confidence)}</td></tr>'
        for name, source, confidence in unconfirmed(token_data)
    ) or '<tr><td colspan="3">すべて確定済みです</td></tr>'

    note_items = "".join(f"<li>{esc(note)}</li>" for note in notes) or "<li>ありません</li>"

    return f"""<h2>要件と画面の対応</h2>
<div class="tbl-wrap" tabindex="0"><table><caption>要件IDごとの担当画面</caption>
<thead><tr><th scope="col">要件ID</th><th scope="col">画面</th></tr></thead>
<tbody>{trace_rows}</tbody></table></div>
<h2>確定していないデザイントークン</h2>
<div class="tbl-wrap" tabindex="0"><table><caption>抽出元と確度</caption>
<thead><tr><th scope="col">トークン</th><th scope="col">抽出元</th><th scope="col">確度</th></tr></thead>
<tbody>{token_rows}</tbody></table></div>
<h2>要確認事項</h2>
<ul>{note_items}</ul>"""


def render(screens_data: Any, token_data: Any, template: str | None = None) -> str:
    from tokens import to_css_variables

    source = template if template is not None else TEMPLATE_PATH.read_text(encoding="utf-8")
    screens = (screens_data.get("screens") or []) if isinstance(screens_data, dict) else []
    meta = (screens_data.get("meta") or {}) if isinstance(screens_data, dict) else {}
    title = esc(meta.get("phase") or "画面")

    replacements = {
        "<!--TITLE-->": title,
        "<!--TOKENS-->": to_css_variables(token_data),
        "<!--NAV-->": render_nav(screens),
        "<!--SCREENS-->": "".join(render_screen(screen) for screen in screens),
        "<!--DIAGRAM-->": render_diagram(screens),
        "<!--TRACE-->": render_trace(screens, token_data),
    }
    for marker, value in replacements.items():
        source = source.replace(marker, value)
    return source


def main(argv: list[str] | None = None) -> int:
    import argparse
    import json

    import yaml

    parser = argparse.ArgumentParser(description="画面モックHTMLを生成する")
    parser.add_argument("screens", type=Path, help="screens.yaml")
    parser.add_argument("tokens", type=Path, help="design-tokens.json")
    parser.add_argument("--output", type=Path, required=True, help="出力先HTML")
    args = parser.parse_args(argv)

    screens_data = yaml.safe_load(args.screens.read_text(encoding="utf-8"))
    token_data = json.loads(args.tokens.read_text(encoding="utf-8"))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(screens_data, token_data), encoding="utf-8")
    print(f"画面モックを書き出しました: {args.output}")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
