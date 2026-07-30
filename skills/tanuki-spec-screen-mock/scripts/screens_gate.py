#!/usr/bin/env python3
"""screens.yamlが画面定義の規約を満たすかを決定論的に検証する。"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from catalog import Catalog

SCREEN_ID_PATTERN = re.compile(r"^SC-[EL]?\d+$")
REQUIRED_SCREEN_FIELDS = ("id", "name", "purpose", "actor", "layout", "trace", "blocks", "states")
STATE_KEYS = ("normal", "empty", "loading", "error", "forbidden")


@dataclass
class Result:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def ok(self) -> bool:
        return not self.errors

    def merge(self, other: "Result") -> "Result":
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        return self


def _screens(data: Any) -> list[dict]:
    screens = data.get("screens") if isinstance(data, dict) else None
    return [s for s in screens if isinstance(s, dict)] if isinstance(screens, list) else []


def validate_schema(data: Any, catalog: Catalog) -> Result:
    result = Result()
    if not isinstance(data, dict):
        result.errors.append("screens.yamlはマッピングで記述してください")
        return result

    meta = data.get("meta")
    if not isinstance(meta, dict):
        result.errors.append("metaをマッピングで定義してください")
        meta = {}

    screens = data.get("screens")
    if not isinstance(screens, list) or not screens:
        result.errors.append("screensを1件以上の配列で定義してください")
        return result

    seen: set[str] = set()
    for index, screen in enumerate(screens):
        where = f"screens[{index}]"
        if not isinstance(screen, dict):
            result.errors.append(f"{where}はマッピングで指定してください")
            continue

        for name in REQUIRED_SCREEN_FIELDS:
            if name not in screen:
                result.errors.append(f"{where}に必須フィールド{name}がありません")

        screen_id = screen.get("id")
        if isinstance(screen_id, str):
            if not SCREEN_ID_PATTERN.match(screen_id):
                result.errors.append(f"{where}のid「{screen_id}」はSC-数字 / SC-E数字 / SC-L数字の形式にしてください")
            elif screen_id in seen:
                result.errors.append(f"画面ID「{screen_id}」が重複しています")
            else:
                seen.add(screen_id)

        label = screen_id if isinstance(screen_id, str) else where

        layout = screen.get("layout")
        rule = catalog.layouts.get(layout) if isinstance(layout, str) else None
        if rule is None:
            result.errors.append(f"{label}のlayout「{layout}」はカタログにありません")

        trace = screen.get("trace")
        if isinstance(trace, list) and not trace:
            result.warnings.append(f"{label}のtraceが空です。対応する要件IDを書いてください")

        block_types = _validate_blocks(screen.get("blocks"), label, catalog, result)
        if rule is not None:
            for missing in sorted(rule.required - block_types):
                result.errors.append(f"{label}のlayout「{layout}」には部品{missing}が必須です")
            for banned in sorted(rule.forbidden & block_types):
                result.errors.append(f"{label}のlayout「{layout}」に部品{banned}は置けません")

    _validate_entry_screens(meta.get("entry_screens"), seen, result)
    return result


def _validate_blocks(blocks: Any, label: str, catalog: Catalog, result: Result) -> set[str]:
    if not isinstance(blocks, list) or not blocks:
        result.errors.append(f"{label}のblocksを1件以上の配列で定義してください")
        return set()

    types: set[str] = set()
    for index, block in enumerate(blocks):
        if not isinstance(block, dict):
            result.errors.append(f"{label}のblocks[{index}]はマッピングで指定してください")
            continue
        block_type = block.get("type")
        if not isinstance(block_type, str) or block_type not in catalog.blocks:
            result.errors.append(f"{label}のblocks[{index}]のtype「{block_type}」はカタログにありません")
            continue
        types.add(block_type)
    return types


def _validate_entry_screens(entry: Any, known: set[str], result: Result) -> None:
    if not isinstance(entry, list) or not entry:
        result.errors.append("meta.entry_screensに入口となる画面IDを1件以上書いてください")
        return
    for screen_id in entry:
        if screen_id not in known:
            result.errors.append(f"meta.entry_screensの「{screen_id}」に対応する画面がありません")
