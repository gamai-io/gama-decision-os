# -*- coding: utf-8 -*-
"""
test_temperature_scaling.py — testovi za Temperature Scaling kalibraciju.

Pokriva:
  1. fit T* na sintetickim preuvjerenim podacima (NLL opada, T* > 0),
  2. ECE pada nakon skaliranja,
  3. rangiranje (poredak vjerovatnoca i odluka na pragu 0.5) ostaje nepromijenjeno,
  4. calibration.json payload sadrzi obavezna polja.
"""
import json
import math
import os
import random
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gama_decision.calibration_evaluator import calculate_ece
from gama_decision.eval_adapter_ece import (
    _reconstruct_from_eval_json,
    _write_calibration,
    apply_temperature,
    fit_calibration,
    fit_temperature_scaling,
)


def _sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-value))


def _overconfident_dataset(n: int = 2000, seed: int = 11):
    """Generise kalibrisane logite, pa ih umjetno izostri (preuvjeren model)."""
    rng = random.Random(seed)
    probs, labels = [], []
    for _ in range(n):
        true_logit = rng.gauss(0.0, 1.2)
        p_true = _sigmoid(true_logit)
        label = 1 if rng.random() < p_true else 0
        over_logit = true_logit * 3.2
        probs.append(_sigmoid(over_logit))
        labels.append(label)
    return probs, labels


class TemperatureScalingTest(unittest.TestCase):
    def test_fit_returns_positive_temperature(self):
        probs, labels = _overconfident_dataset()
        temperature, info = fit_temperature_scaling(probs, labels)
        self.assertGreater(temperature, 0.0)
        self.assertIn(info["method"], ("scipy.bounded", "grid"))

    def test_ece_drops_after_scaling(self):
        probs, labels = _overconfident_dataset()
        ece_before, _ = calculate_ece(probs, labels, 10)
        temperature, _ = fit_temperature_scaling(probs, labels)
        scaled = [apply_temperature(p, temperature) for p in probs]
        ece_after, _ = calculate_ece(scaled, labels, 10)
        self.assertLess(ece_after, ece_before)
        self.assertLess(ece_after, 0.05)

    def test_ranking_unchanged(self):
        probs, _labels = _overconfident_dataset()
        temperature = 1.7
        scaled = [apply_temperature(p, temperature) for p in probs]
        order_before = sorted(range(len(probs)), key=lambda i: probs[i])
        order_after = sorted(range(len(scaled)), key=lambda i: scaled[i])
        self.assertEqual(order_before, order_after)
        for before, after in zip(probs, scaled, strict=True):
            self.assertEqual(before >= 0.5, after >= 0.5)

    def test_fit_calibration_payload(self):
        probs, labels = _overconfident_dataset(n=1000)
        payload = fit_calibration(probs, labels, seed=7)
        for key in (
            "temperature",
            "ece_before",
            "ece_after",
            "brier_before",
            "brier_after",
            "n_calib",
            "n_test",
            "fit_ts",
        ):
            self.assertIn(key, payload)
        self.assertEqual(payload["n_calib"] + payload["n_test"], len(probs))
        self.assertLess(payload["ece_after"], payload["ece_before"])
        self.assertTrue(payload["ranking_unchanged"])

    def test_calibration_json_written(self):
        probs, labels = _overconfident_dataset(n=500)
        payload = fit_calibration(probs, labels, seed=3)
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_calibration(tmp, payload)
            self.assertTrue(os.path.exists(path))
            with open(path, encoding="utf-8") as handle:
                loaded = json.load(handle)
            self.assertEqual(loaded["temperature"], payload["temperature"])

    def test_reconstruct_from_bin_details(self):
        payload = {
            "metrics": {
                "bin_details": {
                    "0": {"size": 10, "conf": 0.05, "acc": 0.0, "error": 0.05},
                    "9": {"size": 10, "conf": 0.95, "acc": 1.0, "error": 0.05},
                }
            }
        }
        probs, labels = _reconstruct_from_eval_json(payload)
        self.assertEqual(len(probs), 20)
        self.assertEqual(sum(labels), 10)
        self.assertEqual(sum(1 for p in probs if p < 0.5), 10)


if __name__ == "__main__":
    unittest.main()
