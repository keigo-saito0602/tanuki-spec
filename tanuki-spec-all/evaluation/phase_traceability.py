#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""phase内の全funcのtraceability.yamlを横断してUS/requirement索引をマージする共有ヘルパー。

system_traceability_gate.py と task_plan_gate.py の両方が「phase配下の全funcを読み、
IDが重複していないか確認し、1つの索引にする」処理を必要とするため、ここへ集約する。
個別実装すると参照解決の仕様がずれるリスクが高い
（tanuki-spec func/phase再構成設計 2026-08-12 §4）。
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import yaml

# func_traceabilityの各要素は「phase直下のfunc-<名前>/traceability.yaml」という
# 正規形だけを許す。絶対パスや`../`によるphase外参照を防ぐ（相対パスの文字列だけでは
# 判定できないため、後段でresolve()した結果がphase直下かも別途確認する）。
FUNC_TRACEABILITY_PATTERN = re.compile(r"^func-[^/\\]+/traceability\.yaml$")


def load_func_traceability(
    system_path: Path, func_traceability: object
) -> tuple[list[tuple[str, dict]], list[str]]:
    """func_traceabilityが指す各traceability.yamlを読み込み、traceability_gate.validate()で
    構造検証する。ここで弾かないと、statusが不正・user_story_ids未解決などの壊れたfuncが
    そのままphase側の索引（system_traceability_gate・task_plan_gate・レンダラ）へ混入する。

    Returns: [(funcの相対パス, 読み込んだdict), ...] と failures（不正なfuncはresultsに含めない）。
    """
    import traceability_gate

    results: list[tuple[str, dict]] = []
    failures: list[str] = []
    if not isinstance(func_traceability, list) or not func_traceability:
        return results, ["func_traceability は1件以上の配列で指定してください"]
    phase_dir = system_path.parent.resolve()
    for relative in func_traceability:
        if not isinstance(relative, str) or not relative.strip():
            failures.append("func_traceability の各要素は空でない文字列で指定してください")
            continue
        if Path(relative).is_absolute() or not FUNC_TRACEABILITY_PATTERN.fullmatch(relative):
            failures.append(
                f"func_traceability {relative} は func-<名前>/traceability.yaml 形式の相対パスで指定してください"
            )
            continue
        path = system_path.parent / relative
        resolved = path.resolve()
        if resolved.parent.parent != phase_dir:
            failures.append(
                f"func_traceability {relative} はphase直下のfunc-*/を指してください（phase外への参照は禁止）"
            )
            continue
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as error:
            failures.append(f"func_traceability {relative} を読み込めません: {error}")
            continue
        if not isinstance(data, dict):
            failures.append(f"func_traceability {relative} はYAMLオブジェクトで指定してください")
            continue
        func_failures = traceability_gate.validate(data)
        if func_failures:
            failures.extend(f"{relative}: {message}" for message in func_failures)
            continue
        results.append((relative, data))
    return results, failures


def merged_index(entries: list[tuple[str, dict]], key: str) -> tuple[dict[str, dict], list[str]]:
    """各funcのtraceability.yamlの`key`セクション（user_stories/requirements）を
    1つの索引へマージする。IDがfuncをまたいで重複していれば failures に記録する。
    """
    merged: dict[str, dict] = {}
    owner: dict[str, str] = {}
    failures: list[str] = []
    for relative, data in entries:
        items = data.get(key)
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            identifier = item.get("id")
            if not isinstance(identifier, str) or not identifier:
                continue
            if identifier in merged:
                failures.append(
                    f"{key} のIDがfuncをまたいで重複しています: {identifier}"
                    f"（{owner[identifier]} と {relative}）"
                )
                continue
            merged[identifier] = item
            owner[identifier] = relative
    return merged, failures


def build_phase_index(system_path: Path, system_data: dict) -> tuple[dict[str, dict], dict[str, dict], list[str]]:
    """system-traceability.yamlのfunc_traceabilityからUS/requirement索引をマージして返す。

    Returns: (user_stories_index, requirements_index, failures)
    """
    entries, failures = load_func_traceability(system_path, system_data.get("func_traceability"))
    if failures:
        return {}, {}, failures

    user_stories, us_failures = merged_index(entries, "user_stories")
    requirements, req_failures = merged_index(entries, "requirements")
    return user_stories, requirements, us_failures + req_failures


def relative_func_traceability(system_path: Path, func_traceability_path: Path) -> str:
    """funcのtraceability.yamlの、system-traceability.yamlから見た相対パスを返す
    （func_traceability配列の要素と文字列比較するために使う。OS依存のパス区切りを
    posix形式（/区切り）へ正規化する）。
    """
    relative = os.path.relpath(func_traceability_path, system_path.parent)
    return relative.replace(os.sep, "/")
