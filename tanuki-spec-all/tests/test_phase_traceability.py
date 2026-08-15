from __future__ import annotations

import sys
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evaluation"))
import phase_traceability


FUNC_A = """
version: "1.0"
user_stories:
  - id: US-001
    status: in_scope
    statement: "利用者は予約をしたい。なぜなら講座を受けたいから。"
requirements:
  - id: FR-001
    status: in_scope
    type: functional
    statement: "利用者は予約を確定できる"
    user_story_ids: [US-001]
    flow_step_ids: [BF-001-S01]
"""

FUNC_B = """
version: "1.0"
user_stories:
  - id: US-002
    status: in_scope
    statement: "利用者はログインしたい。なぜなら予約するには本人確認が要るから。"
requirements:
  - id: FR-002
    status: in_scope
    type: functional
    statement: "利用者はログインできる"
    user_story_ids: [US-002]
    flow_step_ids: [BF-001-S01]
"""

FUNC_B_DUPLICATE_ID = """
version: "1.0"
user_stories:
  - id: US-002
    status: in_scope
    statement: "利用者はログインしたい。なぜなら予約するには本人確認が要るから。"
requirements:
  - id: FR-001
    status: in_scope
    type: functional
    statement: "利用者はログインできる"
    user_story_ids: [US-002]
    flow_step_ids: [BF-001-S01]
"""

FUNC_INVALID_STATUS = """
version: "1.0"
user_stories:
  - id: US-003
    status: in_scope
    statement: "利用者はキャンセルしたい。なぜなら予定が変わったから。"
requirements:
  - id: FR-003
    status: not_a_valid_status
    type: functional
    statement: "利用者は予約をキャンセルできる"
    user_story_ids: [US-003]
    flow_step_ids: [BF-001-S01]
"""

FUNC_UNRESOLVED_USER_STORY = """
version: "1.0"
user_stories:
  - id: US-004
    status: in_scope
    statement: "利用者は通知を受け取りたい。なぜなら予約確認をしたいから。"
requirements:
  - id: FR-004
    status: in_scope
    type: functional
    statement: "利用者は通知を受け取れる"
    user_story_ids: [US-999]
    flow_step_ids: [BF-001-S01]
"""


