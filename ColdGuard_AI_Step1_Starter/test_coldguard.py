"""Automated smoke tests for the ColdGuard AI Step 4 workflow."""
import os
import unittest
import pandas as pd
from coldguard_agents import run_agent_workflow
from coldguard_validation import validate_and_prepare, validate_workflow_output

ROOT = os.path.dirname(__file__)

class ColdGuardValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = pd.read_csv(os.path.join(ROOT, "product_rules.csv"))
        cls.sample = pd.read_csv(os.path.join(ROOT, "sample_temperature_logs.csv"))

    def test_sample_dataset_has_six_shipments(self):
        prepared, messages = validate_and_prepare(self.sample)
        self.assertEqual(prepared["shipment_id"].nunique(), 6)
        self.assertEqual(len(prepared), 23)

    def test_missing_column_is_reported(self):
        broken = self.sample.drop(columns=["temperature"])
        prepared, messages = validate_and_prepare(broken)
        self.assertTrue(prepared.empty)
        self.assertTrue(any("Missing required column" in m for m in messages))

    def test_invalid_temperature_is_reported_and_row_excluded(self):
        broken = self.sample.copy()
        broken.loc[0, "temperature"] = "not-a-number"
        prepared, messages = validate_and_prepare(broken)
        self.assertEqual(len(prepared), len(self.sample) - 1)
        self.assertTrue(any("invalid temperatures" in m for m in messages))

    def test_duplicate_timestamp_is_flagged(self):
        broken = pd.concat([self.sample, self.sample.iloc[[0]]], ignore_index=True)
        prepared, messages = validate_and_prepare(broken)
        self.assertTrue(any("duplicate shipment/timestamp" in m for m in messages))

    def test_workflow_has_all_five_agents(self):
        workflow = run_agent_workflow(self.sample, "Vaccine A", self.rules)
        for key in ["plan", "executor", "decision", "critic", "report"]:
            self.assertIn(key, workflow)
        self.assertEqual(len(workflow["critic"]["results"]), 6)

    def test_workflow_output_structure(self):
        workflow = run_agent_workflow(self.sample, "Vaccine A", self.rules)
        issues = validate_workflow_output(workflow)
        self.assertEqual(issues, [])

if __name__ == "__main__":
    unittest.main(verbosity=2)
