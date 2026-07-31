#!/usr/bin/env python3
"""design-tokens.jsonを検証し、CSSカスタムプロパティへ変換する。"""

from __future__ import annotations

import re
from typing import Any

SOURCES = frozenset({"code", "screenshot", "url", "principles"})
CONFIDENCES = frozenset({"confirmed", "estimated", "proposed"})
REQUIRED_COLOR_ROLES = ("primary", "surface", "text", "line", "accent")
HEX_PATTERN = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
VALUE_GROUPS = ("color", "typography", "spacing", "radius", "shadow")
MIN_CONTRAST = 4.5
# 骨格テンプレートの .bar と .btn は文字色を白で固定している。
# primaryはその背景になるため、surfaceではなく白文字とのコントラストを見る。
BUTTON_TEXT_COLOR = "#ffffff"


def _expand(hex_color: str) -> tuple[int, int, int]:
    value = hex_color.lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def relative_luminance(hex_color: str) -> float:
    """WCAG 2.1の相対輝度を返す。"""

    channels = []
    for raw in _expand(hex_color):
        srgb = raw / 255
        channels.append(srgb / 12.92 if srgb <= 0.04045 else ((srgb + 0.055) / 1.055) ** 2.4)
    red, green, blue = channels
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast_ratio(a: str, b: str) -> float:
    first, second = relative_luminance(a), relative_luminance(b)
    lighter, darker = max(first, second), min(first, second)
    return (lighter + 0.05) / (darker + 0.05)


def validate_tokens(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["design-tokens.jsonはオブジェクトで記述してください"]

    colors = data.get("color")
    if not isinstance(colors, dict):
        return ["colorをオブジェクトで定義してください"]

    for role in REQUIRED_COLOR_ROLES:
        if role not in colors:
            errors.append(f"color.{role}が未定義です。役割トークンをすべて定義してください")

    for group in VALUE_GROUPS:
        entries = data.get(group)
        if entries is None:
            continue
        if not isinstance(entries, dict):
            errors.append(f"{group}はオブジェクトで定義してください")
            continue
        for name, entry in entries.items():
            errors.extend(_validate_entry(entry, f"{group}.{name}", is_color=group == "color"))

    errors.extend(_validate_contrast(colors))
    return errors


def _validate_entry(entry: Any, where: str, is_color: bool) -> list[str]:
    errors: list[str] = []
    if not isinstance(entry, dict):
        return [f"{where}は value と confidence を持つオブジェクトで指定してください"]

    value = entry.get("value")
    if not isinstance(value, str) or not value:
        errors.append(f"{where}.valueに値を書いてください")
    elif is_color and not HEX_PATTERN.match(value):
        errors.append(f"{where}.valueの「{value}」は#RRGGBB形式で書いてください")

    source = entry.get("source")
    if source is not None and source not in SOURCES:
        errors.append(f"{where}.sourceの「{source}」は{'/'.join(sorted(SOURCES))}のいずれかにしてください")

    confidence = entry.get("confidence")
    if confidence not in CONFIDENCES:
        errors.append(f"{where}.confidenceの「{confidence}」は{'/'.join(sorted(CONFIDENCES))}のいずれかにしてください")

    return errors


def _validate_contrast(colors: dict) -> list[str]:
    pairs = (("text", "surface"), ("accent", "surface"))
    errors: list[str] = []
    for foreground, background in pairs:
        front = colors.get(foreground, {})
        back = colors.get(background, {})
        if not isinstance(front, dict) or not isinstance(back, dict):
            continue
        front_value, back_value = front.get("value"), back.get("value")
        if not (isinstance(front_value, str) and HEX_PATTERN.match(front_value)):
            continue
        if not (isinstance(back_value, str) and HEX_PATTERN.match(back_value)):
            continue
        ratio = contrast_ratio(front_value, back_value)
        if ratio < MIN_CONTRAST:
            errors.append(
                f"color.{foreground}とcolor.{background}のコントラストが{ratio:.2f}:1で、"
                f"必要な{MIN_CONTRAST}:1を下回っています"
            )
    primary = colors.get("primary", {})
    primary_value = primary.get("value") if isinstance(primary, dict) else None
    if isinstance(primary_value, str) and HEX_PATTERN.match(primary_value):
        ratio = contrast_ratio(primary_value, BUTTON_TEXT_COLOR)
        if ratio < MIN_CONTRAST:
            errors.append(
                f"color.primaryと白文字のコントラストが{ratio:.2f}:1で、必要な{MIN_CONTRAST}:1を"
                f"下回っています。ボタンとヘッダーの文字が読めません"
            )
    return errors


def _sanitize(value: str) -> str:
    """CSS宣言から抜け出せる文字を落とす。

    バックスラッシュも落とす。CSSは `\\7d` のような数値エスケープを解釈するため、
    リテラルの記号だけを除いても抜け道が残る。改行と制御文字も同様に落とす。
    """

    return re.sub(r"[<>{};\\\x00-\x1f\x7f]", "", value).strip()


def to_css_variables(data: Any) -> str:
    lines: list[str] = []
    for group in VALUE_GROUPS:
        entries = data.get(group) if isinstance(data, dict) else None
        if not isinstance(entries, dict):
            continue
        for name, entry in entries.items():
            if not isinstance(entry, dict):
                continue
            value = entry.get("value")
            if not isinstance(value, str):
                continue
            lines.append(f"  --{group}-{name}: {_sanitize(value)};")
    return "\n".join(lines)


def unconfirmed(data: Any) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for group in VALUE_GROUPS:
        entries = data.get(group) if isinstance(data, dict) else None
        if not isinstance(entries, dict):
            continue
        for name, entry in entries.items():
            if not isinstance(entry, dict):
                continue
            confidence = entry.get("confidence")
            if confidence == "confirmed":
                continue
            rows.append((f"{group}.{name}", str(entry.get("source", "未記録")), str(confidence)))
    return rows
