#!/bin/bash
set -uo pipefail
BASE=${BASE:-/project/project_XXXXX/gama/stress_2026-11-15}
MODEL=${MODEL:-/scratch/project_XXXXX/models/qwen25-7b}
export BASE MODEL
bash "$BASE/run_two_servers_4gpu.sh" &
SPID=$!
for i in $(seq 1 300); do
  A=$(curl -sf http://127.0.0.1:8010/v1/models >/dev/null && echo y || echo n)
  B=$(curl -sf http://127.0.0.1:8011/v1/models >/dev/null && echo y || echo n)
  [ "$A" = y ] && [ "$B" = y ] && break
  sleep 2
done
if ! curl -sf http://127.0.0.1:8010/v1/models >/dev/null || ! curl -sf http://127.0.0.1:8011/v1/models >/dev/null; then
  echo VLLM_FAIL
  pkill -f 'vllm.entrypoints' 2>/dev/null || true
  wait "$SPID" 2>/dev/null || true
  exit 2
fi
echo "VLLM_READY $(date -u)"
for A in 1000 5000 10000; do
  echo "=== AGENTS $A ==="
  python "$BASE/stress_load_v2.py" --url http://127.0.0.1:8010 --url http://127.0.0.1:8011 \
    --agents "$A" --rounds 1 --retries 2 --timeout 300 --model qwen \
    --json-out "$BASE/stress_v5_${A}.json" 2>&1 | tee "$BASE/stress_v5_${A}.log"
done
pkill -f 'vllm.entrypoints' 2>/dev/null || true
wait "$SPID" 2>/dev/null || true
echo "=== V5 DONE $(date -u) ==="
ls -lh "$BASE"/stress_v5_*.json 2>/dev/null
exit 0
