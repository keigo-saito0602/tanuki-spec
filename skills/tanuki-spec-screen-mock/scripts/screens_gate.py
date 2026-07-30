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
            if not isinstance(transition.get("action"), str) or not transition["action"]:
                result.errors.append(f"{where}のactionに操作名を書いてください")
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


NOT_APPLICABLE = "該当なし"
FIELD_BEARING_BLOCKS = ("filter-bar", "form-section")


def validate_states(data: Any) -> Result:
    result = Result()
    for screen in _screens(data):
        screen_id = screen.get("id", "(id未設定)")
        states = screen.get("states")
        if not isinstance(states, dict):
            result.errors.append(f"{screen_id}のstatesをマッピングで定義してください")
            continue
        for key in STATE_KEYS:
            value = states.get(key)
            if not isinstance(value, str) or not value.strip():
                result.errors.append(f"{screen_id}のstates.{key}に検討結果を書いてください")
                continue
            if value.strip().startswith(NOT_APPLICABLE) and ":" not in value and "：" not in value:
                result.errors.append(f"{screen_id}のstates.{key}は「該当なし: 理由」の形で理由を書いてください")
    return result


def validate_fields(data: Any) -> Result:
    result = Result()
    for screen in _screens(data):
        screen_id = screen.get("id", "(id未設定)")
        blocks = screen.get("blocks")
        if not isinstance(blocks, list):
            continue
        for block in blocks:
            if not isinstance(block, dict) or block.get("type") not in FIELD_BEARING_BLOCKS:
                continue
            fields = block.get("fields")
            if not isinstance(fields, list) or not fields:
                result.errors.append(f"{screen_id}の{block.get('type')}にfieldsを1件以上定義してください")
                continue
            for index, item in enumerate(fields):
                _validate_field(item, f"{screen_id}の{block['type']}.fields[{index}]", result)
    return result


def _validate_field(item: Any, where: str, result: Result) -> None:
    if not isinstance(item, dict):
        result.errors.append(f"{where}はマッピングで指定してください")
        return
    label = item.get("label")
    if not isinstance(label, str) or not label:
        result.errors.append(f"{where}のlabelに項目名を書いてください")
        label = where
    if not isinstance(item.get("control"), str) or not item["control"]:
        result.errors.append(f"{where}のcontrolに入力方法を書いてください")
    if not isinstance(item.get("required"), bool):
        result.errors.append(f"{where}のrequiredをtrueまたはfalseで書いてください")
        return
    if not item["required"]:
        return
    if not isinstance(item.get("constraint"), str) or not item["constraint"]:
        result.warnings.append(f"[要確認] {label}の入力制限が未定義です（{where}.constraint）")
    if not isinstance(item.get("error"), str) or not item["error"]:
        result.warnings.append(f"[要確認] {label}のエラー文言が未定義です（{where}.error）")


def validate_all(data: Any, catalog: Catalog) -> Result:
    result = validate_schema(data, catalog)
    if not result.ok():
        return result
    result.merge(validate_transitions(data))
    result.merge(validate_states(data))
    result.merge(validate_fields(data))
    return result


def main(argv: list[str] | None = None) -> int:
    import argparse
    from pathlib import Path

    import yaml

    from catalog import load_catalog

    parser = argparse.ArgumentParser(description="screens.yamlの画面定義を検証する")
    parser.add_argument("screens", type=Path, help="検証するscreens.yaml")
    parser.add_argument("--catalog", type=Path, default=None, help="部品カタログのパス")
    args = parser.parse_args(argv)

    data = yaml.safe_load(args.screens.read_text(encoding="utf-8"))
    result = validate_all(data, load_catalog(args.catalog))

    for warning in result.warnings:
        print(f"注意: {warning}")
    for error in result.errors:
        print(f"エラー: {error}")

    if result.errors:
        print(f"\n{len(result.errors)}件のエラーがあります。screens.yamlを直して再実行してください。")
        return 1
    print(f"\n検証を通過しました。注意は{len(result.warnings)}件です。")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
