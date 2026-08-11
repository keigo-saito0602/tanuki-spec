#!/usr/bin/env python3
"""生成した画面モックHTMLが出力契約を満たすかを検証する。

静的に読み取れる項目だけを見る。320pxでの横スクロール、タップ対象44px、
色以外の手がかりの併用は、レイアウトエンジンが要るためここでは検証しない。
これらは骨格テンプレート側のCSSで作り込んで担保する。
"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path

from tokens import BUTTON_TEXT_COLOR, MIN_CONTRAST, contrast_ratio

FORBIDDEN_TAGS = ("script", "iframe", "object", "embed")
EXTERNAL_PATTERN = re.compile(r"""(?:src|href)\s*=\s*["'](?:https?:)?//""", re.I)
# コントラストは:rootのトークンだけを見る。ワイヤーモードの上書きブロックにも
# --color-surface があるため、HTML全体から拾うと後勝ちで本来の背景色を取り違える。
ROOT_BLOCK_PATTERN = re.compile(r":root\s*\{(.*?)\}", re.S)
VARIABLE_PATTERN = re.compile(r"--color-(text|surface|primary|accent|line):\s*(#[0-9a-fA-F]{3,6})\s*;")
VOID_ELEMENTS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
# border:0やborder:noneはsr-onlyパターンのダミー値であり、実際の境界線の手掛かりとして数えない。
BORDER_PATTERN = re.compile(r"border(?:-[a-z]+)?\s*:\s*(?!(?:0(?:px)?|none)\b)\S")


class MockParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.errors: list[str] = []
        self.html_lang = ""
        self.h1_count = 0
        self.heading_levels: list[int] = []
        self.meta_names: set[str] = set()
        self.has_csp = False
        self.section_ids: list[str] = []
        self.state_markers: list[dict] = []
        self.section_states: dict[str, set[str]] = {}
        self._open_tags: list[tuple[dict | None, bool]] = []
        self._section_stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {name: (value or "") for name, value in attrs}

        if tag in FORBIDDEN_TAGS:
            self.errors.append(f"{tag}要素は使えません。モックはHTMLとCSSだけで表現してください")

        for name in values:
            if name.startswith("on"):
                self.errors.append(f"イベント属性{name}は使えません。JavaScriptを使わずに表現してください")

        if tag == "html":
            self.html_lang = values.get("lang", "")
        if tag == "meta":
            if "name" in values:
                self.meta_names.add(values["name"])
            if values.get("http-equiv", "").lower() == "content-security-policy":
                self.has_csp = True
        if tag == "h1":
            self.h1_count += 1
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.heading_levels.append(int(tag[1]))
        if tag == "section" and "screen" in values.get("class", "").split():
            screen_id = values.get("id", "")
            self.section_ids.append(screen_id)
            self._section_stack.append(screen_id)
        elif tag == "section":
            self._section_stack.append("")

        state = values.get("data-state")
        marker: dict | None = None
        if state:
            marker = {"state": state, "has_text": False, "has_border": False, "has_icon": False}
            self.state_markers.append(marker)
            if self._section_stack:
                self.section_states.setdefault(self._section_stack[-1], set()).add(state)

        if BORDER_PATTERN.search(values.get("style", "")):
            for open_marker, _ in self._open_tags:
                if open_marker:
                    open_marker["has_border"] = True
            if marker:
                marker["has_border"] = True

        is_aria_hidden = values.get("aria-hidden") == "true"
        if tag not in VOID_ELEMENTS:
            self._open_tags.append((marker, is_aria_hidden))

    def handle_data(self, data: str) -> None:
        if not data.strip():
            return
        # aria-hidden はどの祖先要素に付いていても、内側のテキストをアイコン扱いにする。
        within_aria_hidden = any(is_aria_hidden for _, is_aria_hidden in self._open_tags)
        for marker, _ in self._open_tags:
            if marker is None:
                continue
            marker["has_text"] = True
            if within_aria_hidden:
                marker["has_icon"] = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "section" and self._section_stack:
            self._section_stack.pop()
        if self._open_tags:
            self._open_tags.pop()


