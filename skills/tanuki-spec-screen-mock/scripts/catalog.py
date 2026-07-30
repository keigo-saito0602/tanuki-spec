#!/usr/bin/env python3
"""部品カタログ（component-catalog.yaml）を読み、レイアウトと部品の規則を返す。"""

from __future__ import annotations

import sys
import types
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

# importlib.util での読み込みに対応: モジュールを sys.modules に登録
if __name__ not in sys.modules:
    _module = types.ModuleType(__name__ or 'catalog')
    _module.__file__ = __file__
    _module.__loader__ = globals().get('__loader__')
    _module.__package__ = globals().get('__package__')
    _module.__spec__ = globals().get('__spec__')
    sys.modules[__name__ or 'catalog'] = _module

SKILL_DIR = Path(__file__).resolve().parent.parent
CATALOG_PATH = SKILL_DIR / "references" / "component-catalog.yaml"


class CatalogError(ValueError):
    """カタログの内容が規約を満たさない。"""


@dataclass(frozen=True)
class LayoutRule:
    required: frozenset[str]
    forbidden: frozenset[str]


@dataclass(frozen=True)
class Catalog:
    blocks: frozenset[str]
    layouts: dict[str, LayoutRule]


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

    return Catalog(blocks=blocks, layouts=layouts)
