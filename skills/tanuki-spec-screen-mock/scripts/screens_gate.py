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


TRANSITION_KINDS = ("forward", "back", "cancel")


def validate_transitions(data: Any) -> Result:
    result = Result()
    screens = _screens(data)
    known = {s["id"] for s in screens if isinstance(s.get("id"), str)}
    outgoing: dict[str, set[str]] = {}

    for screen in screens:
        screen_id = screen.get("id")
        if not isinstance(screen_id, str):
            continue
        transitions = screen.get("transitions") or []
        if not isinstance(transitions, list):
            result.errors.append(f"{screen_id}のtransitionsは配列で指定してください")
            transitions = []

        targets: set[str] = set()
        for index, transition in enumerate(transitions):
            where = f"{screen_id}のtransitions[{index}]"
            if not isinstance(transition, dict):
                result.errors.append(f"{where}はマッピングで指定してください")
                continue
            if not isinstance(transition.get("on"), str) or not transition["on"]:
                result.errors.append(f"{where}のonに操作名を書いてください")
            kind = transition.get("kind")
            if kind not in TRANSITION_KINDS:
                result.errors.append(f"{where}のkind「{kind}」は{'/'.join(TRANSITION_KINDS)}のいずれかにしてください")
            target = transition.get("to")
            if not isinstance(target, str) or target not in known:
                result.errors.append(f"{where}の遷移先「{target}」に対応する画面がありません")
                continue
            targets.add(target)

        outgoing[screen_id] = targets
        is_terminal = screen.get("terminal") is True
        if not targets and not is_terminal:
            result.errors.append(f"{screen_id}は遷移先がない行き止まりです。終端なら terminal: true を書いてください")
        elif targets == {screen_id} and not is_terminal:
            result.errors.append(f"{screen_id}は自分自身へ戻る遷移しかありません。他画面への導線を足してください")

    _report_unreachable(data, known, outgoing, result)
    return result


def _report_unreachable(data: Any, known: set[str], outgoing: dict[str, set[str]], result: Result) -> None:
    meta = data.get("meta") if isinstance(data, dict) else None
    entry = meta.get("entry_screens") if isinstance(meta, dict) else None
    seeds = [s for s in entry if s in known] if isinstance(entry, list) else []
    if not seeds:
        return

    reached: set[str] = set()
    queue = list(seeds)
    while queue:
        current = queue.pop()
        if current in reached:
            continue
        reached.add(current)
        queue.extend(outgoing.get(current, set()) - reached)

    for screen_id in sorted(known - reached):
        result.errors.append(f"{screen_id}はmeta.entry_screensのどこからも到達できません")
