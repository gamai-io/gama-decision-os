#!/bin/bash
#SBATCH --job-name=stress10k_v4s
#SBATCH --account=project_XXXXX
#SBATCH --partition=standard-g
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=56
#SBATCH --gres=gpu:mi250:4
#SBATCH --time=01:00:00
#SBATCH --output=/project/project_XXXXX/gama/stress_2026-11-15/stress_v4s_%j.out
set -uo pipefail
BASE=/project/project_XXXXX/gama/stress_2026-11-15
MODEL=/scratch/project_XXXXX/models/qwen25-7b
export BASE MODEL
mkdir -p "$BASE"
module purge
module load Local-LAIF lumi-aif-singularity-bindings
SIF=/appl/local/laifs/containers/lumi-multitorch-latest.sif
export VLLM_CACHE_ROOT=/scratch/project_XXXXX/vllm_cache
export TRITON_CACHE_DIR=/scratch/project_XXXXX/vllm_cache/triton
export TORCHINDUCTOR_CACHE_DIR=/scratch/project_XXXXX/vllm_cache/torchinductor
export HF_HOME=/scratch/project_XXXXX/hf_home
mkdir -p "$VLLM_CACHE_ROOT"
echo "=== V4 START $(date) node=$(hostname) ==="
srun -n1 --gres=gpu:mi250:4 --cpus-per-task=48 singularity exec -B /scratch:/scratch -B /project:/project "$SIF" \
  bash "$BASE/run_two_servers_4gpu.sh" > "$BASE/servers4_$SLURM_JOB_ID.out" 2>&1 &
PS=$!
for i in $(seq 1 300); do
  A=$(curl -sf http://127.0.0.1:8010/v1/models >/dev/null && echo y || echo n)
  B=$(curl -sf http://127.0.0.1:8011/v1/models >/dev/null && echo y || echo n)
  [ "$A" = y ] && [ "$B" = y ] && break
  sleep 2
done
if ! curl -sf http://127.0.0.1:8010/v1/models >/dev/null || ! curl -sf http://127.0.0.1:8011/v1/models >/dev/null; then
  echo VLLM_FAIL
  tail -40 "$BASE/vllm_a4_$SLURM_JOB_ID.log" 2>/dev/null
  tail -40 "$BASE/vllm_b4_$SLURM_JOB_ID.log" 2>/dev/null
  kill "$PS" 2>/dev/null
  exit 2
fi
echo "VLLM_READY $(date -u)"
for A in 1000 5000 10000; do
  echo "=== AGENTS $A ==="
  srun --overlap --jobid="$SLURM_JOB_ID" -n1 --cpus-per-task=8 singularity exec -B /scratch:/scratch -B /project:/project "$SIF" \
    python "$BASE/stress_load_v2.py" --url http://127.0.0.1:8010 --url http://127.0.0.1:8011 \
    --agents "$A" --rounds 1 --retries 2 --timeout 300 --model qwen \
    --json-out "$BASE/stress_v4s_${A}.json" 2>&1 | tee "$BASE/stress_v4s_${A}.log"
done
kill "$PS" 2>/dev/null || true
wait "$PS" 2>/dev/null || true
echo "=== V4 DONE $(date -u) ==="
ls -lh "$BASE"/stress_v4_*.json 2>/dev/null
