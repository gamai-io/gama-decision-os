# LUMI-G — 10,000 concurrent async agents, 0 errors

**Date:** 2026-11-15  
**Hardware:** LUMI-G, 1 node, **4× AMD MI250X** (gfx90a)  
**Model:** Qwen2.5-7B, **2× vLLM replicas** (TP2 each), `max-model-len 4096`, `max-num-seqs 512` per replica, prefix caching  
**Client:** 10,000 async aiohttp requests (not 10,000 processes), timeout 300 s, 2 retries — **0 retries used**

## Results (clean run)

| agents | ok | err | retried | wall | req/s | p50 | p95 | p99 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1,000 | 1,000 | **0** | 0 | 18.3 s | **54.59** | 6.6 s | 15.8 s | 17.6 s |
| 5,000 | 5,000 | **0** | 0 | 107.9 s | **46.32** | 27.2 s | 64.2 s | 69.7 s |
| 10,000 | **10,000** | **0** | 0 | 172.2 s | **58.09** | 52.0 s | 123.9 s | 134.6 s |

**10k: 100% success, 0 errors, 0 retries.** Throughput 46–58 req/s (one run; run-to-run variance). 10k is a concurrency envelope, not a production SLA.

## Verification

- **LUMI Slurm job `23765235`**, partition `standard-g`, state **COMPLETED**, exit **0:0**, elapsed **7:01**.
- Log excerpt:
  - `V5 START … node=nid005374`
  - `VLLM_READY`
  - `AGENTS 10000`
  - `{"agents": 10000, "ok": 10000, "err": 0, "retried_requests": 0, "wall_s": 172.16, "rps": 58.09, "p50_ms": 52012.5, "p95_ms": 123921.3, "p99_ms": 134573.3}`
  - `V5 DONE`
- Raw JSON: [`benchmarks/lumi_10k/results/stress_v5_10000.json`](../benchmarks/lumi_10k/results/stress_v5_10000.json), sha256 `9c3a1a0ad63cb5167cda65ead3eafe9c575037b8c846c12327e204756a6ff777`.
- Scripts: `stress_load_v2.py` (`asyncio.gather` 10k, 2 retries, timeout 300), `stress_10k_v5.sbatch`, `run_stress_v5.sh`, `run_two_servers_4gpu.sh`.
- The public JSON omits the noisy `false_success` detector field; quality/false-success is **not** part of this benchmark.

## Interpretation

- Two TP2 replicas give enough capacity for 10k concurrent requests on 4 GCDs.
- 1k–5k are interactive (p95 15.8–64.2 s); 10k has p95 123.9 s — valid stress envelope, not an SLA.
- The bottleneck at 10k is queueing, not failures; `max-num-seqs` and replica count are the levers.

## Limitations

- Short synthetic prompts (6 templates); this is not a quality benchmark.
- One run per level; not a statistical sample.
- 10k = 10k async clients, not 10k processes.
- False-success/quality detection is outside this result.

## Reproduce

See [`benchmarks/lumi_10k`](../benchmarks/lumi_10k/): `stress_load_v2.py`, `stress_10k_v5.sbatch`, `run_stress_v5.sh`, `run_two_servers_4gpu.sh`.

The scripts use a `project_XXXXX` placeholder; set your LUMI project and model path.
