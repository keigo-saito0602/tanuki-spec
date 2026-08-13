from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evaluation"))
import render_traceability_docs


def user_stories() -> dict[str, dict]:
    return {"US-001": {"id": "US-001", "status": "in_scope", "statement": "利用者は予約したい。なぜなら講座を受けたいから。"}}


def requirements() -> dict[str, dict]:
    return {
        "FR-001": {
            "id": "FR-001", "status": "in_scope", "type": "functional",
            "statement": "利用者は予約を確定できる", "user_story_ids": ["US-001"], "flow_step_ids": ["BF-001-S01"],
        }
    }


def business_flows() -> list[dict]:
    return [
        {
            "id": "BF-001", "status": "in_scope", "name": "予約フロー",
            "steps": [{"id": "BF-001-S01", "action": "予約画面を開く", "user_story_ids": ["US-001"]}],
        }
    ]


def system_tests() -> list[dict]:
    return [
        {
            "id": "ST-001", "status": "in_scope", "test_type": "functional",
            "requirement_ids": ["FR-001"], "acceptance_test_ids": ["AC-001"],
            "preconditions": ["APIが起動している"], "steps": ["POST /reservations"], "expected_results": ["200が返る"],
        }
    ]


class RenderTraceabilityDocsTest(unittest.TestCase):
    def test_render_requirements_includes_user_story_and_flow_and_requirement(self):
        rendered = render_traceability_docs.render_requirements(user_stories(), requirements(), business_flows())
        self.assertIn("US-001", rendered)
        self.assertIn("BF-001-S01", rendered)
        self.assertIn("FR-001", rendered)

    def test_render_system_includes_system_test(self):
        rendered = render_traceability_docs.render_system(system_tests())
        self.assertIn("ST-001", rendered)
        self.assertIn("AC-001", rendered)


if __name__ == "__main__":
    unittest.main()
