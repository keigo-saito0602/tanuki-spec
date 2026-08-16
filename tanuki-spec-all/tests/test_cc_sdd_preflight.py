from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock

from evaluation.cc_sdd_preflight import (
    CC_SDD_VERSION,
    COMPATIBILITY_FILE,
    MODERN_SKILLS,
    PreflightError,
    check,
    ensure,
    inspect,
    install_command,
    legacy_commands,
    load_compatibility,
    required_artifacts,
    _main,
)


class CcSddPreflightTest(unittest.TestCase):
    def _modern(
        self,
        root: Path,
        agent: str,
        names=MODERN_SKILLS,
        *,
        include_artifacts: bool = True,
    ) -> None:
        skill_root = root / (".agents" if agent == "codex" else ".claude") / "skills"
        for name in names:
            skill_dir = skill_root / name
            skill_dir.mkdir(parents=True, exist_ok=True)
            (skill_dir / "SKILL.md").write_text(
                f"---\nname: {name}\ndescription: fixture\n---\n",
                encoding="utf-8",
            )
        if include_artifacts:
            for relative in required_artifacts(agent):
                artifact = root / relative
                artifact.parent.mkdir(parents=True, exist_ok=True)
                artifact.write_text("fixture\n", encoding="utf-8")

    def _legacy(self, root: Path, agent: str, names=None) -> None:
        command_root = root / (
            ".codex/prompts" if agent == "codex" else ".claude/commands/kiro"
        )
        command_root.mkdir(parents=True, exist_ok=True)
        if names is None:
            names = legacy_commands(agent)
        for name in names:
            (command_root / name).write_text(f"# {name}\n", encoding="utf-8")

    def test_missing_modern_legacy_and_partial_are_distinguished_per_agent(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self._modern(root, "codex")
            self._legacy(root, "claude")
            (root / ".agents/skills/kiro-debug/SKILL.md").unlink()

            states = {state.agent: state for state in check(root)}

            self.assertEqual(states["codex"].status, "partial")
            self.assertEqual(states["claude"].status, "legacy")
            self.assertEqual(inspect(root, "codex").modern_missing[0], "kiro-debug")

    def test_complete_modern_requires_every_skill_and_artifact(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self._modern(root, "codex")
            self.assertEqual(inspect(root, "codex").status, "modern")
            self._modern(root, "claude")
            self.assertEqual(inspect(root, "claude").status, "modern")

    def test_missing_artifact_or_invalid_skill_frontmatter_is_partial(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self._modern(root, "codex")
            missing_artifact = root / ".kiro/settings/templates/specs/tasks.md"
            missing_artifact.unlink()

            state = inspect(root, "codex")

            self.assertEqual(state.status, "partial")
            self.assertIn(
                ".kiro/settings/templates/specs/tasks.md",
                state.artifacts_missing,
            )

            missing_artifact.write_text("fixture\n", encoding="utf-8")
            (root / ".agents/skills/kiro-debug/SKILL.md").write_text(
                "---\nname: another-skill\n---\n",
                encoding="utf-8",
            )
            state = inspect(root, "codex")
            self.assertEqual(state.status, "partial")
            self.assertIn("kiro-debug", state.modern_missing)

    def test_modern_and_legacy_mixture_is_partial(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self._modern(root, "codex")
            self._legacy(root, "codex")

            self.assertEqual(inspect(root, "codex").status, "partial")

    def test_existing_agents_and_kiro_are_preserved_without_force_flags(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            agents_file = root / "AGENTS.md"
            agents_file.write_text("project-owned\n", encoding="utf-8")
            kiro = root / ".kiro"
            kiro.mkdir()
            kiro_marker = kiro / "owned.md"
            kiro_marker.write_text("tanuki-owned\n", encoding="utf-8")
            calls: list[tuple[list[str], dict[str, object]]] = []

            def runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
                calls.append((command, kwargs))
                if "--dry-run" not in command:
                    self._modern(root, "codex")
                return subprocess.CompletedProcess(command, 0, "", "")

            result = ensure(root, ("codex",), runner=runner)

            self.assertEqual(result.installed, ("codex",))
            self.assertEqual(agents_file.read_text(encoding="utf-8"), "project-owned\n")
            self.assertEqual(kiro_marker.read_text(encoding="utf-8"), "tanuki-owned\n")
            self.assertEqual(len(calls), 2)
            self.assertTrue(calls[0][0][-1] == "--dry-run")
            self.assertNotIn("--overwrite", calls[0][0])
            self.assertNotIn("--yes", calls[0][0][3:])
            self.assertFalse(calls[0][1]["shell"])
            self.assertFalse(calls[1][1]["shell"])

    def test_partial_or_legacy_never_runs_subprocess(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self._legacy(root, "codex", legacy_commands("codex")[:1])
            runner = Mock()

            with self.assertRaises(PreflightError):
                ensure(root, ("codex",), runner=runner)

            runner.assert_not_called()

    def test_dry_run_that_changes_state_aborts_before_install(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            calls: list[list[str]] = []

            def runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
                calls.append(command)
                if "--dry-run" in command:
                    self._modern(root, "codex", MODERN_SKILLS[:1])
                return subprocess.CompletedProcess(command, 0, "", "")

            with self.assertRaises(PreflightError):
                ensure(root, ("codex",), runner=runner)

            self.assertEqual(len(calls), 1)
            self.assertIn("--dry-run", calls[0])

    def test_dry_run_that_changes_existing_project_file_aborts(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            agents_file = root / "AGENTS.md"
            agents_file.write_text("before\n", encoding="utf-8")

            def runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
                agents_file.write_text("overwritten\n", encoding="utf-8")
                return subprocess.CompletedProcess(command, 0, "", "")

            with self.assertRaisesRegex(PreflightError, "既存ファイル"):
                ensure(root, ("codex",), runner=runner)

    def test_install_that_changes_existing_nested_file_is_not_success(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            settings = root / ".kiro/settings/project.json"
            settings.parent.mkdir(parents=True)
            settings.write_text('{"owned": true}\n', encoding="utf-8")

            def runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
                if "--dry-run" not in command:
                    settings.write_text('{"owned": false}\n', encoding="utf-8")
                    self._modern(root, "codex")
                return subprocess.CompletedProcess(command, 0, "", "")

            with self.assertRaisesRegex(PreflightError, "既存ファイル"):
                ensure(root, ("codex",), runner=runner)

    def test_symlink_in_protected_tree_refuses_automatic_install(self) -> None:
        with TemporaryDirectory() as directory, TemporaryDirectory() as outside:
            root = Path(directory)
            agents = root / ".agents"
            agents.mkdir()
            (agents / "skills").symlink_to(Path(outside), target_is_directory=True)
            runner = Mock()

            with self.assertRaisesRegex(PreflightError, "symlink"):
                ensure(root, ("codex",), runner=runner)

            runner.assert_not_called()

    def test_official_commands_use_shell_false_compatible_argument_vectors(self) -> None:
        self.assertEqual(
            install_command("codex"),
            ("npx", "--yes", "cc-sdd@3.0.2", "--codex-skills", "--lang", "ja"),
        )
        self.assertEqual(
            install_command("claude", dry_run=True),
            (
                "npx",
                "--yes",
                "cc-sdd@3.0.2",
                "--claude-skills",
                "--lang",
                "ja",
                "--dry-run",
            ),
        )
        self.assertEqual(CC_SDD_VERSION, "3.0.2")
        self.assertNotIn("@latest", " ".join(install_command("codex")))

    def test_compatibility_manifest_is_external_and_matches_required_skills(self) -> None:
        compatibility = load_compatibility()

        self.assertEqual(compatibility["dependency"]["distribution"], "external-npm")
        self.assertEqual(compatibility["dependency"]["package"], "cc-sdd")
        self.assertEqual(tuple(compatibility["required_skills"]), MODERN_SKILLS)
        self.assertTrue(COMPATIBILITY_FILE.is_file())

    def test_invalid_compatibility_manifest_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            manifest = Path(directory) / "compatibility.json"
            manifest.write_text(
                '{"schema_version": 1, "dependency": {"distribution": "vendored"}}',
                encoding="utf-8",
            )

            with self.assertRaisesRegex(RuntimeError, "dependency/install"):
                load_compatibility(manifest)

    def test_manifest_rejects_another_package_and_unsafe_agent_flag(self) -> None:
        with TemporaryDirectory() as directory:
            manifest = Path(directory) / "compatibility.json"
            compatibility = load_compatibility()
            compatibility["dependency"]["package"] = "another-package"
            manifest.write_text(
                json.dumps(compatibility, ensure_ascii=False),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(RuntimeError, "許容値"):
                load_compatibility(manifest)

            compatibility = load_compatibility()
            compatibility["install"]["agents"]["codex"]["flag"] = "--overwrite=force"
            manifest.write_text(
                json.dumps(compatibility, ensure_ascii=False),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(RuntimeError, "許容値"):
                load_compatibility(manifest)

    def test_cli_accepts_legacy_flag_shape_used_by_existing_skill_docs(self) -> None:
        with TemporaryDirectory() as directory:
            self.assertEqual(_main([directory, "--agent", "codex", "--check"]), 0)


if __name__ == "__main__":
    unittest.main()
