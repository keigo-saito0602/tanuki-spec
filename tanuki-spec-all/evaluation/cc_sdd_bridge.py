#!/usr/bin/env python3
"""tanuki の仕様正本から cc-sdd の薄い参照カードを生成する。

このブリッジは要件・設計本文を cc-sdd 側へ複製しない。tanuki の ID と
相対リンクを残したまま、cc-sdd のスキルが読める数値要件 ID・設計要素・
スコープ境界だけを生成する。生成物はこのブリッジが所有するため、既存の
手書き spec や tasks.md を誤って上書きしないことを最優先にする。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import yaml


OWNER_MARKER = "tanuki-spec-cc-sdd-bridge-v1"
OUTPUT_FILES = ("spec.json", "requirements.md", "design.md")
REQUIREMENT_STATUS = {"in_scope", "draft", "deferred", "out_of_scope"}
# cc-sdd の標準メタデータは `kiro-spec-*` が更新する。ブリッジが所有する
# 拡張フィールドだけを `check` で比較し、タスク生成や承認処理による
# cc-sdd 管理フィールドの更新を正本との差分として誤検知しない。
BRIDGE_OWNED_SPEC_FIELDS = (
    "generated_by",
    "source",
    "bridge",
    "feature_name",
    "language",
)


class BridgeError(RuntimeError):
    """安全確認または入力検証に失敗した。"""


@dataclass(frozen=True)
class Requirement:
    tanuki_id: str
    status: str
    statement: str
    source: dict[str, Any]
    number: int | None


@dataclass(frozen=True)
class DesignElement:
    tanuki_id: str
    element_type: str
    name: str
    requirement_ids: tuple[str, ...]
    source: dict[str, Any]


@dataclass(frozen=True)
class Inputs:
    project_root: Path
    phase_dir: Path
    func_dir: Path
    spec_dir: Path
    phase_label: str
    func_label: str
    traceability_path: Path
    design_traceability_path: Path
    summary_path: Path
    requirements_path: Path
    basic_design_path: Path
    detailed_design_path: Path


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, dict):
        return list(value.values())
    raise BridgeError("YAMLの配列項目が配列またはマップではありません")


def _safe_relative(path: Path, base: Path, label: str) -> Path:
    """path が base 配下であることを realpath ベースで検証する。"""

    try:
        relative = path.resolve(strict=True).relative_to(base.resolve(strict=True))
    except (FileNotFoundError, ValueError) as error:
        raise BridgeError(f"{label} は対象phase/func配下にありません: {path}") from error
    return relative


def _resolve_phase(project_root: Path, phase_arg: str) -> Path:
    candidate = Path(phase_arg).expanduser()
    if not candidate.is_absolute():
        candidate = project_root / candidate
    candidate = candidate.resolve(strict=True)
    _safe_relative(candidate, project_root, "phase")
    if not candidate.is_dir():
        raise BridgeError(f"phaseディレクトリではありません: {candidate}")
    return candidate


def _resolve_func(phase_dir: Path, func_arg: str) -> Path:
    candidate = Path(func_arg).expanduser()
    if not candidate.is_absolute():
        candidate = phase_dir / candidate
        # `イベント公開管理` と `func-イベント公開管理` の両方を受け付ける。
        if not candidate.exists() and not str(func_arg).startswith("func-"):
            candidate = phase_dir / f"func-{func_arg}"
    candidate = candidate.resolve(strict=True)
    _safe_relative(candidate, phase_dir, "func")
    if not candidate.is_dir():
        raise BridgeError(f"funcディレクトリではありません: {candidate}")
    if not candidate.name.startswith("func-"):
        raise BridgeError(f"funcディレクトリ名は func-<機能名> で指定してください: {candidate.name}")
    return candidate


def _resolve_source(func_dir: Path, filename: str) -> Path:
    path = (func_dir / filename).resolve(strict=True)
    _safe_relative(path, func_dir, f"入力ファイル {filename}")
    if not path.is_file():
        raise BridgeError(f"入力ファイルがありません: {path}")
    return path


def resolve_inputs(
    project_root: str | Path,
    phase: str | Path,
    func: str | Path,
    spec: str,
) -> Inputs:
    root = Path(project_root).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise BridgeError(f"project rootがディレクトリではありません: {root}")
    phase_dir = _resolve_phase(root, str(phase))
    func_dir = _resolve_func(phase_dir, str(func))
    if not spec or Path(spec).name != spec or spec in {".", ".."}:
        raise BridgeError("specは単一のディレクトリ名で指定してください")
    if any(part in {".", ".."} for part in Path(spec).parts):
        raise BridgeError("specに親ディレクトリ指定は使えません")
    spec_dir = root / ".kiro" / "specs" / spec
    # 出力先そのものは未作成でもよいが、既存のsymlinkを解決してはいけない。
    if spec_dir.exists() and spec_dir.is_symlink():
        raise BridgeError(f"出力specディレクトリがsymlinkです: {spec_dir}")

    return Inputs(
        project_root=root,
        phase_dir=phase_dir,
        func_dir=func_dir,
        spec_dir=spec_dir,
        phase_label=phase_dir.name,
        func_label=func_dir.name.removeprefix("func-"),
        traceability_path=_resolve_source(func_dir, "traceability.yaml"),
        design_traceability_path=_resolve_source(func_dir, "design-traceability.yaml"),
        summary_path=_resolve_source(func_dir, "00_サマリ.md"),
        requirements_path=_resolve_source(func_dir, "01_要件定義書.md"),
        basic_design_path=_resolve_source(func_dir, "02_基本設計書.md"),
        detailed_design_path=_resolve_source(func_dir, "03_詳細設計書.md"),
    )


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise BridgeError(f"YAMLを読み込めません: {path}: {error}") from error
    if not isinstance(data, dict):
        raise BridgeError(f"YAMLのルートはマップである必要があります: {path}")
    return data


def _records(value: Any, label: str) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        records: list[dict[str, Any]] = []
        for key, item in value.items():
            if isinstance(item, dict):
                record = dict(item)
                record.setdefault("id", key)
                records.append(record)
            else:
                raise BridgeError(f"{label} の {key} はマップである必要があります")
        return records
    if not isinstance(value, list):
        raise BridgeError(f"{label} は配列またはマップである必要があります")
    if not all(isinstance(item, dict) for item in value):
        raise BridgeError(f"{label} の各項目はマップである必要があります")
    return [dict(item) for item in value]


def load_records(inputs: Inputs) -> tuple[list[Requirement], list[Requirement], list[DesignElement]]:
    traceability = _load_yaml(inputs.traceability_path)
    raw_requirements = _records(traceability.get("requirements"), "requirements")
    if not raw_requirements:
        raise BridgeError("requirementsが空です")
    requirements: list[Requirement] = []
    ids: set[str] = set()
    for record in raw_requirements:
        identifier = _as_text(record.get("id")).strip()
        status = _as_text(record.get("status")).strip() or "draft"
        statement = _as_text(record.get("statement")).strip()
        if not identifier:
            raise BridgeError("要件IDがありません")
        if identifier in ids:
            raise BridgeError(f"要件IDが重複しています: {identifier}")
        if status not in REQUIREMENT_STATUS:
            raise BridgeError(f"要件 {identifier} のstatusが不正です: {status}")
        if not statement:
            raise BridgeError(f"要件 {identifier} のstatementが空です")
        ids.add(identifier)
        requirements.append(Requirement(identifier, status, statement, record, None))
    active = [
        Requirement(item.tanuki_id, item.status, item.statement, item.source, index)
        for index, item in enumerate(
            (item for item in requirements if item.status in {"in_scope", "draft"}), 1
        )
    ]
    by_id = {item.tanuki_id: item for item in active}
    excluded = [item for item in requirements if item.status in {"deferred", "out_of_scope"}]

    design_data = _load_yaml(inputs.design_traceability_path)
    design_records = _records(design_data.get("design_elements"), "design_elements")
    elements: list[DesignElement] = []
    for record in design_records:
        identifier = _as_text(record.get("id")).strip()
        if not identifier:
            raise BridgeError("設計要素IDがありません")
        raw_ids = record.get("requirement_ids", [])
        if not isinstance(raw_ids, (list, tuple)):
            raise BridgeError(f"設計要素 {identifier} のrequirement_idsが配列ではありません")
        requirement_ids = tuple(_as_text(item).strip() for item in raw_ids)
        unknown = [item for item in requirement_ids if item not in ids]
        if unknown:
            raise BridgeError(
                f"設計要素 {identifier} が未知の要件IDを参照しています: {', '.join(unknown)}"
            )
        elements.append(
            DesignElement(
                identifier,
                _as_text(record.get("type")).strip() or "design",
                _as_text(record.get("name")).strip() or identifier,
                requirement_ids,
                record,
            )
        )
    return active, excluded, elements


def _relative_link(path: Path, output_dir: Path) -> str:
    return Path(os.path.relpath(path, output_dir)).as_posix()


def _key_points(path: Path, limit: int = 5) -> list[str]:
    points: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("---"):
            continue
        if stripped.startswith("-") or re.match(r"\d+[.)] ", stripped):
            point = re.sub(r"^[-*]\s+|^\d+[.)]\s+", "", stripped).strip()
            if point and point not in points:
                points.append(point[:180])
        if len(points) >= limit:
            break
    if not points:
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and not stripped.startswith("---"):
                points.append(stripped[:180])
                break
    return points


def _markdown_table(rows: Iterable[tuple[str, ...]]) -> str:
    materialized = list(rows)
    rendered = [
        "| " + " | ".join(cell.replace("\n", " ").replace("|", "\\|") for cell in row) + " |"
        for row in materialized
    ]
    if not rendered:
        return "（該当なし）"
    columns = len(materialized[0])
    header = rendered[0]
    separator = "| " + " | ".join("---" for _ in range(columns)) + " |"
    return "\n".join([header, separator, *rendered[1:]])


def render_spec_json(inputs: Inputs, active: list[Requirement], approved: bool) -> str:
    data = {
        "feature_name": inputs.spec_dir.name,
        "name": inputs.spec_dir.name,
        "created_at": None,
        "updated_at": None,
        "language": "ja",
        "phase": "design-generated",
        "generated_by": OWNER_MARKER,
        "source": {
            "phase": inputs.phase_label,
            "func": inputs.func_dir.name,
            "tanuki_root": _relative_link(inputs.func_dir, inputs.spec_dir),
        },
        "approvals": {
            "requirements": {"generated": True, "approved": approved},
            "design": {"generated": True, "approved": approved},
            "tasks": {"generated": False, "approved": False},
        },
        "bridge": {"requirement_count": len(active), "output_files": list(OUTPUT_FILES)},
        "ready_for_implementation": False,
    }
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def render_requirements_md(
    inputs: Inputs, active: list[Requirement], excluded: list[Requirement]
) -> str:
    rows = [("cc-sdd ID", "tanuki ID", "status", "要点")]
    rows.extend((f"Requirement {item.number}", item.tanuki_id, item.status, item.statement) for item in active)
    lines = [
        f"# 要件参照カード — {inputs.func_label}",
        "",
        f"> {OWNER_MARKER}。tanukiの要件本文を正本とし、このファイルはcc-sdd向けの薄い参照カードです。",
        "",
        "## 読み方",
        "",
        "要件の詳細・受入条件・根拠はtanuki側を参照してください。cc-sddのタスク生成が扱えるよう、採用要件には決定論的な数値IDを付けています。",
        "",
        "## タスク生成前の必須読込",
        "",
        "kiro-spec-tasksは次の正本を全文読んでからtasks.mdを生成してください。このカードの要点だけでタスクを生成してはいけません。",
        "",
        f"- 要件本文・受入条件・制約: [{inputs.requirements_path.name}]({_relative_link(inputs.requirements_path, inputs.spec_dir)})",
        f"- 要件status・ID・根拠: [{inputs.traceability_path.name}]({_relative_link(inputs.traceability_path, inputs.spec_dir)})",
        f"- 対象範囲・未決事項: [{inputs.summary_path.name}]({_relative_link(inputs.summary_path, inputs.spec_dir)})",
        "",
        "## 要件IDマップ",
        "",
        _markdown_table(rows),
        "",
        "## 要件",
        "",
    ]
    for item in active:
        lines.extend(
            [
                f"### Requirement {item.number}: [{item.tanuki_id}] {item.statement}",
                "",
                f"- status: `{item.status}`",
                f"- tanuki: [{inputs.requirements_path.name}]({_relative_link(inputs.requirements_path, inputs.spec_dir)})",
                "",
            ]
        )
    lines.extend(["## 対象外", ""])
    if excluded:
        lines.append("| tanuki ID | status | 理由 |")
        lines.append("| --- | --- | --- |")
        for item in excluded:
            reason = _as_text(item.source.get("reason")).strip() or (
                "tanuki側で対象外として管理されているため、cc-sddの数値要件には含めない"
            )
            lines.append(f"| {item.tanuki_id} | `{item.status}` | {reason} |")
    else:
        lines.append("対象外の要件はありません。")
    lines.extend(
        [
            "",
            "## 境界",
            "",
            f"- 対象phase: [{inputs.phase_label}]({_relative_link(inputs.phase_dir, inputs.spec_dir)})",
            f"- 対象func: [{inputs.func_dir.name}]({_relative_link(inputs.func_dir, inputs.spec_dir)})",
            "- requirements/design/tasks本文の正本はtanuki側であり、このカードは複製しない。",
            "",
        ]
    )
    return "\n".join(lines)


def render_design_md(
    inputs: Inputs,
    active: list[Requirement],
    excluded: list[Requirement],
    elements: list[DesignElement],
) -> str:
    number_by_id = {item.tanuki_id: item.number for item in active}
    status_by_id = {item.tanuki_id: item.status for item in [*active, *excluded]}
    links = [
        ("要件定義", inputs.requirements_path),
        ("基本設計", inputs.basic_design_path),
        ("詳細設計", inputs.detailed_design_path),
        ("サマリ", inputs.summary_path),
    ]
    lines = [
        f"# 設計参照カード — {inputs.func_label}",
        "",
        f"> {OWNER_MARKER}。設計本文はtanuki側を正本とし、ここでは設計要素と境界だけを橋渡しします。",
        "",
        "## タスク生成前の必須読込",
        "",
        "kiro-spec-tasksは次の正本を全文読んでからファイル境界・依存関係・完了条件を決めてください。このカードの要点だけでタスクを生成してはいけません。",
        "",
        f"- 基本設計・シーケンス・外部境界: [{inputs.basic_design_path.name}]({_relative_link(inputs.basic_design_path, inputs.spec_dir)})",
        f"- 詳細設計・データ・例外・復旧: [{inputs.detailed_design_path.name}]({_relative_link(inputs.detailed_design_path, inputs.spec_dir)})",
        f"- 要件と設計要素の対応: [{inputs.design_traceability_path.name}]({_relative_link(inputs.design_traceability_path, inputs.spec_dir)})",
        f"- 要件本文・受入条件: [{inputs.requirements_path.name}]({_relative_link(inputs.requirements_path, inputs.spec_dir)})",
        f"- 対象phaseのテスト正本（存在時）: [{inputs.phase_label}]({_relative_link(inputs.phase_dir, inputs.spec_dir)})",
        "",
        "## Tanuki設計書へのリンク",
        "",
    ]
    for label, path in links:
        lines.extend(
            [
                f"### {label}",
                f"[{path.name}]({_relative_link(path, inputs.spec_dir)})",
                "",
                "要点:",
            ]
        )
        for point in _key_points(path):
            lines.append(f"- {point}")
        lines.append("")
    lines.extend(["## 設計要素", ""])
    if not elements:
        lines.append("設計要素はありません。")
    for element in elements:
        lines.extend(
            [
                f"### {element.tanuki_id}: {element.name}",
                f"- type: `{element.element_type}`",
                f"- tanuki requirement IDs: {', '.join(element.requirement_ids) or '（なし）'}",
            ]
        )
        mapped: list[str] = []
        numeric_ids: list[str] = []
        excluded_ids: list[str] = []
        for identifier in element.requirement_ids:
            if identifier in number_by_id:
                mapped.append(f"Requirement {number_by_id[identifier]} [{identifier}]")
                numeric_ids.append(str(number_by_id[identifier]))
            else:
                mapped.append(f"除外 [{identifier}] ({status_by_id[identifier]})")
                excluded_ids.append(identifier)
        lines.append(f"- requirement_ids: [{', '.join(numeric_ids)}]" if numeric_ids else "- requirement_ids: []")
        lines.append(f"- cc-sdd requirement map: {', '.join(mapped) or '（なし）'}")
        if excluded_ids:
            lines.append(f"- excluded requirement IDs: {', '.join(excluded_ids)}")
        lines.append("")
    lines.extend(
        [
            "## 境界",
            "",
            "- 採用範囲はrequirements.mdのin_scope/draft要件に限る。",
            "- deferred/out_of_scope要件は設計要素の参照に残っていても実装対象へ昇格させない。",
            "- データモデル、API、画面、テスト、移行の詳細はtanukiの各設計書・テスト正本を参照する。",
            "",
        ]
    )
    return "\n".join(lines)


def _assert_not_symlink(path: Path, label: str) -> None:
    if path.is_symlink():
        raise BridgeError(f"{label}がsymlinkのため安全に扱えません: {path}")


def _assert_no_symlink_components(path: Path, root: Path, label: str) -> None:
    """出力先へ至る既存の各ディレクトリがsymlinkでないことを確認する。"""

    try:
        relative = path.relative_to(root)
    except ValueError as error:
        raise BridgeError(f"{label}がproject rootの外です: {path}") from error
    current = root
    for part in relative.parts:
        current = current / part
        _assert_not_symlink(current, label)


def _check_output_state(spec_dir: Path) -> None:
    """参照カードを読み取る前に出力先の安全性と所有権を確認する。

    この関数は読み取り専用の ``check`` からも呼ばれるため、既存の
    ``tasks.md`` の有無は判定しない。タスクを上書きしないための拒否は、
    実際に書き込む ``render`` 側のガードで行う。
    """

    # `.kiro` や `.kiro/specs` がsymlinkの場合も、意図しない場所への書込みになる。
    project_root = spec_dir.parents[2]
    _assert_no_symlink_components(spec_dir, project_root, "出力specパス")
    if spec_dir.exists():
        _assert_not_symlink(spec_dir, "出力specディレクトリ")
        if not spec_dir.is_dir():
            raise BridgeError(f"出力specパスがディレクトリではありません: {spec_dir}")
        tasks = spec_dir / "tasks.md"
        _assert_not_symlink(tasks, "tasks.md")
        metadata = spec_dir / "spec.json"
        _assert_not_symlink(metadata, "spec.json")
        if not metadata.exists():
            raise BridgeError(f"既存specディレクトリに所有メタデータがありません: {metadata}")
        try:
            parsed = json.loads(metadata.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise BridgeError(f"既存spec.jsonが不正なため上書きしません: {metadata}") from error
        if not isinstance(parsed, dict) or parsed.get("generated_by") != OWNER_MARKER:
            raise BridgeError(f"既存spec.jsonに所有マーカーがないため上書きしません: {metadata}")
    else:
        parent = spec_dir.parent
        if parent.exists():
            _assert_not_symlink(parent, "出力spec親ディレクトリ")
            if not parent.is_dir():
                raise BridgeError(f"出力spec親パスがディレクトリではありません: {parent}")


def _check_render_output_state(spec_dir: Path) -> None:
    """参照カードを書き込む前の安全性と上書き防止を確認する。"""

    _check_output_state(spec_dir)
    tasks = spec_dir / "tasks.md"
    if tasks.exists():
        raise BridgeError(f"既存tasks.mdがあるため上書きしません: {tasks}")


def _write_atomic(path: Path, content: str) -> None:
    _assert_not_symlink(path, str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def generate(inputs: Inputs, approved: bool) -> dict[str, str]:
    active, excluded, elements = load_records(inputs)
    if not active:
        raise BridgeError("cc-sddへ渡せるin_scope/draft要件がありません")
    if approved:
        draft_ids = [item.tanuki_id for item in active if item.status == "draft"]
        if draft_ids:
            raise BridgeError(
                "draft要件が残るためrequirements/designを承認できません: "
                + ", ".join(draft_ids)
            )
    contents = {
        "spec.json": render_spec_json(inputs, active, approved),
        "requirements.md": render_requirements_md(inputs, active, excluded),
        "design.md": render_design_md(inputs, active, excluded, elements),
    }
    for filename, content in contents.items():
        if not content.strip():
            raise BridgeError(f"生成内容が空です: {filename}")
    return contents


def render(inputs: Inputs, approved: bool = False) -> list[Path]:
    _check_render_output_state(inputs.spec_dir)
    contents = generate(inputs, approved)
    inputs.spec_dir.mkdir(parents=True, exist_ok=True)
    for filename, content in contents.items():
        _write_atomic(inputs.spec_dir / filename, content)
    return [inputs.spec_dir / filename for filename in OUTPUT_FILES]


def check(inputs: Inputs, approved: bool = False) -> list[str]:
    _check_output_state(inputs.spec_dir)
    contents = generate(inputs, approved)
    failures: list[str] = []
    for filename, expected in contents.items():
        path = inputs.spec_dir / filename
        _assert_not_symlink(path, filename)
        if not path.is_file():
            failures.append(f"{filename} がありません")
            continue
        if filename == "spec.json":
            actual_spec = json.loads(path.read_text(encoding="utf-8"))
            expected_spec = json.loads(expected)
            actual_bridge_fields = {
                field: actual_spec.get(field)
                for field in BRIDGE_OWNED_SPEC_FIELDS
            }
            expected_bridge_fields = {
                field: expected_spec.get(field)
                for field in BRIDGE_OWNED_SPEC_FIELDS
            }
            if actual_bridge_fields != expected_bridge_fields:
                failures.append(f"{filename} が最新のtanuki入力と一致しません")
            continue
        actual = path.read_text(encoding="utf-8")
        if actual != expected:
            failures.append(f"{filename} が最新のtanuki入力と一致しません")
    return failures


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("render", "check"))
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--phase", required=True, help="project rootからのphaseパス、または絶対パス")
    parser.add_argument("--func", required=True, help="func名（func-は省略可）またはパス")
    parser.add_argument("--spec", required=True, help=".kiro/specs配下のspec名")
    parser.add_argument("--approve", action="store_true", help="requirements/designをapprovedにする")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        inputs = resolve_inputs(args.project_root, args.phase, args.func, args.spec)
        if args.command == "render":
            paths = render(inputs, approved=args.approve)
            print("生成しました:")
            for path in paths:
                print(path)
            return 0
        failures = check(inputs, approved=args.approve)
        if failures:
            for failure in failures:
                print(f"差分: {failure}", file=sys.stderr)
            return 1
        print("check passed")
        return 0
    except BridgeError as error:
        print(f"エラー: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
