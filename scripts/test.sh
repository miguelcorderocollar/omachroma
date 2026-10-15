#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONDONTWRITEBYTECODE=1
python3 -m unittest discover -s "$ROOT/tests" -p 'test_*.py'
node "$ROOT/tests/test_batch_plan.mjs"
node "$ROOT/tests/test_prices.mjs"
