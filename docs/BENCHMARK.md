# Benchmarks and calibration notes

All numbers below were measured while preparing this release (v1.2.2) with the
public core on a single Linux x86-64 host. They are indicative, not a
cross-hardware guarantee. Re-run them on your own hardware.

## Decision engine latency

500 sequential calls per case, after warm-up. Values are **milliseconds**
(mean / p50 / p95).

| Case | Mean | p50 | p95 |
| --- | ---: | ---: | ---: |
| `READ` allow — "provjeri stanje diska" | 0.0659 | 0.0027 | 0.0041 |
| `IRREVERSIBLE` deny — destructive shell precheck | 0.0030 | 0.0025 | 0.0028 |
| `SEND` ask — "pošalji mail kupcu ALFA sa ponudom" | 0.0053 | 0.0036 | 0.0047 |

The first `READ` call includes one-time imports and cache warm-up; the steady
state is a few microseconds. The deterministic rules run before any model or
network call, so they are effectively free.

## Context compression

Repository scan + rank + prompt assembly over this repository, budget 2000
tokens, 50 iterations: **6.67 ms mean, 6.64 ms p50, 7.82 ms p95**. This uses the
dependency-free fallback ranker shipped in the core.

## Calibration (expected calibration error)

Evaluated on 1,200 predictions from the DPO near-miss dataset (10 bins).

| Run | n | ECE | Brier | Accuracy |
| --- | ---: | ---: | ---: | ---: |
| Adapter, real logprobs | 1200 | 0.299211 | 0.094742 | 1.00 |
| Dry-run mode | 1200 | 0.286841 | 0.221786 | 0.75 |

**Caveat.** The adapter run has accuracy 1.0 on this set, which is degenerate
for calibration: the temperature fit is pushed to a boundary. The ECE number is
therefore a lower-bound diagnostic, not a production calibration claim. The
correct next step is to re-fit on a set with real mistakes. This caveat is
intentional and should be kept in any public comparison.

Temperature scaling is covered by `tests/test_temperature_scaling.py`:

- fitting returns `T* > 0` with method `scipy.bounded` or `grid`,
- ECE drops on a synthetic over-confident set (test asserts `< 0.05` after scaling),
- probability ranking and the 0.5 decision threshold are unchanged.

## Test suite

```
python3 -m pytest tests/ -q
27 passed, 1 skipped
```

The skipped test is the optional live speculative classifier; it runs only when
`GAMA_SPECULATIVE_URL` is set. No network access is required for the core suite.

## What is not claimed

- No claim of superiority over other agent frameworks.
- No claim that these latencies hold under concurrent load.
- No claim that the ECE above reflects production traffic.

## Re-measured 2026-11-23 (this repo, x86-64)

`python3 benchmarks/decision_latency.py --n 500` — warm-up first, then 500 calls per case,
and **0 wrong decisions across 1,500 calls** (tier/verdict asserted per case):

| Case | mean (ms) | p50 (ms) | p95 (ms) | wrong |
| --- | ---: | ---: | ---: | ---: |
| `READ` allow | 0.0033 | 0.0026 | 0.0100 | 0 |
| `IRREVERSIBLE` deny | 0.0023 | 0.0017 | 0.0027 | 0 |
| `SEND` ask | 0.0029 | 0.0020 | 0.0067 | 0 |

Numbers differ from the v1.2.2 table above (same order of magnitude); the script is the
source of truth — re-run it on your hardware rather than quoting this table.

## Not reproduced in this repository

`Tier model 40/40`, `Tool paging 97.3%` and `Code Mode -82.3% tokens` were measured
internally but the benchmark scripts are **not shipped here**. Treat them as unconfirmed.
