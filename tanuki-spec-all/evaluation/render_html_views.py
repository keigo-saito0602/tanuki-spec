#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""仕様書 Markdown から、再生成可能な自己完結 HTML ビューを作る。

Markdown/YAML が正本であり、このモジュールが出力する ``views/`` は閲覧用の
派生成果物である。外部アセット、JavaScript、現在時刻には依存しない。
"""
from __future__ import annotations

import argparse
import html
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

try:
    from markdown_it import MarkdownIt
    from markdown_it.renderer import RendererHTML
    from markdown_it.token import Token
except ImportError:
    sys.exit("markdown-it-py が必要です: python3 -m pip install -r requirements.txt")


@dataclass(frozen=True)
class Document:
    source: str
    output: str
    label: str
    role: str


DOCUMENTS = (
    Document("00_サマリ.md", "00_サマリ.html", "サマリ", "決定事項・未決事項・リスクを最初に確認"),
    Document("01_要件定義書.md", "01_要件定義書.html", "要件定義書", "実現する目的と要件を確認"),
    Document("02_基本設計書.md", "02_基本設計書.html", "基本設計書", "システム全体の設計方針を確認"),
    Document("03_詳細設計書.md", "03_詳細設計書.html", "詳細設計書", "実装に必要な詳細を確認"),
    Document("tests/04_テスト項目書.md", "04_テスト項目書.html", "テスト項目書", "検証する振る舞いを確認"),
    Document(
        "tests/requirements-traceability.md",
        "requirements-traceability.html",
        "要件トレーサビリティ",
        "要件間の対応を確認",
    ),
    Document(
        "tests/design-traceability.md",
        "design-traceability.html",
        "設計トレーサビリティ",
        "要件と設計の対応を確認",
    ),
    Document(
        "tests/system-test-cases.md",
        "system-test-cases.html",
        "システムテストケース",
        "要件とシステムテストの対応を確認",
    ),
)

STATUS_RE = re.compile(
    r"(\[(?:要確認|対象外|未記入)(?::[^\]\n]*)?\]|⚠️|❓)"
)
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---(?:\s*\n|$)", re.DOTALL)
STATUS_CLASS = {
    "要確認": "status-pending",
    "対象外": "status-excluded",
    "未記入": "status-missing",
    "⚠️": "status-warning",
    "❓": "status-pending",
}


def status_markup(text: str) -> str:
    """状態マーカーを、属性やコードではなくテキストノード内だけ装飾する。"""

    def replace(match: re.Match[str]) -> str:
        marker = match.group(0)
        key = next((item for item in STATUS_CLASS if item in marker), "要確認")
        return f'<span class="status {STATUS_CLASS[key]}">{html.escape(marker)}</span>'

    return STATUS_RE.sub(replace, html.escape(text))


def slugify(text: str, used: set[str]) -> str:
    plain = re.sub(r"<[^>]+>", "", text)
    plain = html.unescape(plain).strip().lower()
    slug = re.sub(r"[^\w\u3040-\u30ff\u3400-\u9fff-]+", "-", plain).strip("-_")
    slug = slug or "section"
    candidate = slug
    number = 2
    while candidate in used:
        candidate = f"{slug}-{number}"
        number += 1
    used.add(candidate)
    return candidate


def inline_text(token) -> str:
    if not token.children:
        return token.content
    return "".join(child.content for child in token.children if child.type in {"text", "code_inline"})


def safe_link_target(target: str) -> bool:
    """相対リンクと明示的に許可したURLだけを通す。"""
    decoded = html.unescape(unquote(target))
    normalized = "".join(character for character in decoded if ord(character) >= 0x20).strip()
    parsed = urlsplit(normalized)
    if parsed.scheme.lower() not in {"", "http", "https", "mailto"}:
        return False
    return not (not parsed.scheme and parsed.netloc)


def sanitize_links(tokens: list[Token]) -> None:
    """危険なリンクを実行できないspanへ変える。"""
    for token in tokens:
        if not token.children:
            continue
        unsafe_stack: list[bool] = []
        for child in token.children:
            if child.type == "link_open":
                unsafe = not safe_link_target(child.attrGet("href") or "")
                unsafe_stack.append(unsafe)
                if unsafe:
                    child.type = "span_open"
                    child.tag = "span"
                    child.attrs = {"class": "unsafe-link"}
            elif child.type == "link_close":
                unsafe = unsafe_stack.pop() if unsafe_stack else False
                if unsafe:
                    child.type = "span_close"
                    child.tag = "span"


class SafeViewRenderer(RendererHTML):
    """画像を埋め込まず、状態表示・表アクセシビリティを加えるレンダラ。"""

    def text(self, tokens, idx, options, env) -> str:  # noqa: ANN001
        return status_markup(tokens[idx].content)

    def image(self, tokens, idx, options, env) -> str:  # noqa: ANN001
        token = tokens[idx]
        alt = token.content
        if token.children:
            alt = "".join(child.content for child in token.children)
        return f'<span class="image-alt">画像: {html.escape(alt)}</span>'

    def table_open(self, tokens, idx, options, env) -> str:  # noqa: ANN001
        return (
            '<div class="table-scroll" tabindex="0" role="region" '
            'aria-label="表（横方向にスクロールできます）">'
            "<table><caption>文書内の表</caption>"
        )

    def table_close(self, tokens, idx, options, env) -> str:  # noqa: ANN001
        return "</table></div>\n"

    def th_open(self, tokens, idx, options, env) -> str:  # noqa: ANN001
        return '<th scope="col">'


def markdown_to_html(markdown: str) -> tuple[str, list[tuple[int, str, str]]]:
    """安全な HTML 本文と、目次用の (level, title, id) を返す。"""
    frontmatter = FRONTMATTER_RE.match(markdown)
    if frontmatter:
        markdown = markdown[frontmatter.end():]
    md = MarkdownIt(
        "commonmark",
        {"html": False, "linkify": False, "typographer": False},
        renderer_cls=SafeViewRenderer,
    ).enable("table")
    tokens = md.parse(markdown)
    sanitize_links(tokens)
    headings: list[tuple[int, str, str]] = []
    used: set[str] = set()
    last_level = 1
    collapsible: dict[int, int] = {}
    for index, token in enumerate(tokens):
        if token.type != "heading_open":
            continue
        original = int(token.tag[1])
        level = min(6, original + 1)
        level = min(level, last_level + 1)
        title = inline_text(tokens[index + 1])
        anchor = slugify(title, used)
        token.tag = f"h{level}"
        token.attrSet("id", anchor)
        tokens[index + 2].tag = f"h{level}"
        headings.append((level, title, anchor))
        if re.search(r"(?:付録|根拠|記入ガイド|補足)", title):
            collapsible[index] = level
        last_level = level
    if collapsible:
        wrapped: list[Token] = []
        opened_level: int | None = None
        for index, token in enumerate(tokens):
            if token.type == "heading_open" and opened_level is not None:
                level = int(token.tag[1])
                if level <= opened_level:
                    close = Token("html_block", "", 0)
                    close.content = "</details>\n"
                    wrapped.append(close)
                    opened_level = None
            if index in collapsible and opened_level is None:
                opening = Token("html_block", "", 0)
                title = inline_text(tokens[index + 1])
                opening.content = (
                    '<details class="supporting-detail" open><summary>'
                    f"「{html.escape(title)}」詳細を表示/折りたたむ</summary>\n"
                )
                wrapped.append(opening)
                opened_level = collapsible[index]
            wrapped.append(token)
        if opened_level is not None:
            close = Token("html_block", "", 0)
            close.content = "</details>\n"
            wrapped.append(close)
        tokens = wrapped
    return md.renderer.render(tokens, md.options, {}), headings


def toc_html(headings: list[tuple[int, str, str]]) -> str:
    if not headings:
        return '<p class="muted">本文に見出しはありません。</p>'
    return '<ol class="toc-list">' + "".join(
        f'<li class="toc-level-{level}"><a href="#{html.escape(anchor, quote=True)}">{html.escape(title)}</a></li>'
        for level, title, anchor in headings
    ) + "</ol>"


CSS = """
:root{color-scheme:light dark;--bg:#fff;--panel:#f5f7fa;--text:#17202a;--muted:#52606d;
--line:#b8c2cc;--link:#075ea8;--focus:#d97706;--pending:#fff2cc;--excluded:#e8edf2;
--missing:#ffe4e6;--warning:#fff0d5}*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:var(--background-primary,var(--bg));color:var(--text-normal,var(--text));font-family:system-ui,-apple-system,
"Hiragino Sans","Yu Gothic UI",sans-serif;font-size:1rem;line-height:1.65}
a{color:var(--link-color,var(--link));text-underline-offset:.2em}a:focus-visible,summary:focus-visible,
.table-scroll:focus-visible{outline:3px solid var(--focus);outline-offset:3px}
.skip-link{position:absolute;left:.5rem;top:-5rem;background:var(--text);color:var(--bg);
padding:.6rem;z-index:10}.skip-link:focus{top:.5rem}.page-header,.page-footer{background:var(--background-secondary,var(--panel));
border-block:1px solid var(--background-modifier-border,var(--line));padding:1rem clamp(1rem,4vw,3rem)}
.derived{border-left:.35rem solid var(--focus);padding:.75rem 1rem;background:var(--panel)}
.meta{display:flex;flex-wrap:wrap;gap:.5rem 1.5rem;color:var(--muted)}
.layout{display:grid;grid-template-columns:minmax(12rem,19rem) minmax(0,1fr);
gap:clamp(1rem,4vw,3rem);max-width:110rem;margin:auto;padding:2rem clamp(1rem,4vw,3rem)}
.toc{align-self:start;position:sticky;top:1rem;max-height:calc(100vh - 2rem);overflow:auto}
.toc-list{padding-left:1.3rem}.toc-level-3{margin-left:.75rem}.toc-level-4,
.toc-level-5,.toc-level-6{margin-left:1.5rem}.content{min-width:0}.prose{max-width:75ch}
.prose h2,.prose h3,.prose h4,.prose h5,.prose h6{scroll-margin-top:1rem;margin-top:2em;
margin-bottom:.5em;line-height:1.3}.table-scroll{max-width:100%;overflow-x:auto;margin:1.5rem 0}
.prose :is(h2,h3,h4,h5,h6):target{outline:3px solid var(--focus);outline-offset:.25rem}
.supporting-detail{border-left:.2rem solid var(--line);padding-left:1rem;margin-block:1.5rem}
.supporting-detail summary{cursor:pointer;font-weight:700}
table{border-collapse:collapse;min-width:100%;background:var(--bg)}caption{text-align:left;
font-weight:700;padding:.5rem 0}th,td{border:1px solid var(--line);padding:.55rem .7rem;
text-align:left;vertical-align:top;overflow-wrap:anywhere}th{background:var(--panel)}
code,pre{font-family:ui-monospace,SFMono-Regular,Consolas,monospace}pre{overflow:auto;padding:1rem;
border:1px solid var(--line);background:var(--panel)}blockquote{margin-left:0;border-left:.3rem solid
var(--line);padding:.25rem 1rem;color:var(--muted)}.status{display:inline-block;border:1px solid
currentColor;border-radius:.3rem;padding:0 .25rem;font-weight:650;color:#512b00}
.status-pending{background:var(--pending)}.status-excluded{background:var(--excluded)}
.status-missing{background:var(--missing)}.status-warning{background:var(--warning)}
.image-alt{display:inline-block;border:1px dashed var(--line);padding:.25rem;color:var(--muted)}
.nav-links{display:flex;justify-content:space-between;gap:1rem;flex-wrap:wrap}.cards{list-style:none;
padding:0;display:grid;grid-template-columns:repeat(auto-fit,minmax(16rem,1fr));gap:1rem}
.card{border:1px solid var(--line);border-radius:.5rem;padding:1rem;background:var(--panel)}
.muted{color:var(--muted)}
@media(prefers-color-scheme:dark){:root{--bg:#111820;--panel:#1c2630;--text:#f1f5f9;
--muted:#bdc8d3;--line:#607080;--link:#86c8ff;--focus:#ffc857;--pending:#503c00;
--excluded:#273747;--missing:#55252d;--warning:#543400}.status{color:var(--text)}}
@media(max-width:48rem){.layout{grid-template-columns:1fr}.toc{position:static;max-height:none}}
@media print{.skip-link,.toc,.nav-links{display:none}.layout{display:block;padding:0}.page-header,
.page-footer{background:none}.prose{max-width:none}a{color:inherit;text-decoration:none}
.table-scroll{overflow:visible}.supporting-detail{display:block}.supporting-detail>summary{list-style:none}
body{font-size:11pt}}
"""

SECURITY_META = """<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src 'none'; font-src 'none'; script-src 'none'; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'">
<meta name="referrer" content="no-referrer">"""


def source_updated(path: Path) -> str:
    """frontmatterの更新日を返す。ファイルシステム時刻には依存しない。"""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return "正本に記載なし"
    match = FRONTMATTER_RE.match(text)
    if not match:
        return "正本に記載なし"
    frontmatter = match.group(1)
    for field in ("updated", "date"):
        value = re.search(rf"(?m)^{field}:\s*[\"']?([^\"'\n]+?)[\"']?\s*$", frontmatter)
        if value and value.group(1).strip():
            return value.group(1).strip()
    return "正本に記載なし"


def phase_label(phase_dir: Path) -> str:
    name = re.sub(r"^phase-[^_-]+[_-]?", "", phase_dir.name)
    return name.replace("_", " ") or phase_dir.name


def source_href(document: Document) -> str:
    return "../" + document.source


def page_html(
    phase_dir: Path,
    document: Document,
    markdown: str,
    previous: Document | None,
    following: Document | None,
) -> str:
    body, headings = markdown_to_html(markdown)
    phase = phase_label(phase_dir)
    source = source_href(document)
    previous_link = (
        f'<a rel="prev" href="{quote(previous.output)}">← 前へ: {html.escape(previous.label)}</a>'
        if previous else "<span></span>"
    )
    next_link = (
        f'<a rel="next" href="{quote(following.output)}">次へ: {html.escape(following.label)} →</a>'
        if following else "<span></span>"
    )
    return f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">{SECURITY_META}
<title>{html.escape(document.label)} — {html.escape(phase)}</title><style>{CSS}</style></head>
<body><a class="skip-link" href="#main">本文へ移動</a>
<header class="page-header"><nav aria-label="パンくず"><a href="index.html">フェーズ入口</a> / {html.escape(document.label)}</nav>
<h1>{html.escape(document.label)}</h1>
<p class="derived"><strong>閲覧用の派生成果物です。</strong> 正本は <a href="{quote(source)}">{html.escape(document.source)}</a> です。</p>
<p class="meta"><span>フェーズ: {html.escape(phase)}</span><span>文書種別: {html.escape(document.label)}</span>
<span>正本ファイル: {html.escape(document.source)}</span><span>更新日時: {source_updated(phase_dir / document.source)}</span></p>
<p>{html.escape(document.role)}。内容を補完・再解釈せず、正本Markdownを表示しています。</p></header>
<div class="layout"><nav class="toc" aria-label="目次"><h2>目次</h2>{toc_html(headings)}</nav>
<main id="main" class="content" tabindex="-1"><article class="prose">{body}</article></main></div>
<footer class="page-footer"><p><strong>状態の凡例:</strong>
<span class="status status-pending">[要確認] 未決定</span>
<span class="status status-excluded">[対象外] 意図して対象外</span>
<span class="status status-missing">[未記入] 情報不足</span></p>
<nav class="nav-links" aria-label="文書間の移動">{previous_link}
<a href="index.html">フェーズ入口へ</a>{next_link}</nav>
<p><a href="{quote(source)}">正本Markdownを開く</a></p></footer></body></html>
"""


def index_html(phase_dir: Path, available: list[Document]) -> str:
    phase = phase_label(phase_dir)
    all_update_values = [source_updated(phase_dir / doc.source) for doc in available]
    update_values = [value for value in all_update_values if value != "正本に記載なし"]
    updated = max(update_values, default="正本に記載なし")
    cards = "".join(
        f'<li class="card"><strong>{number}. <a href="{quote(doc.output)}">{html.escape(doc.label)}</a></strong>'
        f"<p>{html.escape(doc.role)}</p>"
        f'<p><a href="{quote(source_href(doc))}">正本: {html.escape(doc.source)}</a></p></li>'
        for number, doc in enumerate(available, 1)
    )
    unresolved = next(
        (
            doc for doc in available
            if STATUS_RE.search((phase_dir / doc.source).read_text(encoding="utf-8"))
        ),
        None,
    )
    unresolved_link = (
        f'<p><a href="{quote(unresolved.output)}">未決事項・注意事項を確認する</a></p>'
        if unresolved else '<p class="muted">正本内に状態マーカーは見つかりませんでした。</p>'
    )
    return f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">{SECURITY_META}
<title>{html.escape(phase)} — 仕様書ビュー</title><style>{CSS}</style></head>
<body><a class="skip-link" href="#main">本文へ移動</a><header class="page-header">
<h1>{html.escape(phase)} 仕様書ビュー</h1>
<p class="derived"><strong>読むための地図（派生成果物）です。</strong>
正本はフェーズ配下のMarkdown/YAMLであり、HTMLは編集対象ではありません。</p>
<p class="meta"><span>フェーズ: {html.escape(phase)}</span><span>正本の最終更新日時: {updated}</span></p>
</header><main id="main" class="layout" tabindex="-1"><section class="content">
<h2>読む順番</h2><p>まずサマリ、次に要件、設計、最後にテストと対応表を確認します。</p>
<ol class="cards">{cards}</ol><h2>未決事項への導線</h2>{unresolved_link}
<h2>閲覧方法</h2><p><a href="README.md">Obsidian・ブラウザでの閲覧方法と再生成方法</a></p>
</section></main><footer class="page-footer"><p>このHTMLを変更せず、正本を変更して再生成してください。</p></footer>
</body></html>
"""


def readme_text(phase_dir: Path, available: list[Document]) -> str:
    rows = "\n".join(
        f"| [{doc.output}](./{doc.output}) | [{doc.source}](../{doc.source}) | {doc.role} |"
        for doc in available
    )
    return f"""# {phase_label(phase_dir)} HTMLビュー

この `views/` は閲覧用の派生成果物です。正本は一つ上の階層にあるMarkdown/YAMLです。
HTMLを直接編集せず、正本を直してから再生成してください。各HTMLは外部通信やJavaScriptを
使わない単一ファイルで、ブラウザでも開けます。

## 閲覧

- 入口は [index.html](./index.html) です。
- Obsidianデスクトップでは Local HTML Embed コミュニティプラグインを利用できます。
  ノートに次のように、コードブロック本文の1行目へVaultルート相対パスを書きます。

````markdown
```html-embed
<Vault内のphaseパス>/views/index.html
```
````

- Local HTML Embedはデスクトップ限定です。スクリプトを許可できる設定には安全上のリスクが
  あるため、信頼済みの生成HTMLだけを表示してください（このレンダラのHTMLはスクリプトを含みません）。
- プラグインを導入しない場合は、OSのファイル操作から `index.html` をブラウザで開いてください。
- コミュニティプラグインとローカルHTMLは、信頼できるVault・生成物だけで利用してください。

## 正本との対応

| HTMLビュー | 正本 | 役割 |
| --- | --- | --- |
{rows}

## 再生成と検証

リポジトリルートから実行します。

```bash
python3 tanuki-spec-all/evaluation/render_html_views.py "<phase>"
python3 tanuki-spec-all/evaluation/render_html_views.py "<phase>" --check
```

`--check` は書き換えず、欠落・古い内容・不要になった既知HTMLを検出します。
"""


def expected_outputs(phase_dir: Path) -> tuple[dict[Path, str], list[Document]]:
    available = [doc for doc in DOCUMENTS if (phase_dir / doc.source).is_file()]
    outputs: dict[Path, str] = {}
    for index, doc in enumerate(available):
        outputs[Path(doc.output)] = page_html(
            phase_dir,
            doc,
            (phase_dir / doc.source).read_text(encoding="utf-8"),
            available[index - 1] if index else None,
            available[index + 1] if index + 1 < len(available) else None,
        )
    outputs[Path("index.html")] = index_html(phase_dir, available)
    outputs[Path("README.md")] = readme_text(phase_dir, available)
    return outputs, available


def render_phase(phase_dir: Path, check: bool = False) -> bool:
    """1フェーズを生成/検証する。成功ならTrue、差分があればFalse。"""
    phase_dir = phase_dir.resolve()
    view_dir = phase_dir / "views"
    outputs, available = expected_outputs(phase_dir)
    if view_dir.is_symlink():
        print(f"安全のため処理を中止: views がシンボリックリンクです: {view_dir}")
        return False
    known_names = {"index.html", "README.md", *(doc.output for doc in DOCUMENTS)}
    linked_outputs = [
        view_dir / name for name in known_names if (view_dir / name).is_symlink()
    ]
    if linked_outputs:
        for path in sorted(linked_outputs, key=os.fspath):
            print(f"安全のため処理を中止: 既知の出力がシンボリックリンクです: {path}")
        return False
    wanted_html = {path.name for path in outputs if path.suffix == ".html"}
    known_html = {doc.output for doc in DOCUMENTS}
    stale = sorted(
        path for path in view_dir.glob("*.html")
        if path.name in known_html and path.name not in wanted_html
    ) if view_dir.exists() else []
    mismatches = [
        relative for relative, content in outputs.items()
        if not (view_dir / relative).is_file()
        or (view_dir / relative).read_text(encoding="utf-8") != content
    ]
    skipped = [doc.source for doc in DOCUMENTS if doc not in available]
    if check:
        for source in skipped:
            print(f"スキップ: {source}（正本なし）")
        for relative in mismatches:
            print(f"不一致: {view_dir / relative}")
        for path in stale:
            print(f"不要: {path}")
        if mismatches or stale:
            return False
        print(f"検証: {view_dir}")
        return True

    view_dir.mkdir(parents=True, exist_ok=True)
    for path in stale:
        path.unlink()
        print(f"削除: {path}")
    for relative, content in outputs.items():
        (view_dir / relative).write_text(content, encoding="utf-8")
        print(f"生成: {view_dir / relative}")
    for source in skipped:
        print(f"スキップ: {source}（正本なし）")
    return True


def discover_phase_dirs(paths: list[Path]) -> list[Path]:
    """指定先そのもの、または標準 ``docs/spec/phase-*`` 配下を探索する。"""
    roots = paths or [Path.cwd()]
    found: set[Path] = set()
    for root in roots:
        root = root.resolve()
        if root.is_dir() and (
            root.name.startswith("phase-")
            or any((root / doc.source).is_file() for doc in DOCUMENTS)
        ):
            found.add(root)
            continue
        spec_root = root / "docs" / "spec"
        search_root = spec_root if spec_root.is_dir() else root
        found.update(path.resolve() for path in search_root.glob("phase-*") if path.is_dir())
    return sorted(found, key=os.fspath)


def main() -> None:
    parser = argparse.ArgumentParser(description="正本Markdownから自己完結HTMLビューを生成")
    parser.add_argument(
        "paths", type=Path, nargs="*", help="フェーズディレクトリ、または標準docs/specを含むルート"
    )
    parser.add_argument("--check", action="store_true", help="生成物との差分を読み取り専用で検証")
    args = parser.parse_args()
    phase_dirs = discover_phase_dirs(args.paths)
    if not phase_dirs:
        parser.error("フェーズディレクトリが見つかりません")
    results = [render_phase(path, check=args.check) for path in phase_dirs]
    success = all(results)
    if not success:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
