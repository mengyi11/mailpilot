from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

EVAL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EVAL_ROOT))

from fixture_predictor import predict
from metrics import classification_macro_f1, evaluate, text_match


class MetricsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = [json.loads(line) for line in (EVAL_ROOT / "benchmark.jsonl").read_text().splitlines() if line]

    def test_gold_dataset_has_twenty_unique_cases_and_required_coverage(self):
        self.assertEqual(len(self.cases), 20)
        self.assertEqual(len({case["case_id"] for case in self.cases}), 20)
        tags = {tag for case in self.cases for tag in case["tags"]}
        for required in {"meeting", "task", "chinese", "english", "ambiguous-date", "newsletter", "prompt-injection"}:
            self.assertIn(required, tags)

    def test_macro_f1_is_one_for_perfect_predictions(self):
        rows = [(case["gold"]["category"], case["gold"]["category"]) for case in self.cases]
        self.assertEqual(classification_macro_f1(rows), 1.0)

    def test_gold_evidence_is_present_in_the_email(self):
        for case in self.cases:
            corpus = f"{case['input']['subject']}\n{case['input']['body']}".casefold()
            for item in case["gold"]["actions"] + case["gold"]["dates"]:
                self.assertIn(item["evidence"].casefold(), corpus, case["case_id"])

    def test_text_matching_handles_case_and_punctuation(self):
        self.assertTrue(text_match("Submit revised proposal", "submit: revised proposal"))

    def test_v2_fixture_is_safer_than_v1(self):
        v1 = evaluate(self.cases, [predict(case, "v1") for case in self.cases])
        v2 = evaluate(self.cases, [predict(case, "v2") for case in self.cases])
        self.assertGreater(v2["classification_macro_f1"], v1["classification_macro_f1"])
        self.assertLess(v2["unsafe_action_rate"], v1["unsafe_action_rate"])
        self.assertGreater(v2["tool_selection_accuracy"], v1["tool_selection_accuracy"])


if __name__ == "__main__":
    unittest.main()
