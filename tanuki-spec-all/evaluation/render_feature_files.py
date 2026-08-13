#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""traceability.yaml の受入試験(Gherkinシナリオ)から .feature を生成する。"""
from __future__ import annotations

import argparse
from pathlib import Path

INVALID_FILENAME_CHARS = str.maketrans({c: "_" for c in '\\/:*?"<>| '})
DEFAULT_FEATURE = "受入シナリオ"


def feature_filename(feature: str) -> str:
    return feature.translate(INVALID_FILENAME_CHARS) + ".feature"


def scenario_tags(acceptance: dict) -> str:
    tags = [f"@{acceptance['id']}"]
    tags += [f"@{story_id}" for story_id in acceptance.get("user_story_ids", [])]
    tags += [f"@{requirement_id}" for requirement_id in acceptance.get("requirement_ids", [])]
    return " ".join(tags)


def render_steps(scenario: dict) -> list[str]:
    lines: list[str] = []
    for keyword, field in (("Given", "given"), ("When", "when"), ("Then", "then")):
        for index, text in enumerate(scenario.get(field, [])):
            lines.append(f"    {keyword if index == 0 else 'And'} {text}")
    return lines


def render_examples(examples: list[dict]) -> list[str]:
    headers = list(examples[0])
    lines = ["", "    Examples:", "      | " + " | ".join(headers) + " |"]
    for row in examples:
        lines.append("      | " + " | ".join(str(row[header]) for header in headers) + " |")
    return lines


def render_feature(feature: str, acceptances: list[dict]) -> str:
    lines = [f"Feature: {feature}"]
    for acceptance in acceptances:
        scenario = acceptance["scenario"]
        keyword = "Scenario Outline" if scenario.get("examples") else "Scenario"
        lines.append("")
        lines.append(f"  {scenario_tags(acceptance)}")
        lines.append(f"  {keyword}: {scenario['name']}")
        lines.extend(render_steps(scenario))
        if scenario.get("examples"):
            lines.extend(render_examples(scenario["examples"]))
    return "\n".join(lines) + "\n"


def acceptance_feature(acceptance: dict) -> str:
    """feature を決める。未指定なら user_story_ids 先頭、それも無ければ既定名。"""
    feature = acceptance.get("feature")
    if feature:
        return feature
    story_ids = acceptance.get("user_story_ids") or []
    return story_ids[0] if story_ids else DEFAULT_FEATURE


def render_all(data: dict) -> dict[str, str]:
    groups: dict[str, list[dict]] = {}
    for acceptance in data["acceptance_tests"]:
        if acceptance.get("status") != "in_scope":
            continue
        feature = acceptance_feature(acceptance)
        groups.setdefault(feature, []).append(acceptance)
    return {feature_filename(feature): render_feature(feature, items) for feature, items in groups.items()}


def main() -> None:
    import phase_traceability
    import system_traceability_gate

    parser = argparse.ArgumentParser(description="受入試験のGherkinシナリオから .feature を生成")
    parser.add_argument("traceability", type=Path, help="system-traceability.yaml のパス（phase直下）")
    parser.add_argument("--output-dir", type=Path, required=True, help="生成先ディレクトリ")
    parser.add_argument("--check", action="store_true", help="生成物との差分だけを検証する")
    args = parser.parse_args()
    data = system_traceability_gate.load(args.traceability)
    user_stories, requirements, failures = phase_traceability.build_phase_index(args.traceability, data)
    if not failures:
        failures = system_traceability_gate.validate(data, user_stories, requirements)
    if failures:
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit("システムトレーサビリティゲート不通過のため .feature を生成できません")
    outputs = render_all(data)
    if args.check:
        mismatches = [name for name, content in outputs.items() if not (args.output_dir / name).exists() or (args.output_dir / name).read_text(encoding="utf-8") != content]
        if mismatches:
            raise SystemExit(".feature が正本と不一致です: " + ", ".join(mismatches))
        print(f"検証: {args.output_dir}")
        return
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, content in outputs.items():
        (args.output_dir / name).write_text(content, encoding="utf-8")
    print(f"生成: {args.output_dir}")


if __name__ == "__main__":
    main()
