#!/usr/bin/env bash
set -euo pipefail

N_SESSIONS=${1:-50}
STEPS_PER_SESSION=${2:-100}
OUTDIR=${3:-outputs_smoke}

python make_demo_items.py --output data/items.csv --n-items 3729 --n-styles 19 --seed 42
python run_pipeline.py \
  --items data/items.csv \
  --generate-mock-features \
  --n-sessions "$N_SESSIONS" \
  --steps-per-session "$STEPS_PER_SESSION" \
  --output-dir "$OUTDIR" \
  --skip-cosine-sim-save

echo "\nDone. Key outputs in $OUTDIR:"
ls "$OUTDIR" | sed 's/^/- /'
