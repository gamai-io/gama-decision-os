#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ledger_stats.py — recompute every token-saving figure quoted in the README.

Source of truth: the harness token ledger (SQLite, table `token_ledger`).
Default path: $GAMA_TOKEN_LEDGER or /opt/gama-harness/_token_ledger.db

Usage:
    python3 benchmarks/ledger_stats.py            # 24h / 7d / all
    python3 benchmarks/ledger_stats.py --db /path/to/_token_ledger.db --json

Definitions used in the README:
    saving_pct  = saved_tokens / (prompt_tokens + saved_tokens) * 100
    shortcircuit_pct = shortcircuit rows / all rows * 100
    cache_hit_pct    = cache_hit rows / all rows * 100
"""
import argparse
import json
import os
import sqlite3
import time

DEFAULT_DB = os.environ.get("GAMA_TOKEN_LEDGER", "/opt/gama-harness/_token_ledger.db")
WINDOWS = (("24h", 86400), ("7d", 7 * 86400), ("all", 0))


def stats(db, seconds):
    lo = time.time() - seconds if seconds else 0
    con = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    row = con.execute(
        "SELECT COUNT(*), COALESCE(SUM(prompt_tokens),0), COALESCE(SUM(completion_tokens),0),"
        " COALESCE(SUM(saved_tokens),0),"
        " COALESCE(SUM(CASE WHEN shortcircuit=1 THEN 1 ELSE 0 END),0),"
        " COALESCE(SUM(CASE WHEN cache_hit=1 THEN 1 ELSE 0 END),0)"
        " FROM token_ledger WHERE ts>=?", (lo,)).fetchone()
    con.close()
    n, prompt, compl, saved, sc, ch = row
    if not n:
        return {"n": 0}
    base = prompt + saved
    return {
        "n": n,
        "prompt_tokens": prompt,
        "completion_tokens": compl,
        "saved_tokens": saved,
        "saving_pct": round(100.0 * saved / base, 2) if base else 0.0,
        "shortcircuit_pct": round(100.0 * sc / n, 1),
        "cache_hit_pct": round(100.0 * ch / n, 1),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DEFAULT_DB)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if not os.path.exists(a.db):
        raise SystemExit("ledger not found: %s (set GAMA_TOKEN_LEDGER)" % a.db)
    out = {label: stats(a.db, sec) for label, sec in WINDOWS}
    if a.json:
        print(json.dumps(out, indent=1))
        return
    print("ledger:", a.db)
    print(f"{'window':6} {'n':>7} {'prompt':>12} {'saved':>13} {'saving%':>8} {'short%':>7} {'cache%':>7}")
    for label, _ in WINDOWS:
        s = out[label]
        if not s.get("n"):
            print(f"{label:6} {0:>7}")
            continue
        print(f"{label:6} {s['n']:>7} {s['prompt_tokens']:>12,} {s['saved_tokens']:>13,}"
              f" {s['saving_pct']:>8} {s['shortcircuit_pct']:>7} {s['cache_hit_pct']:>7}")


if __name__ == "__main__":
    main()
