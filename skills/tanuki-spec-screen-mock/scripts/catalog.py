#!/usr/bin/env python3
"""部品カタログ（component-catalog.yaml）を読み、レイアウトと部品の規則を返す。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

SKILL_DIR = Path(__file__).resolve().parent.parent
CATALOG_PATH = SKILL_DIR / "references" / "component-catalog.yaml"


class CatalogError(ValueError):
    """カタログの内容が規約を満たさない。"""


# screens.yamlのstatesが持つ5状態の語彙。state_componentsの値もこの範囲に限る。
STATE_VOCABULARY = frozenset({"normal", "empty", "loading", "error", "forbidden"})


@dataclass(frozen=True)
class LayoutRule:
    required: frozenset[str]
    forbidden: frozenset[str]


@dataclass(frozen=True)
class Catalog:
    blocks: frozenset[str]
    layouts: dict[str, LayoutRule]
    state_required: frozenset[str]
    state_components: dict[str, frozenset[str]]


def _string_list(value: Any, path: str) -> list[str]:
    if not isinstance(value, list):
        raise CatalogError(f"{path}は配列で指定してください")
    for item in value:
        if not isinstance(item, str):
            raise CatalogError(f"{path}の要素は文字列で指定してください: {item!r}")
    return value


def load_catalog(path: Path | None = None) -> Catalog:
    target = path or CATALOG_PATH
    data = yaml.safe_load(target.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise CatalogError("カタログはマッピングで記述してください")

    blocks = frozenset(_string_list(data.get("blocks"), "blocks"))
    if not blocks:
        raise CatalogError("blocksを1件以上定義してください")

    raw_layouts = data.get("layouts")
    if not isinstance(raw_layouts, dict) or not raw_layouts:
        raise CatalogError("layoutsを1件以上のマッピングで定義してください")

    layouts: dict[str, LayoutRule] = {}
    for name, rule in raw_layouts.items():
        if not isinstance(rule, dict):
            raise CatalogError(f"layouts.{name}はマッピングで指定してください")
        required = frozenset(_string_list(rule.get("required", []), f"layouts.{name}.required"))
        forbidden = frozenset(_string_list(rule.get("forbidden", []), f"layouts.{name}.forbidden"))
        unknown = sorted((required | forbidden) - blocks)
        if unknown:
            raise CatalogError(f"layouts.{name}がblocksにない部品を参照しています: {', '.join(unknown)}")
        overlap = sorted(required & forbidden)
        if overlap:
            raise CatalogError(f"layouts.{name}で同じ部品を必須と禁止の両方に指定しています: {', '.join(overlap)}")
        layouts[name] = LayoutRule(required=required, forbidden=forbidden)

    state_required_list = _string_list(data.get("state_required"), "state_required")
    if not state_required_list:
        raise CatalogError("state_requiredを1件以上定義してください")
    unknown_state_blocks = sorted(set(state_required_list) - blocks)
    if unknown_state_blocks:
        raise CatalogError(f"state_requiredがblocksにない部品を参照しています: {', '.join(unknown_state_blocks)}")
    if len(state_required_list) != len(set(state_required_list)):
        raise CatalogError("state_requiredに重複した部品があります")
    state_required = frozenset(state_required_list)

    raw_state_components = data.get("state_components")
    if not isinstance(raw_state_components, dict) or not raw_state_components:
        raise CatalogError("state_componentsを1件以上のマッピングで定義してください")
    component_keys = set(raw_state_components.keys())
    if component_keys != set(state_required_list):
        raise CatalogError(
            "state_componentsのキーはstate_requiredと同じ集合にしてください: "
            f"state_components={sorted(component_keys)}, state_required={sorted(state_required_list)}"
        )

    state_components: dict[str, frozenset[str]] = {}
    for name, values in raw_state_components.items():
        states = _string_list(values, f"state_components.{name}")
        unknown_states = sorted(set(states) - STATE_VOCABULARY)
        if unknown_states:
            raise CatalogError(
                f"state_components.{name}に5状態の語彙にない値があります: {', '.join(unknown_states)}"
            )
        state_components[name] = frozenset(states)

    return Catalog(
        blocks=blocks,
        layouts=layouts,
        state_required=state_required,
        state_components=state_components,
    )
