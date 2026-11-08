#!/bin/bash
# Makes a usable add-on from one of the snapshots saved during training.
#
# Training saves a snapshot every 50 updates (0000050_adapters.safetensors,
# 0000100_adapters.safetensors, ...). If a middle snapshot had the lowest
# Val loss, run, for example:
#   bash ~/Documents/base-model-lab/pick_checkpoint.sh 300
# and use the folder it prints as the playground's "Trained add-on".

set -euo pipefail
cd "$(dirname "$0")"

STEP="${1:-}"
if ! [[ "$STEP" =~ ^[0-9]+$ ]]; then
  echo "Give the update number of the snapshot you want, for example:  bash pick_checkpoint.sh 300"
  exit 1
fi

SRC="adapters/prose"
SNAPSHOT="$SRC/$(printf '%07d' "$STEP")_adapters.safetensors"
if [ ! -f "$SNAPSHOT" ]; then
  echo "There's no snapshot for update $STEP. Snapshots available:"
  ls "$SRC" | grep '_adapters.safetensors' | sed 's/_adapters.safetensors//; s/^0*/  /'
  exit 1
fi

DEST="adapters/prose-step$STEP"
mkdir -p "$DEST"
cp "$SRC/adapter_config.json" "$DEST/"
cp "$SNAPSHOT" "$DEST/adapters.safetensors"
echo "Ready. Use this as the playground's Trained add-on:"
echo "  $(pwd)/$DEST"
