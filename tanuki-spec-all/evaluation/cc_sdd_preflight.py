#!/usr/bin/env python3
"""cc-sdd の導入状態を検査し、安全な導入を行うプリフライト。

このモジュールは cc-sdd 自体を再実装しない。プロジェクト内の
Agent Skills/legacy command の存在を検査し、未導入のときだけ互換性台帳で
検証済みの公式npmパッケージを呼び出す。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Literal, Sequence


Agent = Literal["codex", "claude"]
Status = Literal["modern", "legacy", "partial", "missing"]

AGENTS: tuple[Agent, ...] = ("codex", "claude")

COMPATIBILITY_FILE = (
    Path(__file__).resolve().parents[1]
    / "integrations"
    / "cc-sdd"
    / "compatibility.json"
)


def load_compatibility(path: str | Path = COMPATIBILITY_FILE) -> dict[str, Any]:
    """外部依存cc-sddの互換性台帳を読み、実行に必要な形を検証する。"""

    compatibility_path = Path(path)
    try:
        raw = json.loads(compatibility_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(
            f"cc-sdd互換性台帳を読めません: {compatibility_path}: {error}"
        ) from error

    if not isinstance(raw, dict) or raw.get("schema_version") != 1:
        raise RuntimeError("cc-sdd互換性台帳のschema_versionは1である必要があります")

    dependency = raw.get("dependency")
    install = raw.get("install")
    required_skills = raw.get("required_skills")
    required_artifacts = raw.get("required_artifacts")
    if not isinstance(dependency, dict) or not isinstance(install, dict):
        raise RuntimeError("cc-sdd互換性台帳のdependency/installが不正です")

    for key in ("package", "tested_version", "distribution", "repository", "license"):
        if not isinstance(dependency.get(key), str) or not dependency[key].strip():
            raise RuntimeError(f"cc-sdd互換性台帳のdependency.{key}が不正です")
    if dependency["distribution"] != "external-npm":
        raise RuntimeError("cc-sddはexternal-npmとして管理する必要があります")
    expected_dependency = {
        "package": "cc-sdd",
        "distribution": "external-npm",
        "repository": "https://github.com/gotalab/cc-sdd",
        "license": "MIT",
    }
    for key, expected in expected_dependency.items():
        if dependency[key] != expected:
            raise RuntimeError(f"cc-sdd互換性台帳のdependency.{key}が許容値ではありません")
    version_parts = dependency["tested_version"].split(".")
    if len(version_parts) != 3 or any(not part.isdigit() for part in version_parts):
        raise RuntimeError("cc-sdd互換性台帳のtested_versionは完全SemVerで指定してください")

    language = install.get("language")
    agent_settings = install.get("agents")
    if language != "ja":
        raise RuntimeError("cc-sdd互換性台帳のinstall.languageが不正です")
    if not isinstance(agent_settings, dict) or set(agent_settings) != set(AGENTS):
        raise RuntimeError("cc-sdd互換性台帳のinstall.agentsが不正です")
    for agent in AGENTS:
        settings = agent_settings.get(agent)
        if not isinstance(settings, dict):
            raise RuntimeError(f"cc-sdd互換性台帳の{agent}設定が不正です")
        for key in ("flag", "skills_root"):
            if not isinstance(settings.get(key), str) or not settings[key]:
                raise RuntimeError(f"cc-sdd互換性台帳の{agent}.{key}が不正です")
        skills_root = Path(settings["skills_root"])
        if skills_root.is_absolute() or ".." in skills_root.parts:
            raise RuntimeError(f"cc-sdd互換性台帳の{agent}.skills_rootが危険です")
    expected_agent_settings = {
        "codex": {"flag": "--codex-skills", "skills_root": ".agents/skills"},
        "claude": {"flag": "--claude-skills", "skills_root": ".claude/skills"},
    }
    if agent_settings != expected_agent_settings:
        raise RuntimeError("cc-sdd互換性台帳の導入フラグまたは配置先が許容値ではありません")

    if (
        not isinstance(required_skills, list)
        or not required_skills
        or any(not isinstance(skill, str) or not skill for skill in required_skills)
        or len(set(required_skills)) != len(required_skills)
    ):
        raise RuntimeError("cc-sdd互換性台帳のrequired_skillsが不正です")

    if not isinstance(required_artifacts, dict):
        raise RuntimeError("cc-sdd互換性台帳のrequired_artifactsが不正です")
    shared_artifacts = required_artifacts.get("shared")
    agent_artifacts = required_artifacts.get("agents")
    skill_resources = required_artifacts.get("skill_resources")
    if not isinstance(agent_artifacts, dict) or set(agent_artifacts) != set(AGENTS):
        raise RuntimeError("cc-sdd互換性台帳のrequired_artifacts.agentsが不正です")
    artifact_groups = [shared_artifacts, skill_resources, *agent_artifacts.values()]
    for artifacts in artifact_groups:
        if not isinstance(artifacts, list) or any(
            not isinstance(value, str) or not value for value in artifacts
        ):
            raise RuntimeError("cc-sdd互換性台帳のartifact一覧が不正です")
        for value in artifacts:
            artifact_path = Path(value)
            if artifact_path.is_absolute() or ".." in artifact_path.parts:
                raise RuntimeError(f"cc-sdd互換性台帳のartifactパスが危険です: {value}")

    return raw


COMPATIBILITY = load_compatibility()
DEPENDENCY = COMPATIBILITY["dependency"]
INSTALL = COMPATIBILITY["install"]
AGENT_SETTINGS: dict[str, dict[str, str]] = INSTALL["agents"]
CC_SDD_PACKAGE = DEPENDENCY["package"]
CC_SDD_VERSION = DEPENDENCY["tested_version"]
CC_SDD_LANGUAGE = INSTALL["language"]

# 検証済み版のskills-mode一式。全て揃っている場合だけmodernとする。
MODERN_SKILLS: tuple[str, ...] = tuple(COMPATIBILITY["required_skills"])
REQUIRED_ARTIFACTS: dict[str, Any] = COMPATIBILITY["required_artifacts"]

# v1/v2 の command mode。Claude の --claude-agent も commands を共有する。
# Claude は `.claude/commands/kiro/spec-*.md`、Codex は `.codex/prompts/kiro-*.md`
# という別のファイル名規則を使うため、エージェントごとに定義する。
LEGACY_COMMANDS: tuple[str, ...] = (
    "spec-design.md",
    "spec-impl.md",
    "spec-init.md",
    "spec-requirements.md",
    "spec-status.md",
    "spec-tasks.md",
    "steering-custom.md",
    "steering.md",
    "validate-design.md",
    "validate-gap.md",
    "validate-impl.md",
)

LEGACY_COMMANDS_BY_AGENT: dict[Agent, tuple[str, ...]] = {
    "claude": LEGACY_COMMANDS,
    "codex": tuple(f"kiro-{command}" for command in LEGACY_COMMANDS),
}

COMMAND = ("npx", "--yes", f"{CC_SDD_PACKAGE}@{CC_SDD_VERSION}")
PROTECTED_ROOT_FILES = ("AGENTS.md", "CLAUDE.md")
PROTECTED_DIRECTORIES = (".agents", ".codex", ".claude", ".kiro")


class PreflightError(RuntimeError):
    """プリフライトまたは導入を安全に続行できない場合のエラー。"""


@dataclass(frozen=True)
class InstallationState:
    """一つのエージェント向け cc-sdd の検査結果。"""

    agent: Agent
    status: Status
    modern_found: tuple[str, ...]
    modern_missing: tuple[str, ...]
    artifacts_found: tuple[str, ...]
    artifacts_missing: tuple[str, ...]
    legacy_found: tuple[str, ...]
    legacy_missing: tuple[str, ...]

    @property
    def is_installable(self) -> bool:
        """この状態が安全な新規導入対象かを返す。"""

        return self.status == "missing"


@dataclass(frozen=True)
class EnsureResult:
    """ensure の結果。導入しなかった場合も理由を保持する。"""

    states: tuple[InstallationState, ...]
    installed: tuple[Agent, ...]


def _modern_root(project_dir: Path, agent: Agent) -> Path:
    return project_dir / AGENT_SETTINGS[agent]["skills_root"]


def required_artifacts(agent: Agent) -> tuple[str, ...]:
    """検証済み版で必要な共有・エージェント別・Skill内ファイルを返す。"""

    if agent not in AGENTS:
        raise ValueError(f"未対応のエージェントです: {agent}")
    skills_root = Path(AGENT_SETTINGS[agent]["skills_root"])
    skill_resources = tuple(
        (skills_root / value).as_posix()
        for value in REQUIRED_ARTIFACTS["skill_resources"]
    )
    return (
        *REQUIRED_ARTIFACTS["shared"],
        *REQUIRED_ARTIFACTS["agents"][agent],
        *skill_resources,
    )


def _legacy_root(project_dir: Path, agent: Agent) -> Path:
    return project_dir / (".codex/prompts" if agent == "codex" else ".claude/commands/kiro")


def _modern_found(project_dir: Path, agent: Agent) -> tuple[str, ...]:
    root = _modern_root(project_dir, agent)
    return tuple(
        skill
        for skill in MODERN_SKILLS
        if _is_named_skill(root / skill / "SKILL.md", skill)
    )


def _is_named_skill(path: Path, expected_name: str) -> bool:
    """SKILL.mdのfrontmatter名が検証済みSkill名と一致するか確認する。"""

    if not path.is_file():
        return False
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False
    if not text.startswith("---"):
        return False
    parts = text.split("---", 2)
    if len(parts) < 3:
        return False
    return any(
        line.strip() == f"name: {expected_name}"
        for line in parts[1].splitlines()
    )


def _artifacts_found(project_dir: Path, agent: Agent) -> tuple[str, ...]:
    return tuple(
        relative
        for relative in required_artifacts(agent)
        if (project_dir / relative).is_file()
        and (project_dir / relative).stat().st_size > 0
    )


def _legacy_found(project_dir: Path, agent: Agent) -> tuple[str, ...]:
    root = _legacy_root(project_dir, agent)
    commands = LEGACY_COMMANDS_BY_AGENT[agent]
    return tuple(command for command in commands if (root / command).is_file())


def legacy_commands(agent: Agent) -> tuple[str, ...]:
    """指定エージェントのlegacy commandファイル名を返す。"""

    if agent not in AGENTS:
        raise ValueError(f"未対応のエージェントです: {agent}")
    return LEGACY_COMMANDS_BY_AGENT[agent]


def _status(
    modern_found: tuple[str, ...],
    artifacts_found: tuple[str, ...],
    legacy_found: tuple[str, ...],
    agent: Agent,
) -> Status:
    modern_complete = len(modern_found) == len(MODERN_SKILLS)
    artifacts_complete = len(artifacts_found) == len(required_artifacts(agent))
    # `_status` は agent ごとに legacy の期待数が同じであるため、件数だけを比較する。
    legacy_complete = len(legacy_found) == len(LEGACY_COMMANDS)

    # 必須Skill・補助ファイルの欠落やlegacyとの混在はpartialとして止める。
    if modern_complete and artifacts_complete and not legacy_found:
        return "modern"
    if legacy_complete and not modern_found:
        return "legacy"
    if modern_found or legacy_found:
        return "partial"
    return "missing"


def inspect(project_dir: str | Path, agent: Agent) -> InstallationState:
    """プロジェクト内の指定エージェントの cc-sdd 状態を検査する。

    ``AGENTS.md``と``CLAUDE.md``はプロジェクト資産なので状態判定に使わない。
    ``.kiro/settings``はcc-sdd実行に必要な配布物だけを検査する。
    """

    if agent not in AGENTS:
        raise ValueError(f"未対応のエージェントです: {agent}")
    root = Path(project_dir).expanduser().resolve()
    if not root.is_dir():
        raise PreflightError(f"プロジェクトディレクトリがありません: {root}")

    modern_found = _modern_found(root, agent)
    artifacts_found = _artifacts_found(root, agent)
    legacy_found = _legacy_found(root, agent)
    status = _status(modern_found, artifacts_found, legacy_found, agent)
    return InstallationState(
        agent=agent,
        status=status,
        modern_found=modern_found,
        modern_missing=tuple(skill for skill in MODERN_SKILLS if skill not in modern_found),
        artifacts_found=artifacts_found,
        artifacts_missing=tuple(
            artifact
            for artifact in required_artifacts(agent)
            if artifact not in artifacts_found
        ),
        legacy_found=legacy_found,
        legacy_missing=tuple(
            command
            for command in LEGACY_COMMANDS_BY_AGENT[agent]
            if command not in legacy_found
        ),
    )


def check(project_dir: str | Path, agents: Sequence[Agent] = AGENTS) -> tuple[InstallationState, ...]:
    """指定エージェントの状態を検査する。ファイルは変更しない。"""

    return tuple(inspect(project_dir, agent) for agent in agents)


def install_command(
    agent: Agent,
    *,
    dry_run: bool = False,
) -> tuple[str, ...]:
    """公式 v3 導入コマンドを返す。

    cc-sddのデフォルト`prompt`を使う。非TTYでは既存ファイルを保持し新規だけを
    追加する。`--yes`（cc-sdd側の強制承認）や`--overwrite force/skip`は付けない。
    特に`skip`はカテゴリ単位で新規ファイルまで省略する版があるため使わない。
    """

    if agent not in AGENTS:
        raise ValueError(f"未対応のエージェントです: {agent}")
    command = list(COMMAND)
    command.append(AGENT_SETTINGS[agent]["flag"])
    command.extend(("--lang", CC_SDD_LANGUAGE))
    if dry_run:
        command.append("--dry-run")
    return tuple(command)


Runner = Callable[..., subprocess.CompletedProcess[str]]


def _protected_snapshot(project_dir: Path) -> dict[str, str]:
    """導入前からあるプロジェクト資産の内容を記録する。

    新規ファイルの追加は許可するが、既存ファイルの変更・削除は検知する。
    導入先になり得る保護ディレクトリ内のsymlinkは、プロジェクト外へ書き込む
    経路になり得るため自動導入では拒否する。
    """

    snapshot: dict[str, str] = {}
    candidates = [project_dir / name for name in PROTECTED_ROOT_FILES]
    for directory_name in PROTECTED_DIRECTORIES:
        directory = project_dir / directory_name
        if directory.is_symlink():
            raise PreflightError(f"保護対象ディレクトリがsymlinkのため自動導入できません: {directory}")
        if directory.exists():
            candidates.append(directory)
            candidates.extend(directory.rglob("*"))

    for path in candidates:
        if not path.exists() and not path.is_symlink():
            continue
        relative = path.relative_to(project_dir).as_posix()
        if path.is_symlink():
            raise PreflightError(f"保護対象内にsymlinkがあるため自動導入できません: {path}")
        if path.is_file():
            snapshot[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return snapshot


def _assert_snapshot_unchanged(project_dir: Path, before: dict[str, str], phase: str) -> None:
    """既存ファイルが公式CLIによって変更・削除されていないことを確認する。"""

    changed: list[str] = []
    for relative, expected_hash in before.items():
        path = project_dir / relative
        if not path.is_file() or path.is_symlink():
            changed.append(relative)
            continue
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            changed.append(relative)
    if changed:
        names = ", ".join(changed[:10])
        suffix = " ..." if len(changed) > 10 else ""
        raise PreflightError(
            f"cc-sdd {phase} が既存ファイルを変更したため中止しました: {names}{suffix}。"
            "変更内容を確認し、必要ならGitから復元してください。"
        )


def _run(
    command: Sequence[str], project_dir: Path, runner: Runner
) -> subprocess.CompletedProcess[str]:
    """shell を介さず公式コマンドを実行する。"""

    try:
        return runner(
            list(command),
            cwd=str(project_dir),
            shell=False,
            check=False,
            text=True,
            capture_output=True,
        )
    except OSError as error:
        raise PreflightError(f"cc-sdd のコマンドを起動できません: {error}") from error


def _command_failure(
    phase: str, result: subprocess.CompletedProcess[str]
) -> PreflightError:
    output = "\n".join(part for part in (result.stdout, result.stderr) if part).strip()
    suffix = f"\n{output}" if output else ""
    return PreflightError(f"cc-sdd {phase} が失敗しました (exit={result.returncode}){suffix}")


def ensure(
    project_dir: str | Path,
    agents: Sequence[Agent] = AGENTS,
    *,
    runner: Runner | None = None,
) -> EnsureResult:
    """未導入のエージェントだけを dry-run 後に導入する。

    ``partial`` と ``legacy`` が一つでもあれば全体を中止する。複数エージェント
    を指定した際に、一方だけ導入して状態をさらに複雑にすることを避けるためである。
    """

    root = Path(project_dir).expanduser().resolve()
    command_runner = subprocess.run if runner is None else runner
    states = check(root, agents)
    unsafe = tuple(state for state in states if state.status in ("partial", "legacy"))
    if unsafe:
        summary = ", ".join(f"{state.agent}={state.status}" for state in unsafe)
        raise PreflightError(
            f"既存の cc-sdd 導入（{summary}）があるため自動導入を中止しました。"
            "既存ファイルを確認し、手動で移行してください。"
        )

    missing_agents = tuple(state.agent for state in states if state.status == "missing")
    if not missing_agents:
        return EnsureResult(states=states, installed=())

    protected_before = _protected_snapshot(root)

    # dry-run も対象エージェントごとに実行する。dry-run 後に状態を再検査し、
    # ツールや別プロセスが部分導入した場合は本導入へ進まない。
    for agent in missing_agents:
        dry_run_result = _run(
            install_command(agent, dry_run=True), root, command_runner
        )
        if dry_run_result.returncode != 0:
            raise _command_failure("dry-run", dry_run_result)
        _assert_snapshot_unchanged(root, protected_before, "dry-run")
        after_dry_run = inspect(root, agent)
        if after_dry_run.status != "missing":
            raise PreflightError(
                f"{agent} の dry-run 後に状態が {after_dry_run.status} へ変化したため、"
                "本導入を中止しました。"
            )

    installed: list[Agent] = []
    for agent in missing_agents:
        install_result = _run(
            install_command(agent), root, command_runner
        )
        if install_result.returncode != 0:
            raise _command_failure("導入", install_result)
        _assert_snapshot_unchanged(root, protected_before, "導入")
        after_install = inspect(root, agent)
        if after_install.status != "modern":
            raise PreflightError(
                f"{agent} の導入後も modern になりませんでした（"
                f"{after_install.status}）。生成物を確認してください。"
            )
        installed.append(agent)

    return EnsureResult(states=check(root, agents), installed=tuple(installed))


def _format_state(state: InstallationState) -> str:
    details = [
        f"modern={len(state.modern_found)}/{len(MODERN_SKILLS)}",
        f"artifacts={len(state.artifacts_found)}/{len(required_artifacts(state.agent))}",
        f"legacy={len(state.legacy_found)}/{len(LEGACY_COMMANDS_BY_AGENT[state.agent])}",
    ]
    return f"{state.agent}: {state.status} ({', '.join(details)})"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="cc-sdd の導入状態を検査・導入します")
    subparsers = parser.add_subparsers(dest="operation", required=True)
    for operation in ("check", "ensure"):
        subparser = subparsers.add_parser(operation)
        subparser.add_argument(
            "project",
            nargs="?",
            default=".",
            type=Path,
            help="対象プロジェクト（既定: カレントディレクトリ）",
        )
        subparser.add_argument(
            "--agent",
            choices=("codex", "claude", "both"),
            default="both",
            help="対象エージェント（既定: codex と claude）",
        )
        subparser.add_argument("--json", action="store_true", help="結果を JSON で出力")
    return parser


def _selected_agents(value: str) -> tuple[Agent, ...]:
    if value == "both":
        return AGENTS
    if value == "codex":
        return ("codex",)
    return ("claude",)


def _main(argv: Sequence[str] | None = None) -> int:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    # 移行期間中のスキル文書が使う旧形（`<project> --ensure` / `--check`）も
    # 受け付ける。正規の公開CLIは `check <project>` / `ensure <project>`。
    legacy_operations = [
        operation for operation in ("check", "ensure") if f"--{operation}" in raw_args
    ]
    if legacy_operations:
        if len(legacy_operations) != 1:
            print("エラー: --check と --ensure は同時に指定できません。", file=sys.stderr)
            return 2
        operation = legacy_operations[0]
        raw_args = [arg for arg in raw_args if arg != f"--{operation}"]
        raw_args.insert(0, operation)

    args = _parser().parse_args(raw_args)
    agents = _selected_agents(args.agent)
    try:
        if args.operation == "check":
            result: Any = check(args.project, agents)
            if args.json:
                print(json.dumps([asdict(state) for state in result], ensure_ascii=False, indent=2))
            else:
                for state in result:
                    print(_format_state(state))
            return 0

        result = ensure(args.project, agents)
        if args.json:
            print(
                json.dumps(
                    {
                        "states": [asdict(state) for state in result.states],
                        "installed": list(result.installed),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            for state in result.states:
                print(_format_state(state))
            if result.installed:
                print(f"導入しました: {', '.join(result.installed)}")
            else:
                print("導入は不要です。")
        return 0
    except (PreflightError, ValueError) as error:
        print(f"エラー: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(_main())
