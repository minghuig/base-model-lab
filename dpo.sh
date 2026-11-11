#!/bin/bash
# Trains a new add-on from your picks in the playground's Compare mode, using
# preference tuning (DPO). It starts from the add-on named in dpo.yaml and
# saves the result where dpo.yaml says, then adds it to the playground's menu.
#
# Run it in Terminal with:
#   bash ~/Documents/base-model-lab/dpo.sh
#
# Stop the playground server first: training needs the memory.

set -euo pipefail
cd "$(dirname "$0")"
export PATH="$HOME/.local/bin:$PATH"

PORT=8080
setting() { sed -n "s/^$1:[[:space:]]*\([^[:space:]#]*\).*/\1/p" dpo.yaml; }
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
COUNT=$(grep -c . "$PAIRS" || true)
if [ "$COUNT" -lt 20 ]; then
  echo "There are only $COUNT pairs in $PAIRS. Training on fewer than about 20 mostly teaches"
  echo "the model those exact replies. Collect more with the playground's Compare button first."
  exit 1
fi
if [ ! -f "$START/adapters.safetensors" ]; then
  echo "The starting add-on $START isn't there. Check start_adapter in dpo.yaml."
  exit 1
fi

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

Training on $COUNT pairs, starting from $(basename "$START"). What to watch:
  - "prefers your pick": how often the model has moved toward the reply you
    chose and away from the one you didn't, compared with where it started.
    Before training every pair is a tie; this should rise on the training pairs.
  - The held-out pairs are the honest check. If it rises there too, the model
    is learning what you like rather than memorizing these particular replies.
  - "chosen" and "rejected" show how each reply's score changed. Often both
    fall, with the rejected one falling faster; that's normal for this method.

GUIDE

"$TOOL_PY" dpo_train.py --config dpo.yaml 2>&1 | tee dpo-log.txt
bash list_adapters.sh > /dev/null

cat <<EOF2

Done. Start the server (bash ~/Documents/base-model-lab/start-base-model.sh), then
pick $(basename "$OUT") from the playground's Trained add-on menu and compare it
with $(basename "$START").
EOF2
