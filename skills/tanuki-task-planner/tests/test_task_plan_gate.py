from __future__ import annotations
import sys
from pathlib import Path
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evaluation"))
import task_plan_gate

TRACE_PATH = ROOT.parent / "tanuki-spec-generator" / "examples" / "sample-user-story" / "traceability.yaml"

def complete_plan(trace: dict) -> dict:
    tasks = []
    for index, requirement in enumerate(trace["requirements"], start=1):
        requirement_id = requirement["id"]
        acceptance = [item["id"] for item in trace["acceptance_tests"] if requirement_id in item["requirement_ids"]]
        system = [item["id"] for item in trace["system_tests"] if requirement_id in item["requirement_ids"]]
        tasks.append({"id": f"TASK-{index:03d}", "status": "in_scope", "title": f"{requirement_id}を実装する", "type": "backend", "requirement_ids": [requirement_id], "acceptance_test_ids": acceptance, "system_test_ids": system, "depends_on": [], "definition_of_done": ["要件を満たす実装がある"], "verification": ["対応する自動テストを実行する"]})
    return {"version": "1.0", "release": "MVP", "tasks": tasks}

class TaskPlanGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.trace = yaml.safe_load(TRACE_PATH.read_text(encoding="utf-8"))

    def test_complete_plan_passes(self):
        self.assertEqual(task_plan_gate.validate(complete_plan(self.trace), self.trace), [])

    def test_missing_requirement_task_is_detected(self):
        plan = complete_plan(self.trace); plan["tasks"] = plan["tasks"][1:]
        self.assertTrue(any("requirements がタスクから孤立" in error for error in task_plan_gate.validate(plan, self.trace)))

    def test_cyclic_dependencies_are_detected(self):
        plan = complete_plan(self.trace); plan["tasks"][0]["depends_on"] = ["TASK-002"]; plan["tasks"][1]["depends_on"] = ["TASK-001"]
        self.assertTrue(any("依存関係が循環" in error for error in task_plan_gate.validate(plan, self.trace)))

    def test_plan_without_new_fields_still_passes(self):
        """progress/duration/start_dateを持たない既存形式のプランは後方互換で通過する。"""
        plan = complete_plan(self.trace)
        self.assertEqual(task_plan_gate.validate(plan, self.trace), [])

    def test_invalid_progress_value_is_detected(self):
        plan = complete_plan(self.trace); plan["tasks"][0]["progress"] = "started"
        self.assertTrue(any("progress は todo/doing/done" in error for error in task_plan_gate.validate(plan, self.trace)))

    def test_valid_progress_value_passes(self):
        plan = complete_plan(self.trace); plan["tasks"][0]["progress"] = "doing"
        self.assertEqual(task_plan_gate.validate(plan, self.trace), [])

    def test_progress_on_non_in_scope_task_is_error(self):
        plan = complete_plan(self.trace)
        plan["tasks"][0]["status"] = "deferred"; plan["tasks"][0]["reason"] = "後回し"; plan["tasks"][0]["progress"] = "todo"
        self.assertTrue(any("progress は付けられません" in error for error in task_plan_gate.validate(plan, self.trace)))

    def test_dependency_progress_inversion_is_detected(self):
        plan = complete_plan(self.trace)
        plan["tasks"][0]["depends_on"] = [plan["tasks"][1]["id"]]
        plan["tasks"][0]["progress"] = "done"
        plan["tasks"][1]["progress"] = "todo"
        self.assertTrue(any("done でないのに done にはできません" in error for error in task_plan_gate.validate(plan, self.trace)))

    def test_dependency_both_done_passes(self):
        plan = complete_plan(self.trace)
        plan["tasks"][0]["depends_on"] = [plan["tasks"][1]["id"]]
        plan["tasks"][0]["progress"] = "done"
        plan["tasks"][1]["progress"] = "done"
        self.assertEqual(task_plan_gate.validate(plan, self.trace), [])

    def test_invalid_duration_format_is_detected(self):
        plan = complete_plan(self.trace); plan["tasks"][0]["duration"] = "3days"
        self.assertTrue(any("duration は数字+h/d/w" in error for error in task_plan_gate.validate(plan, self.trace)))

    def test_valid_duration_format_passes(self):
        plan = complete_plan(self.trace); plan["tasks"][0]["duration"] = "3.5d"
        self.assertEqual(task_plan_gate.validate(plan, self.trace), [])

    def test_unquoted_start_date_is_rejected(self):
        """YAMLの裸日付リテラルはdatetime.date型になるため、クォート必須で弾く。"""
        import datetime
        plan = complete_plan(self.trace); plan["tasks"][0]["start_date"] = datetime.date(2026, 8, 1)
        self.assertTrue(any("クォート付きで指定" in error for error in task_plan_gate.validate(plan, self.trace)))

    def test_malformed_start_date_is_detected(self):
        plan = complete_plan(self.trace); plan["tasks"][0]["start_date"] = "2026/08/01"
        self.assertTrue(any("YYYY-MM-DD形式の実在する日付" in error for error in task_plan_gate.validate(plan, self.trace)))

    def test_nonexistent_start_date_is_detected(self):
        plan = complete_plan(self.trace); plan["tasks"][0]["start_date"] = "2026-13-40"
        self.assertTrue(any("YYYY-MM-DD形式の実在する日付" in error for error in task_plan_gate.validate(plan, self.trace)))

    def test_valid_start_date_passes(self):
        plan = complete_plan(self.trace); plan["tasks"][0]["start_date"] = "2026-08-01"
        self.assertEqual(task_plan_gate.validate(plan, self.trace), [])
