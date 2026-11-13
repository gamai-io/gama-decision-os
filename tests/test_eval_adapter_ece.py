# -*- coding: utf-8 -*-
"""Testovi za eval_adapter_ece.py (dry-run, metrike, JSON, confidence)."""
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gama_decision import eval_adapter_ece as E

CATEGORIES = [
    "status_flip",
    "sql_wrong_table",
    "sql_wrong_column",
    "path_lookalike",
    "numeric_hallucination",
    "false_success_ack",
]


def _write_dataset(path, n=12):
    with open(path, "w", encoding="utf-8") as handle:
        for idx in range(n):
            category = CATEGORIES[idx % len(CATEGORIES)]
            pair = {
                "prompt": f"prompt {idx}",
                "chosen": f"chosen {idx}",
                "rejected": f"rejected {idx}",
                "synthetic": category != "status_flip",
                "metadata": {
                    "category": category,
                    "tool": "sql" if "sql" in category else "run",
                    "bucket": "trivial" if category == "status_flip" else "near_miss",
                },
            }
            handle.write(json.dumps(pair, ensure_ascii=False) + "\n")


class EvalAdapterECETest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = self._tmp.name
        self.dataset = os.path.join(self.tmp, "dpo.jsonl")
        self.output = os.path.join(self.tmp, "eval.json")
        _write_dataset(self.dataset)

    def tearDown(self):
        self._tmp.cleanup()

    def test_dry_run_metrics_are_valid_and_json_is_written(self):
        result = E.evaluate(
            dry_run=True,
            dataset=self.dataset,
            output=self.output,
            bins=10,
            seed=3,
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["mode"], "dry-run")
        metrics = result["metrics"]
        self.assertEqual(metrics["n_predictions"], 24)
        self.assertGreaterEqual(metrics["ece"], 0.0)
        self.assertLessEqual(metrics["ece"], 1.0)
        self.assertGreaterEqual(metrics["brier"], 0.0)
        self.assertLessEqual(metrics["brier"], 1.0)
        self.assertGreaterEqual(metrics["accuracy"], 0.0)
        self.assertLessEqual(metrics["accuracy"], 1.0)

        bin_sizes = sum(item["size"] for item in metrics["bin_details"].values())
        self.assertEqual(bin_sizes, metrics["n_predictions"])

        self.assertTrue(os.path.exists(self.output))
        with open(self.output, encoding="utf-8") as handle:
            saved = json.load(handle)
        self.assertEqual(saved["mode"], "dry-run")
        self.assertEqual(saved["metrics"]["n_predictions"], 24)
        self.assertIn("Reliability Diagram", saved["diagram"])
        self.assertIn("Legend", saved["diagram"])

    def test_dry_run_is_deterministic(self):
        first = E.evaluate(dry_run=True, dataset=self.dataset, output=None, seed=11)
        second = E.evaluate(dry_run=True, dataset=self.dataset, output=None, seed=11)
        self.assertEqual(first["metrics"], second["metrics"])

    def test_dry_run_without_dataset_uses_fallback(self):
        result = E.evaluate(
            dry_run=True,
            dataset=os.path.join(self.tmp, "missing.jsonl"),
            output=None,
        )
        self.assertTrue(result["ok"])
        self.assertIsNone(result["dataset"])
        self.assertGreater(result["metrics"]["n_predictions"], 0)

    def test_pair_logprobs_to_confidence_properties(self):
        p_chosen, p_rejected = E.pair_logprobs_to_confidence(-1.0, -2.0)
        self.assertAlmostEqual(p_chosen + p_rejected, 1.0)
        self.assertGreater(p_chosen, p_rejected)
        self.assertGreater(p_chosen, 0.5)

        p_chosen, p_rejected = E.pair_logprobs_to_confidence(-2.0, -1.0)
        self.assertLess(p_chosen, 0.5)
        self.assertGreater(p_rejected, 0.5)

        p_chosen, p_rejected = E.pair_logprobs_to_confidence(
            float("-inf"), float("-inf")
        )
        self.assertEqual((p_chosen, p_rejected), (0.5, 0.5))
        self.assertEqual(
            E.pair_logprobs_to_confidence(float("-inf"), -1.0), (0.0, 1.0)
        )
        self.assertEqual(
            E.pair_logprobs_to_confidence(-1.0, float("-inf")), (1.0, 0.0)
        )

    def test_real_mode_without_model_returns_clear_error(self):
        result = E.evaluate(
            dry_run=False,
            dataset=self.dataset,
            output=None,
            base_model="/nonexistent/gama-base",
            adapter=None,
        )
        self.assertFalse(result["ok"])
        self.assertIn("error", result)

    def test_cli_dry_run_returns_zero_and_writes_json(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = E.main(
                [
                    "--dry-run",
                    "--dataset",
                    self.dataset,
                    "--output",
                    self.output,
                    "--bins",
                    "5",
                    "--limit",
                    "6",
                ]
            )
        self.assertEqual(code, 0)
        self.assertIn("ECE:", buffer.getvalue())
        with open(self.output, encoding="utf-8") as handle:
            saved = json.load(handle)
        self.assertEqual(saved["metrics"]["bins"], 5)
        self.assertEqual(saved["metrics"]["n_predictions"], 12)


if __name__ == "__main__":
    unittest.main()
