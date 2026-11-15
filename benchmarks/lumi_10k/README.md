# LUMI-G 10k async agents — reproduction kit

Clean result: **10,000/10,000, 0 errors, 0 retries** on **4× AMD MI250X** with Qwen2.5-7B and two vLLM TP2 replicas. Full report: [`docs/BENCHMARK_LUMI_10K.md`](../../docs/BENCHMARK_LUMI_10K.md).

## Requirements

- LUMI-G account with a project ID (`project_XXXXX`).
- Qwen2.5-7B weights at `$SCRATCH/models/qwen25-7b`.
- LUMI AI Factory container `lumi-multitorch-latest.sif`.
- Slurm `small-g`/`standard-g`, 4 GPUs, 56 CPUs.

## Run

1. Replace `project_XXXXX` in `stress_10k_v4s.sbatch` and `run_two_servers_4gpu.sh` with your project.
2. Adjust `MODEL`, `BASE`, `VLLM_CACHE_ROOT`, and `HF_HOME` paths.
3. Submit:

```bash
sbatch stress_10k_v4s.sbatch
```

The job starts two vLLM servers (ports 8010/8011) and runs 1k/5k/10k agents with 2 retries and a 300 s timeout. Results go to `stress_v4s_*.json`.

## Expected result

| agents | err | req/s | p95 |
|---:|---:|---:|---:|
| 1,000 | 0 | 57.15 | 14.8 s |
| 5,000 | 0 | 69.68 | 62.7 s |
| 10,000 | 0 | 53.45 | 124.6 s |

Caveats: short synthetic prompts, one run per level, not a production SLA.
