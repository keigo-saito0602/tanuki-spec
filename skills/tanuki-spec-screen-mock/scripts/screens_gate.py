#!/usr/bin/env python3
"""screens.yamlが画面定義の規約を満たすかを決定論的に検証する。"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from catalog import Catalog

SCREEN_ID_PATTERN = re.compile(r"^SC-[EL]?\d+$")
REQUIRED_SCREEN_FIELDS = (
    "id",
    "name",
    "purpose",
    "actor",
    "layout",
    "trace",
    "design_question",
    "hypothesis",
    "risk",
    "validation_task",
    "rationale",
    "exploration_mode",
    "alternatives",
    "blocks",
    "states",
    "state_strategy",
)
REQUIRED_META_FIELDS = ("phase", "source_spec", "generated_at")
GENERATED_AT_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
STATE_KEYS = ("normal", "empty", "loading", "error", "forbidden")
RISK_LEVELS = ("low", "medium", "high")
EXPLORATION_MODES = ("compare", "inherit")
ALTERNATIVE_DECISIONS = ("adopted", "rejected")
PLACEHOLDER_PATTERN = re.compile(
    r"(?:^\s*(?:未定|未確定|未設定|未記入|未入力|TBD|TBA|TODO|PLACEHOLDER|N/?A)\s*[。.]?\s*$|<\s*[^>\n]+\s*>)",
    re.IGNORECASE,
)
PLACEHOLDER_ERROR = "空欄・未定・TBD・TODO・<placeholder>などの仮値は指定できません"


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


def _is_placeholder_text(value: Any) -> bool:
    """未確定のまま残った埋め草を検出する。"""

    return isinstance(value, str) and bool(PLACEHOLDER_PATTERN.search(value))


def _validate_required_text(value: Any, where: str, result: Result, message: str) -> None:
    if not isinstance(value, str) or not value.strip():
        result.errors.append(message)
    elif _is_placeholder_text(value):
        result.errors.append(f"{where}に{PLACEHOLDER_ERROR}")


def validate_schema(data: Any, catalog: Catalog) -> Result:
    result = Result()
    if not isinstance(data, dict):
        result.errors.append("screens.yamlはマッピングで記述してください")
        return result

    meta = data.get("meta")
    if not isinstance(meta, dict):
        result.errors.append("metaをマッピングで定義してください")
        meta = {}
    else:
        for name in REQUIRED_META_FIELDS:
            value = meta.get(name)
            if not isinstance(value, str) or not value.strip():
                result.errors.append(f"metaに必須フィールド{name}がありません")
        generated_at = meta.get("generated_at")
        if isinstance(generated_at, str) and generated_at.strip():
            if not GENERATED_AT_PATTERN.match(generated_at):
                result.errors.append("meta.generated_atはYYYY-MM-DD形式で指定してください")
            else:
                year, month, day = (int(part) for part in generated_at.split("-"))
                try:
                    date(year, month, day)
                except ValueError:
                    result.errors.append(f"meta.generated_at「{generated_at}」は実在する日付ではありません")

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
        for name in ("name", "purpose", "actor"):
            if name in screen:
                _validate_required_text(
                    screen.get(name),
                    f"{where}.{name}",
                    result,
                    f"{where}.{name}に内容を書いてください",
                )

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

        # `trace:` と書いて値を省くとNoneになる。ここで配列以外を弾かないと、
        # 警告も出ないままレンダラがNoneをイテレートして落ちる。
        if "trace" in screen:
            trace = screen.get("trace")
            if not isinstance(trace, list):
                result.errors.append(f"{label}のtraceは要件IDの配列で指定してください")
            elif not trace:
                result.warnings.append(f"{label}のtraceが空です。対応する要件IDを書いてください")
            else:
                for trace_index, trace_id in enumerate(trace):
                    if not isinstance(trace_id, str) or not trace_id.strip():
                        result.errors.append(f"{label}のtrace[{trace_index}]に要件IDを書いてください")
                    elif _is_placeholder_text(trace_id):
                        result.errors.append(f"{label}のtrace[{trace_index}]に{PLACEHOLDER_ERROR}")

        _validate_exploration(screen, label, result)

        block_types, block_states = _validate_blocks(screen.get("blocks"), label, catalog, result)
        if rule is not None:
            for missing in sorted(rule.required - block_types):
                result.errors.append(f"{label}のlayout「{layout}」には部品{missing}が必須です")
            for banned in sorted(rule.forbidden & block_types):
                result.errors.append(f"{label}のlayout「{layout}」に部品{banned}は置けません")

        _validate_state_coverage(screen.get("states"), block_states, label, result)

    _validate_entry_screens(meta.get("entry_screens"), seen, result)
    return result


def _validate_exploration(screen: dict, label: str, result: Result) -> None:
    """画面を部品の充足だけで確定させず、探索と判断の根拠を残す。"""

    for field_name in ("design_question", "hypothesis", "validation_task", "rationale"):
        _validate_required_text(
            screen.get(field_name),
            f"{label}の{field_name}",
            result,
            f"{label}の{field_name}にレビュー可能な内容を書いてください",
        )

    risk = screen.get("risk")
    if risk not in RISK_LEVELS:
        result.errors.append(f"{label}のrisk「{risk}」は{'/'.join(RISK_LEVELS)}のいずれかにしてください")

    exploration_mode = screen.get("exploration_mode")
    if exploration_mode not in EXPLORATION_MODES:
        result.errors.append(
            f"{label}のexploration_mode「{exploration_mode}」は{'/'.join(EXPLORATION_MODES)}のいずれかにしてください"
        )

    alternatives = screen.get("alternatives")
    expected_count = (
        isinstance(alternatives, list)
        and (
            (exploration_mode == "compare" and 2 <= len(alternatives) <= 3)
            or (exploration_mode == "inherit" and len(alternatives) == 1)
        )
    )
    if not expected_count:
        if exploration_mode == "inherit":
            result.errors.append(f"{label}のinheritモードではalternativesを採用案1件だけにしてください")
        else:
            result.errors.append(f"{label}のcompareモードではalternativesを比較可能な2〜3案にしてください")
    else:
        adopted = 0
        alternative_ids: set[str] = set()
        for index, alternative in enumerate(alternatives):
            where = f"{label}のalternatives[{index}]"
            if not isinstance(alternative, dict):
                result.errors.append(f"{where}はマッピングで指定してください")
                continue
            for field_name in ("id", "name", "summary", "reason"):
                _validate_required_text(
                    alternative.get(field_name),
                    f"{where}の{field_name}",
                    result,
                    f"{where}の{field_name}に比較内容を書いてください",
                )
            alternative_id = alternative.get("id")
            if isinstance(alternative_id, str) and alternative_id.strip():
                if alternative_id in alternative_ids:
                    result.errors.append(f"{label}のalternativesでid「{alternative_id}」が重複しています")
                alternative_ids.add(alternative_id)
            decision = alternative.get("decision")
            if decision not in ALTERNATIVE_DECISIONS:
                result.errors.append(
                    f"{where}のdecision「{decision}」は{'/'.join(ALTERNATIVE_DECISIONS)}のいずれかにしてください"
                )
            elif decision == "adopted":
                adopted += 1
        if adopted != 1:
            result.errors.append(f"{label}のalternativesは採用案（decision: adopted）をちょうど1件にしてください")

    if exploration_mode == "inherit":
        inherited_from = screen.get("inherited_from")
        _validate_required_text(
            inherited_from,
            f"{label}のinherited_from",
            result,
            f"{label}のinheritモードではinherited_fromに継承元を書いてください",
        )
        if risk == "high":
            result.errors.append(f"{label}はrisk: highのためinheritではなくcompareモードで代替案を比較してください")

    strategy = screen.get("state_strategy")
    if not isinstance(strategy, dict):
        result.errors.append(f"{label}のstate_strategyをマッピングで定義してください")
        return
    priority_states = strategy.get("priority_states")
    if not isinstance(priority_states, list) or not priority_states:
        result.errors.append(f"{label}のstate_strategy.priority_statesに重点状態を1件以上書いてください")
    else:
        unknown = [state for state in priority_states if state not in STATE_KEYS]
        if unknown:
            result.errors.append(
                f"{label}のstate_strategy.priority_statesに5状態以外の値があります: {', '.join(map(str, unknown))}"
            )
        if len(priority_states) != len({repr(state) for state in priority_states}):
            result.errors.append(f"{label}のstate_strategy.priority_statesに重複があります")
    strategy_rationale = strategy.get("rationale")
    _validate_required_text(
        strategy_rationale,
        f"{label}のstate_strategy.rationale",
        result,
        f"{label}のstate_strategy.rationaleに重点状態を選んだ理由を書いてください",
    )


def _validate_blocks(blocks: Any, label: str, catalog: Catalog, result: Result) -> tuple[set[str], set[str]]:
    if not isinstance(blocks, list) or not blocks:
        result.errors.append(f"{label}のblocksを1件以上の配列で定義してください")
        return set(), set()

    types: set[str] = set()
    block_states: set[str] = set()
    for index, block in enumerate(blocks):
        if not isinstance(block, dict):
            result.errors.append(f"{label}のblocks[{index}]はマッピングで指定してください")
            continue
        block_type = block.get("type")
        if not isinstance(block_type, str) or block_type not in catalog.blocks:
            result.errors.append(f"{label}のblocks[{index}]のtype「{block_type}」はカタログにありません")
            continue
        types.add(block_type)
        _validate_block_state(block, block_type, index, label, catalog, result, block_states)
    return types, block_states


def _validate_block_state(
    block: dict,
    block_type: str,
    index: int,
    label: str,
    catalog: Catalog,
    result: Result,
    block_states: set[str],
) -> None:
    where = f"{label}のblocks[{index}]（{block_type}）"
    state = block.get("state")

    if block_type not in catalog.state_required:
        if state is not None:
            result.errors.append(f"{where}は状態表現部品ではないためstateを書けません")
        return

    if not isinstance(state, str) or not state:
        result.errors.append(f"{where}は状態表現部品なのでstateが必須です")
        return
    if state not in STATE_KEYS:
        result.errors.append(f"{where}のstate「{state}」は{'/'.join(STATE_KEYS)}のいずれかにしてください")
        return
    allowed = catalog.state_components.get(block_type, frozenset())
    if state not in allowed:
        result.errors.append(
            f"{where}のstate「{state}」はこの部品では表せません（表せる値: {'/'.join(sorted(allowed))}）"
        )
        return
    block_states.add(state)


def _validate_state_coverage(states: Any, block_states: set[str], label: str, result: Result) -> None:
    if not isinstance(states, dict):
        return
    for key in STATE_KEYS:
        if key == "normal":
            continue
        value = states.get(key)
        if not isinstance(value, str) or not value.strip():
            continue
        if value.strip().startswith(NOT_APPLICABLE):
            continue
        if key not in block_states:
            result.errors.append(f"{label}のstates.{key}は扱う想定ですが、state: {key}を持つ部品がありません")


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
            _validate_required_text(
                transition.get("action"),
                f"{where}のaction",
                result,
                f"{where}のactionに操作名を書いてください",
            )
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
            if _is_placeholder_text(value):
                result.errors.append(f"{screen_id}のstates.{key}に{PLACEHOLDER_ERROR}")
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
    _validate_required_text(label, f"{where}.label", result, f"{where}のlabelに項目名を書いてください")
    if not isinstance(label, str) or not label:
        label = where
    _validate_required_text(
        item.get("control"),
        f"{where}.control",
        result,
        f"{where}のcontrolに入力方法を書いてください",
    )
    if not isinstance(item.get("required"), bool):
        result.errors.append(f"{where}のrequiredをtrueまたはfalseで書いてください")
        return
    if not item["required"]:
        return
    constraint = item.get("constraint")
    if not isinstance(constraint, str) or not constraint.strip():
        result.warnings.append(f"[要確認] {label}の入力制限が未定義です（{where}.constraint）")
    elif _is_placeholder_text(constraint):
        result.errors.append(f"{where}.constraintに{PLACEHOLDER_ERROR}")
    error_message = item.get("error")
    if not isinstance(error_message, str) or not error_message.strip():
        result.warnings.append(f"[要確認] {label}のエラー文言が未定義です（{where}.error）")
    elif _is_placeholder_text(error_message):
        result.errors.append(f"{where}.errorに{PLACEHOLDER_ERROR}")


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
