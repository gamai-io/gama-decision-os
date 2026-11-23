#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""decision_latency.py — reproduce the latency table in docs/BENCHMARK.md.

Measures the deterministic L0 gate (no model, no network) for three canonical
cases, and asserts that the decision itself is the expected one — a fast wrong
answer is not a benchmark.

Usage: python3 benchmarks/decision_latency.py [--n 500]
"""
import argparse
import json
import statistics
import sys
import time

sys.path.insert(0, __file__.rsplit("/benchmarks/", 1)[0])

from gama_decision import decision_l0 as D0  # noqa: E402

CASES = (
    ("READ allow", "provjeri stanje diska", {"tier": "READ", "verdict": "allow"}),
    ("IRREVERSIBLE deny", "rm -rf /", {"tier": "IRREVERSIBLE", "verdict": "deny"}),
    ("SEND ask", "posalji mail kupcu ALFA sa ponudom", {"verdict": "ask"}),
)


def pct(vals, p):
    vals = sorted(vals)
    k = max(0, min(len(vals) - 1, int(round((p / 100.0) * (len(vals) - 1)))))
    return vals[k]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=500)
    a = ap.parse_args()

    # warm-up: first call imports lazily and fills the cache
    for _, text, _ in CASES:
        D0.decide_request(text)

    out = {}
    for name, text, expect in CASES:
        lat, bad = [], 0
        for _ in range(a.n):
            t0 = time.perf_counter()
            r = D0.decide_request(text)
            lat.append((time.perf_counter() - t0) * 1000.0)
            for k, v in expect.items():
                if str(r.get(k, "")).lower() != v.lower():
                    bad += 1
        out[name] = {
            "n": a.n,
            "mean_ms": round(statistics.mean(lat), 4),
            "p50_ms": round(pct(lat, 50), 4),
            "p95_ms": round(pct(lat, 95), 4),
            "wrong_decisions": bad,
        }

    print(json.dumps(out, indent=1))
    return out


if __name__ == "__main__":
    main()
