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
