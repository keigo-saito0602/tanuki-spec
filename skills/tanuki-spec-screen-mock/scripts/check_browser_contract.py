#!/usr/bin/env python3
"""生成した画面モックHTMLを実ブラウザで開き、静的解析では測れない項目を実測する。

320pxでの横スクロール、タップ対象の実寸（44px）、フォーカス表現を、
実際のレイアウトエンジンで検証する。色の実測はデザインモードで行う
（ワイヤーモードは配色を無効化した構造確認専用のため、色のコントラストを
測る対象にならない）。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tokens import contrast_ratio  # noqa: E402

VIEWPORT_WIDTH = 320
MIN_TAP_TARGET = 44
MIN_OUTLINE_WIDTH = 2
FOCUS_MIN_CONTRAST = 3.0
INTERACTIVE_PARTS = ("a[href]", ".btn", "button", "input[type=submit]", "input[type=button]")
RGB_PATTERN = re.compile(r"rgba?\((\d+),\s*(\d+),\s*(\d+)")


def _scoped_selector(screen_id: str) -> str:
    """`,`区切りのCSSセレクタは枝ごとに独立するため、各枝に画面idのスコープを個別に付ける。"""
    return ", ".join(f'[id="{screen_id}"] {part}' for part in INTERACTIVE_PARTS)


def _rgb_to_hex(rgb: str) -> str:
    match = RGB_PATTERN.match(rgb)
    if not match:
        return "#000000"
    r, g, b = (int(value) for value in match.groups())
    return f"#{r:02x}{g:02x}{b:02x}"


def check(path: Path) -> list[str]:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            return check_with_browser(path, browser)
        finally:
            browser.close()


def check_with_browser(path: Path, browser) -> list[str]:
    errors: list[str] = []
    page = browser.new_page()
    try:
        page.goto(path.resolve().as_uri())
        design_toggle = page.query_selector("#fid-design")
        if design_toggle is not None:
            page.evaluate('document.getElementById("fid-design").checked = true')
        page.set_viewport_size({"width": VIEWPORT_WIDTH, "height": 900})

        screen_ids = page.eval_on_selector_all("section.screen[id]", "els => els.map(el => el.id)")
        if not screen_ids:
            errors.append("section.screenが1件も見つかりません。ブラウザ検査を実行できません")
            return errors

        errors.extend(_check_header_controls(page))

        # 非表示の画面（display:none）はaxe-coreの走査から漏れるため、
        # 画面を切り替えるたびにaxeも実行する。同一違反の重複報告は最初の画面へ集約する。
        seen_axe: set[str] = set()
        for screen_id in screen_ids:
            page.evaluate("(id) => { location.hash = id; }", screen_id)
            for axe_error in _check_axe(page):
                if axe_error not in seen_axe:
                    seen_axe.add(axe_error)
                    errors.append(f"{screen_id}: {axe_error}")
            errors.extend(_check_horizontal_scroll(page, screen_id))
            errors.extend(_check_tap_targets(page, screen_id))
            errors.extend(_check_focus_indicators(page, screen_id))
    finally:
        page.close()
    return errors


def _check_axe(page) -> list[str]:
    """axe-coreによる一般的なアクセシビリティ監査（色以外の手掛かりの妥当性はT-22Cで別に見る）。"""
    from axe_playwright_python.sync_playwright import Axe

    results = Axe().run(page)
    errors: list[str] = []
    for violation in results.response.get("violations", []):
        targets = ", ".join(", ".join(node.get("target", [])) for node in violation.get("nodes", []))
        errors.append(
            f'axe-core[{violation.get("impact", "unknown")}] {violation.get("id")}: '
            f'{violation.get("description")}（対象: {targets}）'
        )
    return errors


def _check_horizontal_scroll(page, screen_id: str) -> list[str]:
    overflow = page.evaluate(f"document.documentElement.scrollWidth - {VIEWPORT_WIDTH}")
    if overflow > 1:
        return [f"{screen_id}: 幅{VIEWPORT_WIDTH}pxで{overflow}pxの横スクロールが発生しています"]
    return []


def _check_tap_targets(page, screen_id: str) -> list[str]:
    errors: list[str] = []
    targets = page.eval_on_selector_all(
        _scoped_selector(screen_id),
        """els => els.map(el => {
            const r = el.getBoundingClientRect();
            return {text: (el.textContent || '').trim().slice(0, 20), width: r.width, height: r.height};
        })""",
    )
    for target in targets:
        if target["width"] < MIN_TAP_TARGET or target["height"] < MIN_TAP_TARGET:
            errors.append(
                f'{screen_id}: タップ対象「{target["text"]}」が'
                f'{target["width"]:.0f}x{target["height"]:.0f}pxで{MIN_TAP_TARGET}px未満です'
            )
    return errors


_MEASURE_OUTLINE_JS = """(el) => {
    const s = getComputedStyle(el);
    let node = el.parentElement;
    let background = 'rgb(255, 255, 255)';
    while (node) {
        const bg = getComputedStyle(node).backgroundColor;
        if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent') { background = bg; break; }
        node = node.parentElement;
    }
    return {
        outlineStyle: s.outlineStyle,
        outlineWidth: parseFloat(s.outlineWidth) || 0,
        outlineColor: s.outlineColor,
        background: background,
    };
}"""


def _report_focus_style(errors: list[str], context: str, text: str, style: dict) -> None:
    if style["outlineStyle"] == "none" or style["outlineWidth"] <= 0:
        errors.append(f"{context}: 「{text}」にフォーカス時のアウトラインがありません")
        return
    if style["outlineWidth"] < MIN_OUTLINE_WIDTH:
        errors.append(
            f'{context}: 「{text}」のフォーカスアウトラインが{style["outlineWidth"]}pxで細すぎます'
            f'（{MIN_OUTLINE_WIDTH}px以上にしてください）'
        )
    ratio = contrast_ratio(_rgb_to_hex(style["outlineColor"]), _rgb_to_hex(style["background"]))
    if ratio < FOCUS_MIN_CONTRAST:
        errors.append(
            f'{context}: 「{text}」のフォーカスアウトラインと背景のコントラストが'
            f"{ratio:.2f}:1で{FOCUS_MIN_CONTRAST}:1を下回ります"
        )


def _check_focus_indicators(page, screen_id: str) -> list[str]:
    errors: list[str] = []
    handles = page.query_selector_all(_scoped_selector(screen_id))
    for handle in handles:
        text = (handle.text_content() or "").strip()[:20]
        handle.focus()
        style = page.evaluate(_MEASURE_OUTLINE_JS, handle)
        _report_focus_style(errors, screen_id, text, style)
    return errors


def _check_header_controls(page) -> list[str]:
    """モード切替のラジオはopacity:0で隠しているため、対応するlabel側でフォーカス表現を測る。

    画面sectionの外にあり、どの画面が表示中でも変わらないため、画面ループの外で一度だけ検査する。
    """
    errors: list[str] = []
    input_ids = page.eval_on_selector_all(".controls .mode-input", "els => els.map(el => el.id)")
    for input_id in input_ids:
        label = page.query_selector(f'label[for="{input_id}"]')
        if label is None:
            continue
        rect = label.bounding_box() or {"width": 0, "height": 0}
        text = (label.text_content() or "").strip()[:20]
        if rect["width"] < MIN_TAP_TARGET or rect["height"] < MIN_TAP_TARGET:
            errors.append(
                f'ヘッダー操作: タップ対象「{text}」が{rect["width"]:.0f}x{rect["height"]:.0f}pxで{MIN_TAP_TARGET}px未満です'
            )
        page.eval_on_selector(f"#{input_id}", "el => el.focus()")
        style = page.evaluate(_MEASURE_OUTLINE_JS, label)
        _report_focus_style(errors, "ヘッダー操作", text, style)
    return errors


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="画面モックHTMLを実ブラウザで検証する")
    parser.add_argument("html", type=Path, help="検証するHTML")
    args = parser.parse_args(argv)

    errors = check(args.html)
    for error in errors:
        print(f"エラー: {error}")
    if errors:
        print(f"\n{len(errors)}件のエラーがあります。")
        return 1
    print("実ブラウザでの契約検査を満たしています。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
