#!/bin/bash
set -uo pipefail
BASE=${BASE:-/project/project_XXXXX/gama/stress_2026-11-15}
MODEL=${MODEL:-/scratch/project_XXXXX/models/qwen25-7b}
J=${SLURM_JOB_ID:-0}
ROCR_VISIBLE_DEVICES=0,1 python -m vllm.entrypoints.openai.api_server \
  --model "$MODEL" --served-model-name qwen --host 127.0.0.1 --port 8010 \
  --tensor-parallel-size 2 --max-model-len 4096 --gpu-memory-utilization 0.85 \
  --max-num-seqs 512 --enable-prefix-caching > "$BASE/vllm_a4_$J.log" 2>&1 &
A=$!
ROCR_VISIBLE_DEVICES=2,3 python -m vllm.entrypoints.openai.api_server \
  --model "$MODEL" --served-model-name qwen --host 127.0.0.1 --port 8011 \
  --tensor-parallel-size 2 --max-model-len 4096 --gpu-memory-utilization 0.85 \
  --max-num-seqs 512 --enable-prefix-caching > "$BASE/vllm_b4_$J.log" 2>&1 &
B=$!
wait $A $B
