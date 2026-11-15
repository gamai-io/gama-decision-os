# LUMI-G — 10,000 concurrent async agents, 0 errors

**Date:** 2026-11-15  
**Hardware:** LUMI-G, 1 node, **4× AMD MI250X** (gfx90a)  
**Model:** Qwen2.5-7B, **2× vLLM replicas** (TP2 each), `max-model-len 4096`, `max-num-seqs 512` per replica, prefix caching  
**Client:** 10,000 async aiohttp requests (not 10,000 processes), timeout 300 s, 2 retries — **0 retries used**

## Results

| agents | ok | err | retried | wall | req/s | p50 | p95 | p99 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1,000 | 1,000 | **0** | 0 | 17.5 s | **57.15** | 6.4 s | 14.8 s | 16.9 s |
| 5,000 | 5,000 | **0** | 0 | 71.8 s | **69.68** | 27.1 s | 62.7 s | 68.0 s |
| 10,000 | **10,000** | **0** | 0 | 187.1 s | **53.45** | 52.0 s | 124.6 s | 135.6 s |

**10k: 100% success, 0 errors, 0 retries.** 5k is the throughput peak; 10k is a concurrency envelope.

## Interpretation

- Two TP2 replicas give enough capacity for 10k concurrent requests on 4 GCDs.
- 1k–5k are interactive (p95 14.8–62.7 s); 10k is not a production SLA (p95 124.6 s), but it is a valid stress envelope.
- The bottleneck at 10k is queueing, not failures; `max-num-seqs` and replica count are the main levers.

## Limitations

- Short synthetic prompts (6 templates); this is not a quality benchmark.
- One run per level; not a statistical sample.
- 10k = 10k async clients, not 10k processes.
- False-success/quality detection is outside this result.

## Reproduce

See [`benchmarks/lumi_10k`](../benchmarks/lumi_10k/): `stress_load_v2.py`, `stress_10k_v4s.sbatch`, `run_two_servers_4gpu.sh`.

The scripts use a `project_XXXXX` placeholder; set your LUMI project and model path.
