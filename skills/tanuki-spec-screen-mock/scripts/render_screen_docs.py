#!/usr/bin/env python3
"""screens.yamlから、基本設計書のbd-screenへ貼る画面一覧・遷移表を標準出力へ書く。

ファイルは作らない。同じ表が正本とビューの2箇所に残ると二重管理になるため、
貼り付け用のテキストとしてだけ提供する。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

HEADER = "| 画面ID | 画面名 | 遷移元→遷移先 | 主な操作 |"
SEPARATOR = "| --- | --- | --- | --- |"


def _cell(value: Any) -> str:
    return str(value).replace("|", r"\|")


def render_table(screens_data: Any) -> str:
    screens = screens_data.get("screens", []) if isinstance(screens_data, dict) else []
    lines = [HEADER, SEPARATOR]
    for screen in screens:
        if not isinstance(screen, dict):
            continue
        screen_id = _cell(screen.get("id", ""))
        transitions = [t for t in (screen.get("transitions") or []) if isinstance(t, dict)]
        if transitions:
            routes = "、".join(f"{screen_id}→{_cell(t.get('to', ''))}" for t in transitions)
            actions = "、".join(_cell(t.get("action", "")) for t in transitions)
        else:
            routes = "（終端）"
            actions = "—"
        lines.append(f"| {screen_id} | {_cell(screen.get('name', ''))} | {routes} | {actions} |")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    import argparse

    import yaml

    parser = argparse.ArgumentParser(description="基本設計へ貼る画面一覧・遷移表を出力する")
    parser.add_argument("screens", type=Path, help="screens.yaml")
    args = parser.parse_args(argv)

    data = yaml.safe_load(args.screens.read_text(encoding="utf-8"))
    print(render_table(data))
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
