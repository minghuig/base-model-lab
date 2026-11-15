#!/bin/bash
# Trains a new add-on from your picks in the playground's Compare mode, using
# preference tuning (DPO). It starts from the add-on named in the settings file
# and saves the result where that file says, then adds it to the playground's
# menu. It only uses pairs written by the add-on it starts from.
#
# Run it in Terminal with:
#   bash ~/Documents/base-model-lab/dpo.sh                          (Llama, dpo.yaml)
#   bash ~/Documents/base-model-lab/dpo.sh --config dpo-nemo.yaml   (Nemo)
#
# Stop the playground server first: training needs the memory.

set -euo pipefail
cd "$(dirname "$0")"
export PATH="$HOME/.local/bin:$PATH"

CONFIG="dpo.yaml"
while [ $# -gt 0 ]; do
  case "$1" in
    --config)
      if [ $# -lt 2 ]; then echo "Usage: bash dpo.sh [--config FILE]"; exit 1; fi
      CONFIG="$2"; shift 2 ;;
    --config=*) CONFIG="${1#*=}"; shift ;;
    -h|--help) echo "Usage: bash dpo.sh [--config FILE]   (default dpo.yaml; dpo-nemo.yaml for Nemo)"; exit 0 ;;
    *) echo "Unknown option: $1"; echo "Usage: bash dpo.sh [--config FILE]"; exit 1 ;;
  esac
done
CONFIG="${CONFIG#./}"
if [ ! -f "$CONFIG" ]; then
  echo "There's no settings file called $CONFIG in this folder."
  exit 1
fi

PORT=8080
setting() { sed -n "s/^$1:[[:space:]]*\([^[:space:]#]*\).*/\1/p" "$CONFIG" | head -1; }
START="$(setting start_adapter)"
OUT="$(setting adapter_path)"
PAIRS="$(setting pairs)"

if ! command -v uv >/dev/null 2>&1 || [ ! -x "$(uv tool dir 2>/dev/null)/mlx-lm/bin/python" ]; then
  echo "mlx-lm isn't installed yet. Run  bash ~/Documents/base-model-lab/start-base-model.sh  once first,"
  echo "then come back and run this again."
  exit 1
fi
TOOL_PY="$(uv tool dir)/mlx-lm/bin/python"

if [ ! -f "$PAIRS" ]; then
  echo "There are no saved pairs yet ($PAIRS). Collect some with the playground's Compare button first."
  exit 1
fi
if [ ! -f "$START/adapters.safetensors" ]; then
  echo "The starting add-on $START isn't there. Check start_adapter in $CONFIG."
  exit 1
fi

# Check there are enough usable pairs before touching anything.
"$TOOL_PY" dpo_train.py --config "$CONFIG" --check-pairs || exit 1

if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "The playground server is still running, and training needs the memory it's using."
  echo "Switch to its Terminal window, press Control-C, then run this again."
  exit 1
fi

if [ -d "$OUT" ] && [ -n "$(ls -A "$OUT" 2>/dev/null)" ]; then
  echo "There's already an add-on in $OUT."
  read -r -p "Train a new one? The old one will be kept, renamed with today's date and time. [y/N] " answer
  case "$answer" in
    y|Y|yes|Yes) mv "$OUT" "${OUT}-$(date +%Y%m%d-%H%M%S)" ;;
    *) echo "Nothing changed."; exit 0 ;;
  esac
fi

cat <<GUIDE

Training from your picks, starting from $(basename "$START") ($CONFIG). What to watch:
  - "prefers your pick": how often the model has moved toward the reply you
    chose and away from the one you didn't, compared with where it started.
    Before training every pair is a tie; this should rise on the training pairs.
  - The held-out pairs are the honest check. If it rises there too, the model
    is learning what you like rather than memorizing these particular replies.
  - "chosen" and "rejected" show how each reply's score changed. Often both
    fall, with the rejected one falling faster; that's normal for this method.
If your Mac is plugged in, you can close the lid once training starts. It keeps
running, and with the screen off macOS won't interrupt it.

GUIDE

# macOS stops any GPU job that holds up drawing the screen for too long
# ("Impacting Interactivity"); long training sequences can trip it. This Apple
# driver setting relaxes that limit, and caffeinate keeps the Mac awake if you
# close the lid, which turns the screen off and removes the problem entirely.
export AGX_RELAX_CDM_CTXSTORE_TIMEOUT=1
# Print each line as it happens; piped into tee, Python would otherwise hold
# its output back until it had a big chunk or finished.
export PYTHONUNBUFFERED=1
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

if ! $KEEP_AWAKE "$TOOL_PY" dpo_train.py --config "$CONFIG" 2>&1 | tee dpo-log.txt; then
  gpu_stopped dpo-log.txt
  exit 1
fi
bash list_adapters.sh > /dev/null

cat <<EOF2

Done. Start the server (bash ~/Documents/base-model-lab/start-base-model.sh), then
pick $(basename "$OUT") from the playground's Trained add-on menu and compare it
with $(basename "$START").
EOF2
