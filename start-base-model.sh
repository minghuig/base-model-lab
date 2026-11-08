#!/bin/bash
# Base model playground: run a base language model on this Mac.
#
# Run it in Terminal with:
#   bash ~/Documents/base-model-lab/start-base-model.sh
#
# The first run installs what it needs and downloads the model. After that,
# run the same command whenever you want the server back. To try a different
# model, put its Hugging Face ID after the command, for example:
#   bash ~/Documents/base-model-lab/start-base-model.sh mlx-community/Meta-Llama-3.1-8B-4bit

set -euo pipefail

PORT=8080
export PATH="$HOME/.local/bin:$PATH"

if [ "$(uname -s)" != "Darwin" ] || [ "$(uname -m)" != "arm64" ]; then
  echo "This needs a Mac with Apple silicon (M1 or later)."
  exit 1
fi

RAM_GB=$(( $(sysctl -n hw.memsize) / 1073741824 ))
FREE_GB=$(df -g "$HOME" | awk 'NR==2 {print $4}')

model_name() {
  case "$1" in
    mlx-community/Meta-Llama-3.1-70B-4bit) echo "Llama 3.1 70B base" ;;
    mlx-community/Qwen2.5-32B-4bit) echo "Qwen 2.5 32B base" ;;
    mlx-community/Mistral-Nemo-Base-2407-4bit) echo "Mistral Nemo 12B base" ;;
    mlx-community/Meta-Llama-3.1-8B-4bit) echo "Llama 3.1 8B base" ;;
    *) echo "$1" ;;
  esac
}
model_size_gb() {
  case "$1" in
    mlx-community/Meta-Llama-3.1-70B-4bit) echo 40 ;;
    mlx-community/Qwen2.5-32B-4bit) echo 19 ;;
    mlx-community/Mistral-Nemo-Base-2407-4bit) echo 7 ;;
    mlx-community/Meta-Llama-3.1-8B-4bit) echo 5 ;;
    *) echo 0 ;;
  esac
}
cache_dir() { echo "${HF_HOME:-$HOME/.cache/huggingface}/hub/models--${1//\//--}"; }

# Pick the largest base model that fits comfortably in this Mac's memory.
# macOS lets the GPU use roughly two thirds to three quarters of RAM.
if [ -n "${1:-}" ]; then
  MODEL="$1"
elif [ "$RAM_GB" -ge 64 ]; then
  MODEL="mlx-community/Meta-Llama-3.1-70B-4bit"
elif [ "$RAM_GB" -ge 32 ]; then
  MODEL="mlx-community/Qwen2.5-32B-4bit"
elif [ "$RAM_GB" -ge 16 ]; then
  MODEL="mlx-community/Mistral-Nemo-Base-2407-4bit"
else
  MODEL="mlx-community/Meta-Llama-3.1-8B-4bit"
fi

# Llama 3.1 8B base is the model the post-training lab fine-tunes. It's
# downloaded too, so the playground can switch to it.
TRAIN_MODEL="mlx-community/Meta-Llama-3.1-8B-4bit"
MODELS=("$MODEL")
[ "$TRAIN_MODEL" != "$MODEL" ] && MODELS+=("$TRAIN_MODEL")

echo "This Mac has ${RAM_GB} GB of memory and ${FREE_GB} GB of free disk space."
echo "The server starts with: $(model_name "$MODEL")"
if [ "${#MODELS[@]}" -gt 1 ]; then
  echo "The playground can also switch to: $(model_name "$TRAIN_MODEL") (the one we'll train)"
fi

MISSING=()
NEED_GB=0
for m in "${MODELS[@]}"; do
  if [ ! -d "$(cache_dir "$m")" ]; then
    MISSING+=("$m")
    NEED_GB=$(( NEED_GB + $(model_size_gb "$m") ))
  fi
done

if [ "${#MISSING[@]}" -eq 0 ]; then
  echo "Everything's been downloaded before."
else
  echo ""
  echo "To download (saved in ~/.cache/huggingface, so this only happens once):"
  for m in "${MISSING[@]}"; do
    size=$(model_size_gb "$m")
    if [ "$size" -gt 0 ]; then echo "  $(model_name "$m"), about ${size} GB"; else echo "  $(model_name "$m")"; fi
  done
  if [ "$FREE_GB" -lt $(( NEED_GB + 5 )) ]; then
    echo "There isn't enough free disk space for that. Free up some space, or pass a smaller model ID."
    exit 1
  fi
  read -r -p "Download and start the server? [y/N] " answer
  case "$answer" in
    y|Y|yes|Yes) ;;
    *) echo "Nothing was downloaded."; exit 0 ;;
  esac
fi

if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Something is already running on port ${PORT}. If it's an earlier copy of this server,"
  echo "switch to that Terminal window and press Control-C, then run this again."
  exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
  echo ""
  echo "Installing uv (a Python installer) into ~/.local/bin…"
  curl -LsSf https://astral.sh/uv/install.sh | env INSTALLER_NO_MODIFY_PATH=1 sh
fi

if ! command -v mlx_lm.server >/dev/null 2>&1; then
  echo ""
  echo "Installing mlx-lm, Apple's tools for running language models…"
  uv tool install --python 3.12 mlx-lm
fi

# Download before starting the server: the server loads models in the
# background, so requests sent during a long first download would just hang.
for m in "${MODELS[@]}"; do
  echo ""
  echo "Checking $(model_name "$m") (a download resumes where it left off if interrupted)…"
  if ! uv tool run --from huggingface_hub hf download "$m" > /dev/null; then
    if [ -d "$(cache_dir "$m")" ]; then
      echo "Couldn't reach Hugging Face; using the copy already on this Mac."
    else
      echo "The download didn't finish. Check your internet connection, then run this again."
      exit 1
    fi
  fi
done

echo ""
echo "Starting the server at http://localhost:${PORT}."
echo "It's ready once it prints \"Starting httpd at 127.0.0.1 on port ${PORT}\". The first"
echo "continuation can take a little longer while the model finishes loading into memory."
echo "A warning that the server isn't meant for production is expected: it only accepts"
echo "connections from this Mac."
echo ""
echo "Then open the playground and choose Provider: Server on this Mac. Use its Model menu"
echo "to switch between the downloaded models."
echo "Leave this window open while you play. Press Control-C here to stop the server."
echo ""

# This starts the same mlx_lm.server with the lab's fixes and additions from
# server_launcher.py, next to this script: it keeps the first word's leading
# space, fixes start- and end-of-document tokens, and adds the scoring behind
# the playground's "Show surprise" button. See the notes at the top of that file.
HERE="$(cd "$(dirname "$0")" && pwd)"
TOOL_PY="$(uv tool dir 2>/dev/null)/mlx-lm/bin/python"
if [ -x "$TOOL_PY" ] && [ -f "$HERE/server_launcher.py" ]; then
  exec "$TOOL_PY" "$HERE/server_launcher.py" --model "$MODEL" --port "$PORT"
fi
echo "(Starting the plain server, without the lab's fixes: server_launcher.py or mlx-lm's own Python wasn't found.)"
exec mlx_lm.server --model "$MODEL" --port "$PORT"
