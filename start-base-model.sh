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

# This starts the same mlx_lm.server with two fixes for continuing documents:
#
# 1. The server drops the space before the first word it sends back. That suits
#    chat replies, but here it glues the first word onto your text
#    ("species of" + " owl" comes back as "species ofowl").
# 2. Some model conversions get the special tokens wrong. mlx-community's
#    Mistral Nemo puts an end-of-document token after every prompt, so the
#    model thinks your document is finished and starts a new, unrelated one;
#    its Llama 3.1 8B leaves off the start-of-document token the model was
#    trained with.
LAUNCHER=$(cat <<'PY'
import sys
import mlx_lm.tokenizer_utils as tu

try:
    tu.BPEStreamingDetokenizer._maybe_trim_space = lambda self, text: text
    _spm_init = tu.SPMStreamingDetokenizer.__init__
    tu.SPMStreamingDetokenizer.__init__ = (
        lambda self, tokenizer, trim_space=True: _spm_init(self, tokenizer, trim_space=False)
    )
except Exception as e:
    print(f"(Couldn't keep the first word's leading space: {e})")

try:
    from tokenizers.processors import TemplateProcessing
    _wrapper_init = tu.TokenizerWrapper.__init__

    def _init(self, tokenizer, *args, **kwargs):
        _wrapper_init(self, tokenizer, *args, **kwargs)
        try:
            eos, bos = tokenizer.eos_token_id, tokenizer.bos_token_id
            backend = getattr(tokenizer, "_tokenizer", None)
            ids = tokenizer.encode("a")
            ends_with_eos = eos is not None and ids and ids[-1] == eos
            missing_bos = bos is not None and (not ids or ids[0] != bos)
            if backend is None or not (ends_with_eos or missing_bos):
                return
            if bos is not None:
                b = tokenizer.bos_token
                backend.post_processor = TemplateProcessing(
                    single=f"{b} $A", pair=f"{b} $A {b} $B", special_tokens=[(b, bos)]
                )
            else:
                backend.post_processor = TemplateProcessing(single="$A", pair="$A $B")
            print("(Fixed this model's tokenizer so prompts start with a start-of-document token and don't end with an end-of-document one.)")
        except Exception as e:
            print(f"(Couldn't check the tokenizer's end-of-document setting: {e})")

    tu.TokenizerWrapper.__init__ = _init
except Exception as e:
    print(f"(Couldn't patch the tokenizer: {e})")

from mlx_lm.server import main
sys.argv = ["mlx_lm.server"] + sys.argv[1:]
main()
PY
)

TOOL_PY="$(uv tool dir 2>/dev/null)/mlx-lm/bin/python"
if [ -x "$TOOL_PY" ]; then
  exec "$TOOL_PY" -c "$LAUNCHER" --model "$MODEL" --port "$PORT"
fi
exec mlx_lm.server --model "$MODEL" --port "$PORT"
