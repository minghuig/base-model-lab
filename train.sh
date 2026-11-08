#!/bin/bash
# Trains the "excellent prose" add-on for Llama 3.1 8B base.
#
# Run it in Terminal with:
#   bash ~/Documents/base-model-lab/train.sh
#
# Everything it makes stays in this folder: the add-on goes in adapters/prose,
# and a copy of the output goes in train-log.txt.

set -euo pipefail
cd "$(dirname "$0")"
export PATH="$HOME/.local/bin:$PATH"

PORT=8080
MODEL="mlx-community/Meta-Llama-3.1-8B-4bit"
ADAPTER_DIR="adapters/prose"

if ! command -v uv >/dev/null 2>&1; then
  echo "mlx-lm isn't installed yet. Run  bash ~/Documents/base-model-lab/start-base-model.sh  once first,"
  echo "then come back and run this again."
  exit 1
fi
TOOL_PY="$(uv tool dir)/mlx-lm/bin/python"
if [ ! -x "$TOOL_PY" ]; then
  echo "mlx-lm isn't installed yet. Run  bash ~/Documents/base-model-lab/start-base-model.sh  once first,"
  echo "then come back and run this again."
  exit 1
fi

if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "The playground server is still running, and training needs the memory it's using."
  echo "Switch to its Terminal window, press Control-C, then run this again."
  exit 1
fi

if [ -d "$ADAPTER_DIR" ] && [ -n "$(ls -A "$ADAPTER_DIR" 2>/dev/null)" ]; then
  echo "There's already a trained add-on in $ADAPTER_DIR."
  read -r -p "Train a new one? The old one will be kept, renamed with today's date and time. [y/N] " answer
  case "$answer" in
    y|Y|yes|Yes) mv "$ADAPTER_DIR" "${ADAPTER_DIR}-$(date +%Y%m%d-%H%M%S)" ;;
    *) echo "Nothing changed."; exit 0 ;;
  esac
fi

echo "Checking the model files…"
if ! uv tool run --from huggingface_hub hf download "$MODEL" > /dev/null; then
  echo "Couldn't download $MODEL. Check your internet connection, then run this again."
  exit 1
fi

cat <<'GUIDE'

Starting training. What to watch:
  - Every 10 updates it prints "Train loss": how surprised the model is by the
    replies it's training on. It should fall quickly at first, then level off.
  - Every 50 updates it prints "Val loss": the same score on the 30 held-out
    conversations it never trains on. This is the honest one.
  - If Val loss starts rising while Train loss keeps falling, the model has
    started memorizing its examples. A snapshot is saved every 50 updates, so
    we can go back to the best one.
The first few updates are slower while things warm up. Your Mac may get warm
and loud; that's normal.

GUIDE

"$TOOL_PY" lab_launcher.py --config config.yaml 2>&1 | tee train-log.txt

cat <<EOF

Done. To try it in the playground:
  1. Start the server:   bash ~/Documents/base-model-lab/start-base-model.sh
  2. In the playground, choose Provider: Server on this Mac
     Model:          mlx-community/Meta-Llama-3.1-8B-4bit
     Trained add-on: $(pwd)/$ADAPTER_DIR
  3. Write a prompt like this, ending with "Assistant:" and no stop string:

     User: what's a fun activity i can do today?

     Assistant:

If Val loss was lowest partway through, use that snapshot instead. For example,
for update 100, run  bash ~/Documents/base-model-lab/pick_checkpoint.sh 100
and use the folder it prints as the Trained add-on.
EOF
