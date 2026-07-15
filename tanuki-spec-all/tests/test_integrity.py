from __future__ import annotations

import sys
from pathlib import Path
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evaluation"))
import generate_templates
import traceability_gate


class IntegrityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = yaml.safe_load((ROOT / "spec-items.yaml").read_text(encoding="utf-8"))

    def test_item_ids_are_unique_and_conditionals_have_conditions(self):
        ids = []
        for phase in self.data["phases"].values():
            for category in phase["categories"]:
                for item in category["items"]:
                    ids.append(item["id"])
                    self.assertTrue(item["source"])
                    if item["required"] == "conditional":
                        self.assertTrue(item.get("condition"))
        self.assertEqual(len(ids), len(set(ids)))

    def test_committed_templates_match_ssot(self):
        for phase, filename in generate_templates.PHASE_FILES.items():
            expected = generate_templates.render_phase(phase, self.data)
            actual = (ROOT / "templates" / filename).read_text(encoding="utf-8")
            self.assertEqual(actual, expected)

    def test_traceability_template_requires_real_content(self):
        template = yaml.safe_load((ROOT / "templates" / "traceability-template.yaml").read_text(encoding="utf-8"))
        failures = traceability_gate.validate(template)
        self.assertTrue(any("statement が必要です" in failure for failure in failures))

    def test_template_catalog_contains_backlog_and_traceability_sources(self):
        for filename in ("README.md", "product-backlog-template.md", "traceability-template.yaml"):
            self.assertTrue((ROOT / "templates" / filename).is_file())
