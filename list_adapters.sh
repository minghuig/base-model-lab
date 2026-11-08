#!/bin/bash
# Writes adapters/index.js: the list of trained add-ons that the playground's
# "Trained add-on" menu shows, with the model each was trained on.
#
# pick_checkpoint.sh and train.sh run this for you. To run it yourself:
#   bash ~/Documents/base-model-lab/list_adapters.sh

set -euo pipefail
cd "$(dirname "$0")"
ROOT="$(pwd)"
mkdir -p adapters

{
  echo "// Written by list_adapters.sh. The playground reads this to fill its add-on menu."
  echo "window.BMP_ADAPTERS = ["
  for dir in adapters/*/; do
    dir="${dir%/}"
    # A usable add-on folder has the weights under the name the server loads.
    [ -f "$dir/adapters.safetensors" ] && [ -f "$dir/adapter_config.json" ] || continue
    name="$(basename "$dir")"
    model="$(grep -o '"model": *"[^"]*"' "$dir/adapter_config.json" | head -1 | sed 's/.*"\([^"]*\)"$/\1/' || true)"
    printf '  {"name": "%s", "path": "%s", "model": "%s"},\n' "$name" "$ROOT/$dir" "$model"
  done
  echo "];"
} > adapters/index.js

count=$(grep -c '"path"' adapters/index.js || true)
echo "The playground's add-on menu now lists $count add-on(s). Switch back to its tab to see them."
