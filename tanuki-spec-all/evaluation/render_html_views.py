#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""正本の仕様書を、フェーズ単位の人間向け HTML ビューへまとめる。

Markdown/YAML は正本であり、``views/`` は常に再生成する派生成果物である。
出力はフェーズ直下の4ファイルだけに限定し、画面モックだけは別生成器の管理物として
保存する。外部アセット・JavaScript・ファイルシステム時刻には依存しない。
"""
from __future__ import annotations

import argparse
import html
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit, urlunsplit

try:
    from markdown_it import MarkdownIt
    from markdown_it.renderer import RendererHTML
    from markdown_it.token import Token
except ImportError:
    sys.exit("markdown-it-py が必要です: python3 -m pip install -r requirements.txt")


@dataclass(frozen=True)
class SourceDocument:
    """一つの正本と、束の中で表示する文書種別。"""

    path: Path
    func_name: str
    kind: str
    label: str


OUTPUT_FILES = (
    "00_サマリ.html",
    "01_要件定義書.html",
    "02_設計書.html",
    "03_テストケース.html",
)
SCREEN_MOCK = "画面モック.html"

# 既存レンダラが生成した既知のHTML。通常実行では安全に削除するが、
# 利用者が置いた未知のHTMLは保存する。
LEGACY_HTML_NAMES = {
    "index.html",
    "README.html",
    "00_サマリ.html",
    "01_要件定義書.html",
    "02_基本設計書.html",
    "03_詳細設計書.html",
    "04_テスト項目書.html",
    "design-traceability.html",
    "requirements-traceability.html",
    "system-test-cases.html",
}
LEGACY_OUTPUT_NAMES = LEGACY_HTML_NAMES | {"README.md"}
LEGACY_DIR_NAMES = {"system"}

STATUS_RE = re.compile(r"(\[(?:要確認|対象外|未記入)(?::[^\]\n]*)?\]|⚠️|❓)")
STATUS_CLASS = {
    "要確認": "status-pending",
    "対象外": "status-excluded",
    "未記入": "status-missing",
    "⚠️": "status-warning",
    "❓": "status-pending",
}
FRONTMATTER_RE = re.compile(r"\A---\s*\n.*?\n---(?:\s*\n|\Z)", re.DOTALL)
HTML_COMMENT_RE = re.compile(r"<!--.*?(?:-->|\Z)", re.DOTALL)
HEADING_RE = re.compile(r"^( {0,3})(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$", re.MULTILINE)
GUIDE_RE = re.compile(
    r"(?:記入ガイド|記入方法|記入形式|書き方|FILL|この節で確認すべきこと|ゴール|読み手|読み方|凡例|レビュー(?:観点|チェック|項目|用チェック)?|"
    r"チェックリスト|第三者レビュー|writing\s+guide|review\s+checklist|checklist)",
    re.IGNORECASE,
)
APPENDIX_RE = re.compile(
    r"(?:^|[：:・\s])(?:付録|根拠一覧|出典一覧|provenance|appendix|evidence(?:\s+index)?)(?:$|[：:・\s])",
    re.IGNORECASE,
)


def status_markup(text: str) -> str:
    """状態マーカーをエスケープ済みテキスト内だけ装飾する。"""

    escaped = html.escape(text)

    def replace(match: re.Match[str]) -> str:
        marker = match.group(0)
        key = next((item for item in STATUS_CLASS if item in marker), "要確認")
        return f'<span class="status {STATUS_CLASS[key]}">{marker}</span>'

    return STATUS_RE.sub(replace, escaped)


def safe_link_target(target: str) -> bool:
    """相対URLと http(s)/mailto だけを許可する。"""

    decoded = html.unescape(unquote(target))
    normalized = "".join(char for char in decoded if ord(char) >= 0x20).strip()
    parsed = urlsplit(normalized)
    if parsed.scheme.lower() not in {"", "http", "https", "mailto"}:
        return False
    # //host/path は scheme が空でも外部ネットワークへのURLなので拒否する。
    return not (not parsed.scheme and parsed.netloc)


def rewrite_relative_link(target: str, source: Path, phase_dir: Path) -> str:
    """正本Markdownから、views直下の出力を起点に解決できる相対URLへ変換する。"""

    if not safe_link_target(target):
        return target
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc or target.startswith("#"):
        return target
    # URLのパスだけをファイルとして解決し、query/fragmentは保持する。
    decoded_path = unquote(parsed.path)
    resolved = (source.parent / decoded_path).resolve()
    output_root = phase_dir.resolve() / "views"
    # フェーズ外（例: docs/spec/_project）へのリンクも、生成HTMLの出力
    # ルートから解決できる位置へ変換する。
    output_root_relative = Path(os.path.relpath(resolved, output_root)).as_posix()
    return urlunsplit(("", "", quote(output_root_relative, safe="/-_.~%"), parsed.query, parsed.fragment))


def strip_reader_only_content(markdown: str) -> str:
    """読者向けには不要なメタデータ・作成ガイド・出典付録を取り除く。

    この関数は入力文字列を返すだけで正本ファイルを書き換えない。
    """

    markdown = FRONTMATTER_RE.sub("", markdown, count=1)
    markdown = HTML_COMMENT_RE.sub("", markdown)
    lines = markdown.splitlines()

    # ガイド用の blockquote は、開始行から連続する引用ブロック全体を除く。
    cleaned: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if re.match(r"^ {0,3}>[ \t]?", line):
            start = index
            block: list[str] = []
            while index < len(lines):
                current = lines[index]
                if re.match(r"^ {0,3}>[ \t]?", current):
                    block.append(re.sub(r"^ {0,3}>[ \t]?", "", current))
                    index += 1
                    continue
                # 引用内の空行は次の引用行まで含める。
                if current.strip() == "" and index + 1 < len(lines) and re.match(r"^ {0,3}>", lines[index + 1]):
                    block.append("")
                    index += 1
                    continue
                break
            if GUIDE_RE.search("\n".join(block)):
                if cleaned and cleaned[-1].strip() == "":
                    cleaned.pop()
                continue
            cleaned.extend(lines[start:index])
            continue
        cleaned.append(line)
        index += 1

    # 「付録: 項目の根拠一覧」等は見出しから同階層以上の次見出しまでを除く。
    without_appendix: list[str] = []
    appendix_level: int | None = None
    for line in cleaned:
        heading = re.match(r"^ {0,3}(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$", line)
        if heading:
            level = len(heading.group(1))
            title = heading.group(2).strip()
            if appendix_level is not None and level <= appendix_level:
                appendix_level = None
            if appendix_level is None and APPENDIX_RE.search(title):
                appendix_level = level
                continue
        if appendix_level is None:
            without_appendix.append(line)
    return "\n".join(without_appendix).strip() + "\n"


class SafeViewRenderer(RendererHTML):
    """raw HTML・画像を実行/取得せず、安全な読み取り専用HTMLにする。"""

    def __init__(self, parser=None, source: Path | None = None, phase_dir: Path | None = None):
        super().__init__(parser)
        self.source = source or Path("source.md")
        self.phase_dir = phase_dir or self.source.parent

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
            'aria-label="表（横方向にスクロールできます）"><table><caption>文書内の表</caption>'
        )

    def table_close(self, tokens, idx, options, env) -> str:  # noqa: ANN001
        return "</table></div>\n"

    def th_open(self, tokens, idx, options, env) -> str:  # noqa: ANN001
        return '<th scope="col">'


def _inline_text(token: Token) -> str:
    if not token.children:
        return token.content
    return "".join(child.content for child in token.children if child.type in {"text", "code_inline"})


def slugify(text: str, used: set[str]) -> str:
    plain = html.unescape(re.sub(r"<[^>]+>", "", text)).strip().lower()
    slug = re.sub(r"[^\w\u3040-\u30ff\u3400-\u9fff-]+", "-", plain).strip("-_") or "section"
    candidate = slug
    number = 2
    while candidate in used:
        candidate = f"{slug}-{number}"
        number += 1
    used.add(candidate)
    return candidate


def markdown_to_html(
    markdown: str,
    source: Path | None = None,
    phase_dir: Path | None = None,
    anchor_prefix: str | None = None,
    heading_offset: int = 1,
) -> tuple[str, list[tuple[int, str, str]]]:
    """Markdownを安全に描画し、目次用の (level, title, id) を返す。"""

    source = source or Path("source.md")
    phase_dir = phase_dir or source.parent
    prepared = strip_reader_only_content(markdown)
    md = MarkdownIt(
        "commonmark",
        {"html": False, "linkify": False, "typographer": False},
        renderer_cls=lambda parser: SafeViewRenderer(parser, source, phase_dir),
    ).enable("table")
    tokens = md.parse(prepared)
    unsafe_stack: list[bool] = []
    for token in tokens:
        if not token.children:
            continue
        for child in token.children:
            if child.type == "link_open":
                target = child.attrGet("href") or ""
                unsafe = not safe_link_target(target)
                unsafe_stack.append(unsafe)
                if unsafe:
                    child.type = "span_open"
                    child.tag = "span"
                    child.attrs = {"class": "unsafe-link"}
                else:
                    child.attrSet("href", rewrite_relative_link(target, source, phase_dir))
            elif child.type == "link_close":
                unsafe = unsafe_stack.pop() if unsafe_stack else False
                if unsafe:
                    child.type = "span_close"
                    child.tag = "span"
    headings: list[tuple[int, str, str]] = []
    used: set[str] = set()
    for index, token in enumerate(tokens):
        if token.type != "heading_open":
            continue
        level = min(6, int(token.tag[1]) + heading_offset)
        inline = tokens[index + 1]
        original_title = _inline_text(inline)
        title = re.sub(r"^\[(?:必須|任意|条件付)\]\s*", "", original_title)
        if title != original_title:
            inline.content = title
            if inline.children:
                for child in inline.children:
                    if child.type in {"text", "code_inline"}:
                        child.content = re.sub(r"^\[(?:必須|任意|条件付)\]\s*", "", child.content, count=1)
                        break
        anchor = slugify(f"{anchor_prefix}-{title}" if anchor_prefix else title, used)
        token.tag = f"h{level}"
        token.attrSet("id", anchor)
        tokens[index + 2].tag = f"h{level}"
        headings.append((level, title, anchor))
    return md.renderer.render(tokens, md.options, {}), headings


CSS = """
:root{color-scheme:light dark;--bg:#fff;--panel:#f4f6f8;--text:#17202a;--muted:#52606d;--line:#b8c2cc;--link:#075ea8;--focus:#d97706;--pending:#fff2cc;--excluded:#e8edf2;--missing:#ffe4e6;--warning:#fff0d5}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--background-primary,var(--bg));color:var(--text-normal,var(--text));font-family:system-ui,-apple-system,"Hiragino Sans","Yu Gothic UI",sans-serif;font-size:1rem;line-height:1.65}a{color:var(--link-color,var(--link));text-underline-offset:.2em}a:focus-visible,.table-scroll:focus-visible{outline:3px solid var(--focus);outline-offset:3px}.skip-link{position:absolute;left:.5rem;top:-5rem;background:var(--text);color:var(--bg);padding:.6rem;z-index:10}.skip-link:focus{top:.5rem}.page-header,.page-footer{background:var(--background-secondary,var(--panel));border-block:1px solid var(--background-modifier-border,var(--line));padding:1rem clamp(1rem,4vw,3rem)}.derived{border-left:.35rem solid var(--focus);padding:.75rem 1rem;background:var(--panel)}.meta{display:flex;flex-wrap:wrap;gap:.5rem 1.5rem;color:var(--muted)}.layout{display:grid;grid-template-columns:minmax(12rem,19rem) minmax(0,1fr);gap:clamp(1rem,4vw,3rem);max-width:110rem;margin:auto;padding:2rem clamp(1rem,4vw,3rem)}.toc{align-self:start;position:sticky;top:1rem;max-height:calc(100vh - 2rem);overflow:auto}.toc-list{padding-left:1.3rem}.toc-level-3{margin-left:.75rem}.toc-level-4,.toc-level-5,.toc-level-6{margin-left:1.5rem}.content{min-width:0}.prose{max-width:82ch}.prose h2,.prose h3,.prose h4,.prose h5,.prose h6{scroll-margin-top:1rem;margin-top:2em;margin-bottom:.5em;line-height:1.3}.table-scroll{max-width:100%;overflow-x:auto;margin:1.5rem 0}.prose :is(h2,h3,h4,h5,h6):target{outline:3px solid var(--focus);outline-offset:.25rem}table{border-collapse:collapse;min-width:100%;background:var(--bg)}caption{text-align:left;font-weight:700;padding:.5rem 0}th,td{border:1px solid var(--line);padding:.55rem .7rem;text-align:left;vertical-align:top;overflow-wrap:anywhere}th{background:var(--panel)}code,pre{font-family:ui-monospace,SFMono-Regular,Consolas,monospace}pre{overflow:auto;padding:1rem;border:1px solid var(--line);background:var(--panel)}blockquote{margin-left:0;border-left:.3rem solid var(--line);padding:.25rem 1rem;color:var(--muted)}.status{display:inline-block;border:1px solid currentColor;border-radius:.3rem;padding:0 .25rem;font-weight:650;color:#512b00}.status-pending{background:var(--pending)}.status-excluded{background:var(--excluded)}.status-missing{background:var(--missing)}.status-warning{background:var(--warning)}.image-alt{display:inline-block;border:1px dashed var(--line);padding:.25rem;color:var(--muted)}.bundle-nav{display:flex;flex-wrap:wrap;gap:.5rem;margin:1rem 0}.bundle-nav a,.bundle-nav strong{border:1px solid var(--line);border-radius:.35rem;padding:.35rem .7rem}.bundle-nav strong{background:var(--panel)}.source-card{border:1px solid var(--line);border-radius:.5rem;padding:1rem;margin:1.25rem 0;background:var(--panel)}.source-card h2{margin-top:0}.source-card .prose{background:var(--bg);padding:1rem;border-radius:.35rem}.muted{color:var(--muted)}.coverage-nav{border:2px solid var(--focus);padding:1rem;background:var(--panel);border-radius:.5rem}.coverage-nav ul{display:flex;flex-wrap:wrap;gap:1rem;margin-bottom:0}@media(prefers-color-scheme:dark){:root{--bg:#111820;--panel:#1c2630;--text:#f1f5f9;--muted:#bdc8d3;--line:#607080;--link:#86c8ff;--focus:#ffc857;--pending:#503c00;--excluded:#273747;--missing:#55252d;--warning:#543400}.status{color:var(--text)}}@media(max-width:48rem){.layout{grid-template-columns:1fr}.toc{position:static;max-height:none}}@media print{.skip-link,.toc,.bundle-nav{display:none}.layout{display:block;padding:0}.page-header,.page-footer{background:none}.prose{max-width:none}a{color:inherit;text-decoration:none}.table-scroll{overflow:visible}body{font-size:11pt}.source-card{break-inside:avoid}}
"""
SECURITY_META = """<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src 'none'; font-src 'none'; script-src 'none'; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'><meta name="referrer" content="no-referrer">"""


def phase_label(phase_dir: Path) -> str:
    name = re.sub(r"^phase-[^_-]+[_-]?", "", phase_dir.name)
    return name.replace("_", " ") or phase_dir.name


def source_updated(path: Path) -> str:
    """frontmatterの更新日を返す（FS mtimeは使わない）。"""

    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return "正本に記載なし"
    match = re.match(r"\A---\s*\n(.*?)\n---(?:\s*\n|\Z)", text, re.DOTALL)
    if match:
        for field in ("updated", "date"):
            value = re.search(rf"(?m)^{field}:\s*[\"']?([^\"'\n]+?)[\"']?\s*$", match.group(1))
            if value and value.group(1).strip():
                return value.group(1).strip()
    return "正本に記載なし"


def discover_funcs(phase_dir: Path) -> list[Path]:
    return sorted((path for path in phase_dir.glob("func-*") if path.is_dir() and not path.is_symlink()), key=os.fspath)


def _docs_for_func(func_dir: Path) -> list[SourceDocument]:
    specs = (
        ("summary", "00_サマリ.md", "サマリ"),
        ("requirements", "01_要件定義書.md", "要件定義書"),
        ("basic_design", "02_基本設計書.md", "基本設計書"),
        ("detailed_design", "03_詳細設計書.md", "詳細設計書"),
        ("tests", "tests/04_テスト項目書.md", "テスト項目書"),
    )
    return [SourceDocument(func_dir / filename, func_dir.name, kind, label) for kind, filename, label in specs if (func_dir / filename).is_file()]


def collect_documents(phase_dir: Path) -> list[SourceDocument]:
    docs: list[SourceDocument] = []
    for func in discover_funcs(phase_dir):
        docs.extend(_docs_for_func(func))
    system = phase_dir / "tests" / "system-test-cases.md"
    if system.is_file():
        docs.append(SourceDocument(system, "phase共通", "system_tests", "システムテストケース"))
    return docs


def _kind_for_output(output: str) -> tuple[str, ...]:
    return {
        "00_サマリ.html": ("summary",),
        "01_要件定義書.html": ("requirements",),
        "02_設計書.html": ("basic_design", "detailed_design"),
        "03_テストケース.html": ("tests", "system_tests"),
    }[output]


def _source_href(source: Path, phase_dir: Path) -> str:
    output_root = (phase_dir / "views").resolve()
    relative = Path(os.path.relpath(source.resolve(), output_root)).as_posix()
    return quote(relative, safe="/-_.~%")


def _bundle_nav(current: str, available_outputs: set[str], screen_exists: bool) -> str:
    links = []
    for output in OUTPUT_FILES:
        if output not in available_outputs:
            continue
        if output == current:
            links.append(f"<strong aria-current=\"page\">{html.escape(output[:-5])}</strong>")
        else:
            links.append(f'<a href="{quote(output, safe="/-_.~%")}">{html.escape(output[:-5])}</a>')
    if screen_exists:
        links.append(f'<a href="{quote(SCREEN_MOCK, safe="/-_.~%")}">画面モック</a>')
    return '<nav class="bundle-nav" aria-label="フェーズ文書">' + "".join(links) + "</nav>"


def _render_source(document: SourceDocument, phase_dir: Path) -> tuple[str, list[tuple[int, str, str]]]:
    return markdown_to_html(
        document.path.read_text(encoding="utf-8"),
        document.path,
        phase_dir,
        anchor_prefix=f"{document.func_name}-{document.kind}",
        heading_offset=3,
    )


def _toc_html(headings: list[tuple[int, str, str]]) -> str:
    if not headings:
        return '<p class="muted">本文に見出しはありません。</p>'
    return '<ol class="toc-list">' + "".join(f'<li class="toc-level-{level}"><a href="#{html.escape(anchor, quote=True)}">{html.escape(title)}</a></li>' for level, title, anchor in headings) + "</ol>"


def _coverage_navigation(headings: list[tuple[int, str, str]]) -> str:
    checks = (
        ("業務フロー・シーケンス", (r"シーケンス", r"処理フロー|業務フロー", r"状態遷移")),
        ("ER・データモデル", (r"ER図", r"データモデル|DB論理")),
        ("DDL / NoSQL物理スキーマ", (r"DDL|DB物理|NoSQL", r"物理設計", r"データファイル仕様")),
        ("インデックス", (r"DB物理.*インデックス", r"インデックス")),
        ("セキュリティルール", (r"セキュリティルール|Firestore Rules", r"認証・アクセス制御|アクセス制御")),
    )
    items: list[str] = []
    for label, patterns in checks:
        match = next(
            (
                match
                for pattern in patterns
                if (match := next(((title, anchor) for _, title, anchor in headings if re.search(pattern, title, re.IGNORECASE)), None))
            ),
            None,
        )
        if match:
            items.append(f'<li><a href="#{html.escape(match[1], quote=True)}">{html.escape(label)}</a></li>')
        else:
            items.append(f'<li>{html.escape(label)}: <span class="status status-pending">[要確認: 未記載]</span></li>')
    return '<aside class="coverage-nav" aria-label="設計の確認導線"><strong>設計レビューの確認導線</strong><ul>' + "".join(items) + "</ul></aside>"


def bundle_html(
    phase_dir: Path,
    output: str,
    documents: list[SourceDocument],
    available_outputs: set[str],
) -> str:
    selected = [document for document in documents if document.kind in _kind_for_output(output)]
    grouped: dict[str, list[SourceDocument]] = {}
    for document in selected:
        if document.kind == "system_tests":
            continue
        grouped.setdefault(document.func_name, []).append(document)
    all_headings: list[tuple[int, str, str]] = []
    sections: list[str] = []
    for func_name, func_documents in grouped.items():
        func_anchor = slugify(func_name, {item[2] for item in all_headings})
        all_headings.append((2, func_name, func_anchor))
        chunks: list[str] = []
        for document in func_documents:
            body, headings = _render_source(document, phase_dir)
            anchor = slugify(f"{func_name} {document.label}", {item[2] for item in all_headings})
            all_headings.append((3, f"{document.label}（{func_name}）", anchor))
            all_headings.extend(headings)
            chunks.append(
                f'<section class="source-card" id="{html.escape(anchor, quote=True)}"><h3>{html.escape(document.label)} '
                f'— {html.escape(func_name)}</h3><p class="meta"><span>正本: '
                f'<a href="{_source_href(document.path, phase_dir)}">{html.escape(document.path.relative_to(phase_dir).as_posix())}</a></span>'
                f'<span>更新日: {html.escape(source_updated(document.path))}</span></p><div class="prose">{body}</div></section>'
            )
        sections.append(f'<section class="func-section"><h2 id="{html.escape(func_anchor, quote=True)}">{html.escape(func_name)}</h2>{"".join(chunks)}</section>')
    # 03_テストケースのシステムテストはfunc横断の最後に独立して置く。
    system = [document for document in selected if document.kind == "system_tests"]
    for document in system:
        body, headings = _render_source(document, phase_dir)
        anchor = slugify("phase共通 システムテスト", {item[2] for item in all_headings})
        all_headings.append((2, "phase共通 システムテスト", anchor))
        all_headings.extend(headings)
        sections.append(f'<section class="source-card" id="{html.escape(anchor, quote=True)}"><h2>phase共通 — システムテストケース</h2><p class="meta"><a href="{_source_href(document.path, phase_dir)}">正本: {html.escape(document.path.relative_to(phase_dir).as_posix())}</a></p><div class="prose">{body}</div></section>')
    screen_exists = (phase_dir / "views" / SCREEN_MOCK).is_file()
    coverage = _coverage_navigation(all_headings) if output == "02_設計書.html" else ""
    title = output[:-5]
    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">{SECURITY_META}<title>{html.escape(phase_label(phase_dir))} — {html.escape(title)}</title><style>{CSS}</style></head><body><a class="skip-link" href="#main">本文へ移動</a><header class="page-header"><h1>{html.escape(phase_label(phase_dir))} — {html.escape(title)}</h1><p class="derived"><strong>閲覧用の派生成果物です。</strong> 正本Markdown/YAMLを変更して再生成してください。</p>{_bundle_nav(output, available_outputs, screen_exists)}</header><div class="layout"><nav class="toc" aria-label="この文書の目次"><h2>目次</h2>{_toc_html(all_headings)}</nav><main id="main" class="content" tabindex="-1">{coverage}{''.join(sections) if sections else '<p class="muted">該当する正本はありません。</p>'}</main></div><footer class="page-footer"><p>各カードに機能名と正本へのリンクを表示しています。状態マーカーは正本の記載です。</p></footer></body></html>'''


def expected_outputs(phase_dir: Path) -> dict[Path, str]:
    documents = collect_documents(phase_dir)
    available = {
        output for output in OUTPUT_FILES
        if any(document.kind in _kind_for_output(output) for document in documents)
    }
    return {
        Path(output): bundle_html(phase_dir, output, documents, available)
        for output in OUTPUT_FILES if output in available
    }


def _iter_safe_entries(root: Path):
    if not root.exists() or root.is_symlink():
        return
    for entry in root.rglob("*"):
        yield entry


def _legacy_stale(view_dir: Path, wanted: set[Path]) -> list[Path]:
    stale: list[Path] = []
    if not view_dir.exists() or view_dir.is_symlink():
        return stale
    for entry in _iter_safe_entries(view_dir):
        if entry.is_symlink():
            continue
        relative = entry.relative_to(view_dir)
        if entry.is_file() and entry.name in LEGACY_OUTPUT_NAMES and relative not in wanted and entry.name != SCREEN_MOCK:
            stale.append(entry)
    return sorted(stale, key=os.fspath)


def _empty_legacy_dirs(view_dir: Path, stale: list[Path]) -> list[Path]:
    """既知の旧namespaceが空になった場合だけ削除対象とする。"""

    if not view_dir.exists() or view_dir.is_symlink():
        return []
    dirs = [entry for entry in view_dir.iterdir() if entry.is_dir() and not entry.is_symlink() and (entry.name in LEGACY_DIR_NAMES or entry.name.startswith("func-"))]
    stale_set = set(stale)
    result: list[Path] = []
    for directory in sorted(dirs, key=os.fspath, reverse=True):
        children = [child for child in directory.iterdir() if child not in stale_set]
        if not children:
            result.append(directory)
    return result


def _symlink_violation(view_dir: Path) -> list[Path]:
    if view_dir.is_symlink():
        return [view_dir]
    violations: list[Path] = []
    if view_dir.exists():
        for entry in _iter_safe_entries(view_dir):
            if entry.is_symlink() and (entry.name in LEGACY_OUTPUT_NAMES or entry.name in OUTPUT_FILES or entry.name == SCREEN_MOCK or entry.is_dir()):
                violations.append(entry)
    return sorted(violations, key=os.fspath)


def render_phase(phase_dir: Path, check: bool = False) -> bool:
    phase_dir = phase_dir.resolve()
    view_dir = phase_dir / "views"
    violations = _symlink_violation(view_dir)
    if violations:
        for violation in violations:
            print(f"安全のため処理を中止: 出力先がシンボリックリンクです: {violation}")
        return False
    outputs = expected_outputs(phase_dir)
    wanted = set(outputs)
    stale = _legacy_stale(view_dir, wanted)
    empty_dirs = _empty_legacy_dirs(view_dir, stale)
    mismatches = [relative for relative, content in outputs.items() if not (view_dir / relative).is_file() or (view_dir / relative).read_text(encoding="utf-8") != content]
    if check:
        for relative in mismatches:
            print(f"不一致: {view_dir / relative}")
        for path in stale:
            print(f"不要: {path}")
        for path in empty_dirs:
            print(f"不要な空ディレクトリ: {path}")
        return not (mismatches or stale or empty_dirs)
    view_dir.mkdir(parents=True, exist_ok=True)
    for path in stale:
        path.unlink()
        print(f"削除: {path}")
    for directory in empty_dirs:
        if directory.exists() and not any(directory.iterdir()):
            directory.rmdir()
            print(f"削除: {directory}")
    for relative, content in outputs.items():
        target = view_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        print(f"生成: {target}")
    return True


def discover_phase_dirs(paths: list[Path]) -> list[Path]:
    roots = paths or [Path.cwd()]
    found: set[Path] = set()
    for root in roots:
        root = root.resolve()
        if root.is_dir() and (root.name.startswith("phase-") or any(path.is_dir() for path in root.glob("func-*"))):
            found.add(root)
            continue
        spec_root = root / "docs" / "spec"
        search_root = spec_root if spec_root.is_dir() else root
        found.update(path.resolve() for path in search_root.glob("phase-*") if path.is_dir())
    return sorted(found, key=os.fspath)


def main() -> None:
    parser = argparse.ArgumentParser(description="正本Markdownからフェーズ単位の自己完結HTMLビューを生成")
    parser.add_argument("paths", type=Path, nargs="*", help="フェーズディレクトリ、または標準docs/specを含むルート")
    parser.add_argument("--check", action="store_true", help="生成物との差分を読み取り専用で検証")
    args = parser.parse_args()
    phase_dirs = discover_phase_dirs(args.paths)
    if not phase_dirs:
        parser.error("フェーズディレクトリが見つかりません")
    if not all(render_phase(path, check=args.check) for path in phase_dirs):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
