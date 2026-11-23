#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify_stress.py — check the 10k-agent LUMI stress result straight from the JSON.

Usage: python3 benchmarks/lumi_10k/verify_stress.py
Prints agents/ok/err/retries/rps per run and exits non-zero if any run has errors.
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    rows, bad = [], 0
    for f in sorted(glob.glob(os.path.join(HERE, "results", "stress_v5_*.json"))):
        d = json.load(open(f))[0]
        rows.append((os.path.basename(f), d.get("agents"), d.get("ok"), d.get("err"),
                     d.get("retried_requests"), d.get("rps")))
        if d.get("err") or (d.get("agents") != d.get("ok")):
            bad += 1
    print(f"{'file':28} {'agents':>7} {'ok':>7} {'err':>4} {'retried':>8} {'rps':>7}")
    for r in rows:
        print(f"{r[0]:28} {r[1]:>7} {r[2]:>7} {r[3]:>4} {r[4]:>8} {r[5]:>7}")
    print("\nGOOD" if not bad else "\nBAD: %d run(s) with errors" % bad)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
