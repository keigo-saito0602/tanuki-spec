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
        '<div class="tbl-wrap"><table><caption>遷移元・操作・遷移先の一覧</caption>'
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
        for requirement in screen.get("trace", []):
            mapping.setdefault(str(requirement), []).append(str(screen.get("id")))
        for note in screen.get("notes", []):
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
<div class="tbl-wrap"><table><caption>要件IDごとの担当画面</caption>
<thead><tr><th scope="col">要件ID</th><th scope="col">画面</th></tr></thead>
<tbody>{trace_rows}</tbody></table></div>
<h2>確定していないデザイントークン</h2>
<div class="tbl-wrap"><table><caption>抽出元と確度</caption>
<thead><tr><th scope="col">トークン</th><th scope="col">抽出元</th><th scope="col">確度</th></tr></thead>
<tbody>{token_rows}</tbody></table></div>
<h2>要確認事項</h2>
<ul>{note_items}</ul>"""


def render(screens_data: Any, token_data: Any, template: str | None = None) -> str:
    from tokens import to_css_variables

    source = template if template is not None else TEMPLATE_PATH.read_text(encoding="utf-8")
    screens = screens_data.get("screens", []) if isinstance(screens_data, dict) else []
    meta = screens_data.get("meta", {}) if isinstance(screens_data, dict) else {}
    title = esc(meta.get("phase", "画面"))

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
