#!/bin/bash
# Trains the "excellent prose" add-on. config.yaml trains it on Llama 3.1 8B
# base; config-nemo.yaml trains it on Mistral Nemo 12B base.
#
# Run it in Terminal with:
#   bash ~/Documents/base-model-lab/train.sh
# or, for Nemo:
#   bash ~/Documents/base-model-lab/train.sh --config config-nemo.yaml
#
# To train for a different number of epochs (passes over the training data)
# than the config says, add --epochs, for example:
#   bash ~/Documents/base-model-lab/train.sh --epochs 2
#
# Everything it makes stays in this folder: the add-on goes in the folder named
# by adapter_path in the config, and a copy of the output goes in train-log.txt.

set -euo pipefail
cd "$(dirname "$0")"
export PATH="$HOME/.local/bin:$PATH"

usage() {
  echo "Usage: bash train.sh [--config FILE] [--epochs N]"
  echo "  --config FILE  the settings to train with (default config.yaml, which"
  echo "                 trains on Llama; config-nemo.yaml trains on Nemo)"
  echo "  --epochs N     train for N passes over the training data instead of what"
  echo "                 the config says (N can be a fraction, like 0.5)"
}
EPOCHS=""
CONFIG="config.yaml"
while [ $# -gt 0 ]; do
  case "$1" in
    --epochs|--passes)
      if [ $# -lt 2 ]; then usage; exit 1; fi
      EPOCHS="$2"; shift 2 ;;
    --epochs=*|--passes=*) EPOCHS="${1#*=}"; shift ;;
    --config)
      if [ $# -lt 2 ]; then usage; exit 1; fi
      CONFIG="$2"; shift 2 ;;
    --config=*) CONFIG="${1#*=}"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1"; usage; exit 1 ;;
  esac
done
if [ -n "$EPOCHS" ] && ! [[ "$EPOCHS" =~ ^([0-9]+([.][0-9]*)?|[.][0-9]+)$ && "$EPOCHS" =~ [1-9] ]]; then
  echo "--epochs needs a number above zero, like 1, 2 or 0.5 (got: $EPOCHS)"
  exit 1
fi

CONFIG="${CONFIG#./}"
if [ ! -f "$CONFIG" ]; then
  echo "There's no settings file called $CONFIG in this folder."
  exit 1
fi
setting() { sed -n "s/^$1:[[:space:]]*\([^[:space:]#]*\).*/\1/p" "$CONFIG" | head -1; }

PORT=8080
MODEL="$(setting model)"
ADAPTER_DIR="$(setting adapter_path)"
if [ -z "$MODEL" ] || [ -z "$ADAPTER_DIR" ]; then
  echo "$CONFIG needs both a model: line and an adapter_path: line."
  exit 1
fi

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
  - Every 25 updates it prints "Val loss": the same score on the held-out
    conversations it never trains on. This is the honest one.
  - If Val loss starts rising while Train loss keeps falling, the model has
    started memorizing its examples. A snapshot is saved every 25 updates, so
    we can go back to the best one.
The first few updates are slower while things warm up. Your Mac may get warm
and loud; that's normal. Training uses most of the memory the GPU is allowed,
especially for Nemo, so close big apps like browsers first. If Activity
Monitor's Memory Pressure turns red, stop with Control-C and set batch_size: 1.
If your Mac is plugged in, you can close the lid once training starts. It keeps
running, and with the screen off macOS won't interrupt it.

GUIDE

echo "Settings: $CONFIG. Model: $MODEL. Add-on: $ADAPTER_DIR."
echo
# macOS stops any GPU job that holds up drawing the screen for too long
# ("Impacting Interactivity"); long training sequences can trip it. This Apple
# driver setting relaxes that limit, and caffeinate keeps the Mac awake if you
# close the lid, which turns the screen off and removes the problem entirely.
export AGX_RELAX_CDM_CTXSTORE_TIMEOUT=1
KEEP_AWAKE=""
if command -v caffeinate >/dev/null 2>&1; then KEEP_AWAKE="caffeinate -is"; fi
gpu_stopped() {
  if grep -q "Impacting Interactivity" "$1" 2>/dev/null; then
    echo
    echo "macOS stopped the training because it was holding up the screen. To get around it:"
    echo "plug in your Mac, run this again, and once it says it's training, close the lid."
    echo "It keeps running with the lid closed (while plugged in), and the screen being off"
    echo "removes the problem. The log is saved in $1."
  fi
}

if ! $KEEP_AWAKE "$TOOL_PY" lab_launcher.py --config "$CONFIG" ${EPOCHS:+--epochs "$EPOCHS"} 2>&1 | tee train-log.txt; then
  gpu_stopped train-log.txt
  exit 1
fi
bash list_adapters.sh > /dev/null

cat <<EOF

Done. To try it in the playground:
  1. Start the server:   bash ~/Documents/base-model-lab/start-base-model.sh
  2. In the playground, choose Provider: Server on this Mac, then pick
     $(basename "$ADAPTER_DIR") from the Trained add-on menu. That also picks the model.
  3. Write a prompt like this, ending with "Assistant:" and no stop string:

     User: what's a fun activity i can do today?

     Assistant:

The learning rate eases off toward the end, so the final add-on is usually the
one to use. If Val loss was clearly lowest partway through, use that snapshot
instead. For example, for update 150, run
  bash ~/Documents/base-model-lab/pick_checkpoint.sh 150 $(basename "$ADAPTER_DIR")
and pick the new add-on from the menu.
EOF
