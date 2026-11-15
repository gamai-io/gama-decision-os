# LUMI-G 10k async agents — reproduction kit

Clean result: **10,000/10,000, 0 errors, 0 retries** on **4× AMD MI250X** with Qwen2.5-7B and two vLLM TP2 replicas. Full report: [`docs/BENCHMARK_LUMI_10K.md`](../../docs/BENCHMARK_LUMI_10K.md).

## Requirements

- LUMI-G account with a project ID (`project_XXXXX`).
- Qwen2.5-7B weights at `$SCRATCH/models/qwen25-7b`.
- LUMI AI Factory container `lumi-multitorch-latest.sif`.
- Slurm `standard-g`, 4 GPUs, 56 CPUs.

## Run

1. Replace `project_XXXXX` in `stress_10k_v5.sbatch` and `run_stress_v5.sh` with your project.
2. Adjust `BASE`, `MODEL`, `VLLM_CACHE_ROOT`, and `HF_HOME` paths.
3. Submit:

```bash
sbatch stress_10k_v5.sbatch
```

The job starts two vLLM servers (ports 8010/8011) and runs 1k/5k/10k agents with 2 retries and a 300 s timeout. Results go to `stress_v5_*.json`.

## Expected result (clean run)

| agents | err | req/s | p95 |
|---:|---:|---:|---:|
| 1,000 | 0 | 54.59 | 15.8 s |
| 5,000 | 0 | 46.32 | 64.2 s |
| 10,000 | 0 | 58.09 | 123.9 s |

Full verification (job `23765235`, COMPLETED, exit 0:0, hashes) is in the report. Caveats: short synthetic prompts, one run per level, not a production SLA.