class PhaseTraceabilityTest(unittest.TestCase):
    def _write(self, directory: Path, name: str, content: str) -> None:
        func_dir = directory / name
        func_dir.mkdir(parents=True, exist_ok=True)
        (func_dir / "traceability.yaml").write_text(content, encoding="utf-8")

    def test_merges_requirements_and_user_stories_across_funcs(self):
        with tempfile.TemporaryDirectory() as directory_str:
            directory = Path(directory_str)
            self._write(directory, "func-予約", FUNC_A)
            self._write(directory, "func-認証", FUNC_B)
            system_path = directory / "system-traceability.yaml"
            system_data = {
                "func_traceability": ["func-予約/traceability.yaml", "func-認証/traceability.yaml"]
            }
            user_stories, requirements, failures = phase_traceability.build_phase_index(system_path, system_data)
            self.assertEqual(failures, [])
            self.assertEqual(set(user_stories), {"US-001", "US-002"})
            self.assertEqual(set(requirements), {"FR-001", "FR-002"})

    def test_duplicate_requirement_id_across_funcs_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory_str:
            directory = Path(directory_str)
            self._write(directory, "func-予約", FUNC_A)
            self._write(directory, "func-認証", FUNC_B_DUPLICATE_ID)
            system_path = directory / "system-traceability.yaml"
            system_data = {
                "func_traceability": ["func-予約/traceability.yaml", "func-認証/traceability.yaml"]
            }
            _, _, failures = phase_traceability.build_phase_index(system_path, system_data)
            self.assertTrue(
                any("FR-001" in failure and "重複" in failure for failure in failures),
                msg=f"重複が検出されるべきです: {failures}",
            )

    def test_missing_func_traceability_file_is_reported(self):
        with tempfile.TemporaryDirectory() as directory_str:
            directory = Path(directory_str)
            system_path = directory / "system-traceability.yaml"
            system_data = {"func_traceability": ["func-存在しない/traceability.yaml"]}
            _, _, failures = phase_traceability.build_phase_index(system_path, system_data)
            self.assertTrue(any("読み込めません" in failure for failure in failures))

    def test_empty_func_traceability_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory_str:
            directory = Path(directory_str)
            system_path = directory / "system-traceability.yaml"
            _, _, failures = phase_traceability.build_phase_index(system_path, {"func_traceability": []})
            self.assertTrue(any("func_traceability" in failure for failure in failures))

    def test_relative_func_traceability_computes_posix_path(self):
        with tempfile.TemporaryDirectory() as directory_str:
            directory = Path(directory_str)
            system_path = directory / "system-traceability.yaml"
            func_path = directory / "func-予約" / "traceability.yaml"
            self.assertEqual(
                phase_traceability.relative_func_traceability(system_path, func_path),
                "func-予約/traceability.yaml",
            )

    def test_absolute_path_in_func_traceability_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory_str:
            directory = Path(directory_str)
            self._write(directory, "func-予約", FUNC_A)
            system_path = directory / "system-traceability.yaml"
            absolute = str((directory / "func-予約" / "traceability.yaml").resolve())
            _, _, failures = phase_traceability.build_phase_index(system_path, {"func_traceability": [absolute]})
            self.assertTrue(any("相対パスで指定してください" in failure for failure in failures))

    def test_escaping_phase_directory_via_dotdot_is_rejected(self):
        """`../`で別phaseのfuncを参照しようとしても拒否する
        （`func-<名前>/traceability.yaml`の正規形チェックで弾かれる）。"""
        with tempfile.TemporaryDirectory() as directory_str:
            root = Path(directory_str)
            phase_a = root / "phase-1"
            phase_b = root / "phase-2"
            self._write(phase_b, "func-他phase", FUNC_A)
            system_path = phase_a / "system-traceability.yaml"
            phase_a.mkdir(parents=True, exist_ok=True)
            escaping = "../phase-2/func-他phase/traceability.yaml"
            _, _, failures = phase_traceability.build_phase_index(system_path, {"func_traceability": [escaping]})
            self.assertTrue(any("func-<名前>/traceability.yaml" in failure for failure in failures))

    def test_non_func_prefixed_path_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory_str:
            directory = Path(directory_str)
            self._write(directory, "not-a-func-dir", FUNC_A)
            system_path = directory / "system-traceability.yaml"
            _, _, failures = phase_traceability.build_phase_index(
                system_path, {"func_traceability": ["not-a-func-dir/traceability.yaml"]}
            )
            self.assertTrue(any("func-<名前>/traceability.yaml" in failure for failure in failures))

    def test_func_with_invalid_status_is_rejected_before_merge(self):
        """funcのtraceability.yaml自体がtraceability_gate.validate()に落ちる場合、
        phase側の索引へ混入させず、funcパス付きで報告する。"""
        with tempfile.TemporaryDirectory() as directory_str:
            directory = Path(directory_str)
            self._write(directory, "func-キャンセル", FUNC_INVALID_STATUS)
            system_path = directory / "system-traceability.yaml"
            system_data = {"func_traceability": ["func-キャンセル/traceability.yaml"]}
            user_stories, requirements, failures = phase_traceability.build_phase_index(system_path, system_data)
            self.assertEqual(user_stories, {})
            self.assertEqual(requirements, {})
            self.assertTrue(
                any("func-キャンセル/traceability.yaml" in failure and "status" in failure for failure in failures),
                msg=f"funcの構造検証エラーがfuncパス付きで報告されるべきです: {failures}",
            )

    def test_func_with_unresolved_user_story_reference_is_rejected_before_merge(self):
        """funcの中で閉じないrequirement→user_story_ids参照は、マージ前にfunc単体で弾く。"""
        with tempfile.TemporaryDirectory() as directory_str:
            directory = Path(directory_str)
            self._write(directory, "func-通知", FUNC_UNRESOLVED_USER_STORY)
            system_path = directory / "system-traceability.yaml"
            system_data = {"func_traceability": ["func-通知/traceability.yaml"]}
            _, _, failures = phase_traceability.build_phase_index(system_path, system_data)
            self.assertTrue(
                any("func-通知/traceability.yaml" in failure and "US-999" in failure for failure in failures),
                msg=f"未解決のuser_story_ids参照がfuncパス付きで報告されるべきです: {failures}",
            )

    def test_symlinked_func_directory_escaping_phase_is_rejected(self):
        """func-*/がphase直下に実在していても、symlinkでphase外を指していれば拒否する
        （正規形チェックは通るが、resolve()後の境界チェックで弾かれるケース）。"""
        with tempfile.TemporaryDirectory() as directory_str:
            root = Path(directory_str)
            phase_dir = root / "phase-1"
            outside_dir = root / "outside"
            phase_dir.mkdir(parents=True, exist_ok=True)
            self._write(outside_dir, "func-outside", FUNC_A)
            # phase_dir直下に「func-予約」という名前のsymlinkを作り、phase外の実ディレクトリを指す
            (phase_dir / "func-予約").symlink_to(outside_dir / "func-outside")
            system_path = phase_dir / "system-traceability.yaml"
            _, _, failures = phase_traceability.build_phase_index(
                system_path, {"func_traceability": ["func-予約/traceability.yaml"]}
            )
            self.assertTrue(
                any("phase直下のfunc-*/を指してください" in failure for failure in failures),
                msg=f"symlinkによるphase外参照が拒否されるべきです: {failures}",
            )


if __name__ == "__main__":
    unittest.main()
