from __future__ import annotations
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evaluation"))
import render_task_plan


def task(**overrides) -> dict:
    base = {
        "id": "TASK-001",
        "status": "in_scope",
        "title": "予約APIを実装する",
        "type": "backend",
        "requirement_ids": ["FR-001"],
        "depends_on": [],
        "definition_of_done": ["実装がある"],
        "verification": ["テストを実行する"],
    }
    base.update(overrides)
    return base


class SanitizeTest(unittest.TestCase):
    def test_removes_characters_that_break_mermaid_syntax(self):
        result = render_task_plan.sanitize('予約"API"[本体](詳細)|区切り\n改行')
        for char in ('"', "[", "]", "(", ")", "|", "\n"):
            self.assertNotIn(char, result)


class WorkableListTest(unittest.TestCase):
    def test_task_without_dependency_and_without_progress_is_workable(self):
        tasks = [task()]
        lines = render_task_plan.render_workable_list(tasks)
        self.assertTrue(any("TASK-001" in line for line in lines))

    def test_task_depending_on_unfinished_task_is_not_workable(self):
        tasks = [task(id="TASK-001", progress="doing"), task(id="TASK-002", depends_on=["TASK-001"])]
        lines = render_task_plan.render_workable_list(tasks)
        workable_ids = [line for line in lines if line.startswith("- ")]
        self.assertFalse(any(line.startswith("- TASK-002") for line in workable_ids))

    def test_task_depending_on_done_task_is_workable(self):
        tasks = [task(id="TASK-001", progress="done"), task(id="TASK-002", depends_on=["TASK-001"])]
        lines = render_task_plan.render_workable_list(tasks)
        self.assertTrue(any("TASK-002" in line for line in lines))

    def test_no_workable_tasks_shows_explicit_message(self):
        tasks = [task(id="TASK-001", progress="doing")]
        lines = render_task_plan.render_workable_list(tasks)
        self.assertTrue(any("着手可能なタスクはありません" in line for line in lines))


class MindmapTest(unittest.TestCase):
    def test_groups_tasks_by_type(self):
        tasks = [task(id="TASK-001", type="backend"), task(id="TASK-002", type="design", title="画面設計")]
        lines = render_task_plan.render_mindmap(tasks, "MVP")
        text = "\n".join(lines)
        self.assertIn("mindmap", text)
        self.assertIn("backend", text)
        self.assertIn("design", text)
        self.assertIn("TASK-001", text)
        self.assertIn("TASK-002", text)


class FlowchartTest(unittest.TestCase):
    def test_renders_dependency_edge_from_dependency_to_dependent(self):
        tasks = [task(id="TASK-001"), task(id="TASK-002", depends_on=["TASK-001"])]
        lines = render_task_plan.render_flowchart(tasks)
        text = "\n".join(lines)
        self.assertIn("TASK-001 --> TASK-002", text)


class GanttTest(unittest.TestCase):
    def test_no_start_date_anywhere_skips_gantt_with_reason(self):
        tasks = [task(id="TASK-001"), task(id="TASK-002")]
        lines = render_task_plan.render_gantt_or_reason(tasks)
        text = "\n".join(lines)
        self.assertIn("start_date が未設定のためガントを生成しません", text)
        self.assertNotIn("gantt", text)

    def test_missing_duration_on_dated_task_skips_gantt_and_lists_ids(self):
        tasks = [task(id="TASK-001", start_date="2026-08-01"), task(id="TASK-002", start_date="2026-08-03")]
        lines = render_task_plan.render_gantt_or_reason(tasks)
        text = "\n".join(lines)
        self.assertIn("duration が未設定のタスクがあるためガントを生成しません", text)
        self.assertIn("TASK-001", text)
        self.assertIn("TASK-002", text)
        self.assertNotIn("gantt", text)

    def test_complete_dates_and_durations_render_gantt(self):
        tasks = [task(id="TASK-001", start_date="2026-08-01", duration="2d")]
        lines = render_task_plan.render_gantt_or_reason(tasks)
        text = "\n".join(lines)
        self.assertIn("gantt", text)
        self.assertIn("TASK-001, 2026-08-01, 2d", text)

    def test_multiple_dependencies_use_after_syntax(self):
        tasks = [
            task(id="TASK-001", start_date="2026-08-01", duration="1d"),
            task(id="TASK-002", start_date="2026-08-01", duration="1d"),
            task(id="TASK-003", duration="2d", depends_on=["TASK-001", "TASK-002"]),
        ]
        lines = render_task_plan.render_gantt_or_reason(tasks)
        text = "\n".join(lines)
        self.assertIn("TASK-003, after TASK-001 TASK-002, 2d", text)


class DocumentIntegrationTest(unittest.TestCase):
    def test_existing_table_output_is_preserved(self):
        """既存のMarkdownテーブル生成は壊さない。"""
        data = {"release": "MVP", "tasks": [task()]}
        text = render_task_plan.build_document(data)
        self.assertIn("| ID | タスク | 種別 | 要件 | 依存 | 完了条件 | 検証 |", text)
        self.assertIn("TASK-001", text)

    def test_new_sections_precede_existing_table(self):
        data = {"release": "MVP", "tasks": [task()]}
        text = render_task_plan.build_document(data)
        workable_index = text.index("着手可能なタスク")
        table_index = text.index("| ID | タスク")
        self.assertLess(workable_index, table_index)


if __name__ == "__main__":
    unittest.main()
