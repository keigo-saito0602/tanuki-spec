#!/usr/bin/env python3
"""screens.yamlとdesign-tokens.jsonから単一HTMLの画面モックを合成する。"""

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


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _labelled(kind: str, body: str) -> str:
    return f'<div class="blk"><div class="blk-label">{esc(kind)}</div>{body}</div>'


def render_block(block: Any) -> str:
    if not isinstance(block, dict):
        return ""
    kind = block.get("type", "unknown")

    if kind == "header":
        items = "".join(f'<a href="#">{esc(item)}</a>' for item in block.get("nav", []))
        return _labelled(kind, f'<div class="bar">{items or "ナビゲーション"}</div>')

    if kind in ("filter-bar", "form-section"):
        cells = "".join(
            f'<div class="box">{esc(field.get("label", "項目"))}'
            f'{"<strong>（必須）</strong>" if field.get("required") else ""}</div>'
            for field in block.get("fields", [])
            if isinstance(field, dict)
        )
        return _labelled(kind, f'<div class="grid">{cells}</div>')

    if kind == "card-grid":
        label = esc(block.get("item_label", "項目"))
        fields = "".join(f"<div>{esc(name)}</div>" for name in block.get("item_fields", []))
        card = f'<div class="box"><strong>{label}</strong>{fields}</div>'
        return _labelled(kind, f'<div class="grid">{card * 3}</div>')

    if kind == "table":
        columns = block.get("columns", ["列1", "列2"])
        head = "".join(f'<th scope="col">{esc(name)}</th>' for name in columns)
        body = "".join("<td>—</td>" for _ in columns)
        table = (
            f'<div class="tbl-wrap"><table><caption>{esc(block.get("caption", "一覧"))}</caption>'
            f"<thead><tr>{head}</tr></thead><tbody><tr>{body}</tr><tr>{body}</tr></tbody></table></div>"
        )
        return _labelled(kind, table)

    if kind == "button-row":
        buttons = block.get("buttons", ["操作"])
        rendered = "".join(
            f'<span class="btn{"" if index == 0 else " btn-sub"}">{esc(name)}</span>'
            for index, name in enumerate(buttons)
        )
        return _labelled(kind, f"<div>{rendered}</div>")

    if kind == "list":
        items = "".join(f'<li class="box">{esc(item)}</li>' for item in block.get("items", ["項目"]))
        return _labelled(kind, f'<ul style="list-style:none;padding:0;margin:0">{items}</ul>')

    text = block.get("text") or block.get("label") or kind
    return _labelled(kind, f'<div class="box">{esc(text)}</div>')


def render_screen(screen: Any) -> str:
    if not isinstance(screen, dict):
        return ""
    screen_id = esc(screen.get("id", "SC-000"))
    blocks = "".join(render_block(block) for block in screen.get("blocks", []))

    states = screen.get("states", {})
    state_rows = "".join(
        f"<tr><th scope=\"row\">{esc(STATE_LABELS.get(key, key))}</th><td>{esc(states.get(key, '未記入'))}</td></tr>"
        for key in STATE_LABELS
    )

    links = "".join(
        f'<a class="{KIND_CLASS.get(t.get("kind"), "btn btn-sub")}" href="#{esc(t.get("to"))}">'
        f'{esc(t.get("action", "遷移"))} → {esc(t.get("to"))}</a> '
        for t in screen.get("transitions", [])
        if isinstance(t, dict)
    )
    trace = "／".join(esc(item) for item in screen.get("trace", [])) or "未対応"
    notes = "".join(
        f'<p><span class="badge badge-check">要確認</span> {esc(note)}</p>'
        for note in screen.get("notes", [])
    )

    return f"""<section class="screen" id="{screen_id}">
  <div class="screen-head">
    <h2>{screen_id} {esc(screen.get('name', ''))}</h2>
    <p>{esc(screen.get('purpose', ''))}／操作者: {esc(screen.get('actor', ''))}</p>
  </div>
  <div class="canvas">{blocks}</div>
  <div class="meta">
    <dl>
      <dt>対応要件</dt><dd>{trace}</dd>
      <dt>遷移</dt><dd>{links or '終端画面'}</dd>
    </dl>
    <div class="tbl-wrap"><table><caption>この画面の5状態</caption><tbody>{state_rows}</tbody></table></div>
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
