#!/usr/bin/env sh
# Start examples/serve_decision.py first, then run this script.
set -eu

curl -s localhost:8092/decide \
  -H 'content-type: application/json' \
  -d '{"text":"delete /tmp/report.txt"}'
echo

curl -s localhost:8092/decide \
  -H 'content-type: application/json' \
  -d '{"text":"send the invoice to customer ALFA"}'
echo