def validate(path: Path, screens_path: Path | None = None) -> list[str]:
    source = path.read_text(encoding="utf-8")
    parser = MockParser()
    parser.feed(source)
    errors = list(parser.errors)

    if parser.html_lang != "ja":
        errors.append('html要素にlang="ja"を指定してください')
    if "viewport" not in parser.meta_names:
        errors.append("viewportのmetaがありません。モバイル表示が壊れます")
    if not parser.has_csp:
        errors.append("Content-Security-Policyのmetaがありません")
    if parser.h1_count != 1:
        errors.append(f"h1は1件にしてください。現在{parser.h1_count}件です")

    previous = 0
    for level in parser.heading_levels:
        if previous and level > previous + 1:
            errors.append(f"見出しレベルがh{previous}からh{level}へ飛んでいます")
            break
        previous = level

    if EXTERNAL_PATTERN.search(source):
        errors.append("外部URLを参照しています。単一ファイルで完結させてください")

    if not parser.section_ids:
        errors.append("画面のsectionが1件もありません")
    for index, screen_id in enumerate(parser.section_ids):
        if not screen_id:
            errors.append(f"{index}番目の画面sectionにidがありません。アンカー遷移が動きません")

    errors.extend(_validate_contrast(source))
    errors.extend(_validate_state_markers(parser.state_markers))
    if screens_path is not None:
        import yaml

        screens_data = yaml.safe_load(screens_path.read_text(encoding="utf-8"))
        errors.extend(_validate_screen_states(parser, screens_data))
    return errors


def _validate_state_markers(markers: list[dict]) -> list[str]:
    """data-state属性を持つ要素に、文字・境界線・アイコンのいずれかが併存するかを見る。

    色だけに頼った状態表現は、色を見分けられない場合に伝わらない。
    """
    errors: list[str] = []
    for marker in markers:
        if marker["has_text"] or marker["has_border"] or marker["has_icon"]:
            continue
        errors.append(
            f'data-state="{marker["state"]}"の要素に、文字・境界線・アイコンのいずれの手掛かりもありません'
            "（色だけに頼っています）"
        )
    return errors


def _validate_screen_states(parser: MockParser, screens_data: object) -> list[str]:
    """screens.yamlのblocks[].stateと、HTMLのsection#<画面ID>内のdata-stateを画面単位で突き合わせる。"""
    errors: list[str] = []
    screens = (screens_data.get("screens") or []) if isinstance(screens_data, dict) else []
    yaml_ids: set[str] = set()

    for screen in screens:
        if not isinstance(screen, dict):
            continue
        screen_id = str(screen.get("id", ""))
        yaml_ids.add(screen_id)
        if screen_id not in parser.section_ids:
            errors.append(f"画面ID {screen_id} はscreens.yamlにありますが、HTMLに見つかりません")
            continue

        expected = {
            block.get("state")
            for block in (screen.get("blocks") or [])
            if isinstance(block, dict) and block.get("state")
        }
        actual = parser.section_states.get(screen_id, set())
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        if missing:
            errors.append(
                f"{screen_id}: screens.yamlで期待されるstateがHTMLのdata-stateにありません: {', '.join(missing)}"
            )
        if extra:
            errors.append(
                f"{screen_id}: HTMLのdata-stateにscreens.yamlで期待されていないstateがあります: {', '.join(extra)}"
            )

    for screen_id in parser.section_ids:
        if screen_id and screen_id not in yaml_ids:
            errors.append(f"画面ID {screen_id} はHTMLにありますが、screens.yamlに定義がありません")

    return errors


def _validate_contrast(source: str) -> list[str]:
    block = ROOT_BLOCK_PATTERN.search(source)
    if not block:
        return [":rootのCSS変数ブロックが見つかりません"]
    values = dict(VARIABLE_PATTERN.findall(block.group(1)))
    surface = values.get("surface")
    if not surface:
        return ["--color-surfaceが出力されていません"]
    errors: list[str] = []
    for role in ("text", "accent"):
        color = values.get(role)
        if not color:
            continue
        ratio = contrast_ratio(color, surface)
        if ratio < MIN_CONTRAST:
            errors.append(f"--color-{role}と--color-surfaceのコントラストが{ratio:.2f}:1で{MIN_CONTRAST}:1を下回ります")
    # .bar と .btn は --color-primary を背景に、文字色を白で固定している。
    # surfaceではなく白文字との比を見ないと、淡いprimaryで文字が読めなくなる。
    primary = values.get("primary")
    if primary:
        ratio = contrast_ratio(primary, BUTTON_TEXT_COLOR)
        if ratio < MIN_CONTRAST:
            errors.append(
                f"--color-primaryとボタンの白文字のコントラストが{ratio:.2f}:1で{MIN_CONTRAST}:1を下回ります"
            )
    return errors


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="画面モックHTMLの出力契約を検証する")
    parser.add_argument("html", type=Path, help="検証するHTML")
    parser.add_argument("--screens", type=Path, default=None, help="screens.yamlのパス（画面単位のstate突き合わせに使う）")
    args = parser.parse_args(argv)

    errors = validate(args.html, args.screens)
    if args.screens is None:
        print("--screens が未指定のため、画面単位のstate突き合わせは未検証です")
    for error in errors:
        print(f"エラー: {error}")
    if errors:
        print(f"\n{len(errors)}件のエラーがあります。screens.yamlまたはdesign-tokens.jsonを直して再生成してください。")
        return 1
    print("出力契約を満たしています。")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
