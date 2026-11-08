#!/bin/bash
# Makes a usable add-on from one of the snapshots saved during training.
#
# Training saves a snapshot every few updates (0000025_adapters.safetensors,
# 0000050_adapters.safetensors, ...). If a middle snapshot had the lowest
# Val loss, run, for example:
#   bash ~/Documents/base-model-lab/pick_checkpoint.sh 175
# and pick it from the playground's "Trained add-on" menu.
#
# It uses the current run's folder (adapter_path in config.yaml). For an
# earlier run, name its folder too:
#   bash ~/Documents/base-model-lab/pick_checkpoint.sh 100 prose

set -euo pipefail
cd "$(dirname "$0")"

STEP="${1:-}"
if ! [[ "$STEP" =~ ^[0-9]+$ ]]; then
  echo "Give the update number of the snapshot you want, for example:  bash pick_checkpoint.sh 175"
  exit 1
fi

if [ -n "${2:-}" ]; then
  SRC="adapters/${2#adapters/}"
else
  SRC="$(sed -n 's/^adapter_path:[[:space:]]*\([^[:space:]#]*\).*/\1/p' config.yaml)"
  SRC="${SRC:-adapters/prose}"
fi
SRC="${SRC%/}"
if [ ! -d "$SRC" ]; then
  echo "There's no add-on folder at $SRC."
  exit 1
fi
SNAPSHOT="$SRC/$(printf '%07d' "$STEP")_adapters.safetensors"
if [ ! -f "$SNAPSHOT" ]; then
  echo "There's no snapshot for update $STEP. Snapshots available:"
  ls "$SRC" | grep '_adapters.safetensors' | sed 's/_adapters.safetensors//; s/^0*/  /'
  exit 1
fi

DEST="$SRC-step$STEP"
mkdir -p "$DEST"
cp "$SRC/adapter_config.json" "$DEST/"
cp "$SNAPSHOT" "$DEST/adapters.safetensors"
bash list_adapters.sh > /dev/null
echo "Ready. In the playground, pick $(basename "$DEST") from the Trained add-on menu"
echo "(switch back to its tab first so it sees the new add-on). Its folder is:"
echo "  $(pwd)/$DEST"
