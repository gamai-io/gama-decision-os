#!/bin/bash
#SBATCH --job-name=stress10k_v5
#SBATCH --account=project_XXXXX
#SBATCH --partition=standard-g
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=56
#SBATCH --gres=gpu:mi250:4
#SBATCH --time=01:00:00
#SBATCH --output=/project/project_XXXXX/gama/stress_2026-11-15/stress_v5_%j.out
set -uo pipefail
BASE=/project/project_XXXXX/gama/stress_2026-11-15
export BASE
export MODEL=/scratch/project_XXXXX/models/qwen25-7b
export VLLM_CACHE_ROOT=/scratch/project_XXXXX/vllm_cache
export TRITON_CACHE_DIR=/scratch/project_XXXXX/vllm_cache/triton
export TORCHINDUCTOR_CACHE_DIR=/scratch/project_XXXXX/vllm_cache/torchinductor
export HF_HOME=/scratch/project_XXXXX/hf_home
mkdir -p "$BASE" "$VLLM_CACHE_ROOT"
module purge
module load Local-LAIF lumi-aif-singularity-bindings
SIF=/appl/local/laifs/containers/lumi-multitorch-latest.sif
echo "=== V5 START $(date) node=$(hostname) ==="
srun -n1 --gres=gpu:mi250:4 --cpus-per-task=52 singularity exec -B /scratch:/scratch -B /project:/project "$SIF" \
  bash "$BASE/run_stress_v5.sh"
echo "=== V5 JOB DONE $(date) ==="
