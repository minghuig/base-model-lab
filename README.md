# Base model lab

A small lab for two things, on a 16 GB Apple silicon MacBook Pro: seeing what a language model is like before any post-training, and doing a bit of post-training ourselves.

It has three parts:

- **A playground** (`base-model-playground.html`). You write the start of a document and a base model continues it. It talks to a server on this Mac, to OpenRouter, or to Featherless.
- **A local server** (`start-base-model.sh`). It runs mlx-lm's server with Mistral Nemo 12B base and Llama 3.1 8B base. The playground can switch between them.
- **A fine-tune** (`train.sh` and friends). A LoRA add-on teaches Llama 3.1 8B base to answer as an assistant whose writing is genuinely good. It trains on 312 single-turn conversations written for this.

## Quick start

**Play with a base model.** In Terminal, run:

```
bash ~/Documents/base-model-lab/start-base-model.sh
```

The first run installs uv and mlx-lm and asks before downloading the models, about 12 GB for both. Leave that window open. Then open `base-model-playground.html` in Safari or Chrome and choose **Provider: Server on this Mac**.

**Train the add-on.** First stop the server with Control-C in its window, because training needs the memory. Then run:

```
bash ~/Documents/base-model-lab/train.sh
```

At the current settings (150 updates) this takes about 10 minutes. The add-on and its snapshots go in `adapters/prose/`, and the output goes to `train-log.txt`.

**Use the best snapshot.** Find the update with the lowest "val" loss in the log, then turn that snapshot into an add-on. For update 100:

```
bash ~/Documents/base-model-lab/pick_checkpoint.sh 100
```

Restart the server and set up the playground:

- **Model:** Llama 3.1 8B base
- **Trained add-on:** the folder the script printed, such as `/Users/minghuiguo/Documents/base-model-lab/adapters/prose-step100`
- **Stop string:** leave it empty

Then prompt it in the training format:

```
User: what's a fun activity i can do today?

Assistant:
```

The add-on learned to end its reply with the end-of-text token, so the reply stops on its own.

## Files

| Path | What it is |
|---|---|
| `base-model-playground.html` | Single-file playground with no build step. Settings and API keys live in the browser's localStorage under `bmp.*`, one key per provider, and never in this folder. |
| `start-base-model.sh` | Installs the tools, downloads the models, and starts `mlx_lm.server` on port 8080 with the fixes described below. With no argument it picks the largest base model that fits in memory. Give it a Hugging Face model ID to override that. |
| `train.sh` | Checks the setup, refuses to run while the server is up, keeps any earlier add-on by renaming it, then runs `lab_launcher.py` with `config.yaml`. |
| `lab_launcher.py` | Runs `mlx_lm.lora` with the tokenizer fix and the `User:` / `Assistant:` chat template installed. |
| `config.yaml` | LoRA settings, with a comment on each line. |
| `pick_checkpoint.sh` | Copies one saved snapshot into its own add-on folder, `adapters/prose-step<N>/`. |
| `data/train.jsonl`, `data/valid.jsonl` | 282 training and 30 held-out conversations, as `{"prompt", "completion"}` lines. They're generated, so don't edit them by hand. |
| `dataset_src/` | The conversations in ten batches by category, plus `build_dataset.py`, which runs quality checks and writes `data/`. |
| `runs/` | Logs from past training runs. The table under "Results so far" summarizes them. |

These are git-ignored: `adapters/`, where each snapshot is about 42 MB, and `train-log.txt`, which is overwritten on every run.

## How the training data is formatted

Each conversation is rendered as:

```
<|begin_of_text|>User: {prompt}

Assistant: {reply}<|end_of_text|>
```

Only the reply counts toward the loss (`mask_prompt: true`). The model learns how to answer, not how to ask.

We deliberately avoid Llama 3's chat tokens (`<|start_header_id|>`, `<|eot_id|>` and the rest). The base model never trained on them, so their embeddings are essentially untrained, and a small add-on would have to learn them from scratch. Plain `User:` / `Assistant:` transcripts already appear on the web, so the base model starts out with some idea of the format.

The dataset is single-turn only. The template would render a second turn straight after `<|end_of_text|>`, which we've never trained on.

## Fixes on top of mlx-lm

Both launchers patch mlx-lm at startup. The server's patches are inlined in `start-base-model.sh`, and training's are in `lab_launcher.py`. The server prints a line in parentheses when it fixes a tokenizer, and another if a patch fails. The training launcher applies its fixes silently.

1. **Start- and end-of-document tokens.** The mlx-community conversion of Mistral Nemo base appended `</s>` (end of document) to every prompt. The model was being asked to continue a document it had just been told was over. That's why replies were often in a random language, like the run that answered only in Arabic. The Llama 3.1 8B conversion had the opposite problem: it added no `<|begin_of_text|>`. The patch replaces the tokenizer's post-processor so every prompt starts with the start-of-document token and doesn't end with an end-of-document one. Training gets the same fix, so the add-on sees prompts the way the server sends them.
2. **The first word's leading space.** mlx_lm.server's streaming detokenizer trims the space before the first generated token. In a completion, that glued the continuation onto the prompt. The server patch turns the trim off.
3. **Chat template (training only).** `lab_launcher.py` gives the tokenizer the template above, so mlx_lm.lora's chat-formatting path produces our format.

One related quirk: stop strings that begin with a newline (such as `"\nUser:"`) didn't fire reliably with mlx_lm.server. The playground's starters use `User:` and `Q:` instead.

These patches reach into mlx-lm internals (`TokenizerWrapper`, `BPEStreamingDetokenizer`, `SPMStreamingDetokenizer`), so an mlx-lm upgrade could break them. After an upgrade, check the server's startup messages and try one playground continuation.

## The dataset

The 312 conversations are written in one voice: plain, precise and warm. Length fits the question, from a one-word reply to about 170 words (median about 100). They use no markdown, no em dashes, and none of the stock assistant phrases. The ten batches:

| Batch | Category | Count |
|---|---|---|
| b01 | Science explanations | 28 |
| b02 | History and technology | 28 |
| b03 | How-to | 35 |
| b04 | Advice | 35 |
| b05 | Opinions and comparisons | 29 |
| b06 | Creative writing | 37 |
| b07 | Editing someone's text | 30 |
| b08 | Playful questions | 30 |
| b09 | Quick replies and small talk | 35 |
| b10 | Work and tech | 25 |

`build_dataset.py` holds out three conversations per batch for validation. The split is seeded, so a rebuild of unchanged batches gives identical files. It also reports duplicate prompts, reply lengths, markdown, em dashes, common first words, and a list of banned tics ("delve", "great question", "it's important to note" and so on). After editing a batch, run:

```
python3 dataset_src/build_dataset.py
```

"What's a fun activity I can do today?" was Ming's first question to a base model. It's deliberately in neither file, so it can serve as the headline test.

## Results so far

### Run 1, 2026-11-07

Settings: LoRA rank 8, scale 20, last 16 layers (10.5M trainable parameters, 0.13% of the model), batch 2, learning rate 2e-5, 450 updates. One pass over the training set is 141 updates, so this was a bit over three passes. It took about 28 minutes. The full log is in `runs/2026-11-07-prose-450-log.txt`.

| Update | start | 50 | **100** | 150 | 200 | 250 | 300 | 350 | 400 | 450 |
|---|---|---|---|---|---|---|---|---|---|---|
| Held-out loss | 2.379 | 1.855 | **1.796** | 1.813 | 1.962 | 2.038 | 2.646 | 2.437 | 2.494 | 2.866 |

Average training loss was 1.93 on the first pass, 1.04 on the second and 0.36 on the third. It fell to about 0.1 by the end.

What it means: the add-on learned the voice quickly. Held-out loss fell from 2.38 to 1.80 within the first pass. After that it began memorizing. Training loss drops sharply each time a pass starts over (1.83 at update 140, 1.37 at 150), because the model is seeing replies it has seen before. Meanwhile held-out loss rises. The best snapshot is update 100.

Change for the next run: `iters` is now 150, with snapshots at 50, 100 and 150.

## Ideas for what's next

- **Three-way comparison.** Use the same prompts on three setups: the base model with the plain `User:` / `Assistant:` format, the base model with a style header (a written description of the voice, or a few example exchanges, placed before the conversation), and the trained add-on. The prompts are the 30 held-out conversations plus the fun-activity question. This tests how much of a "personality" a prompt alone can buy, versus training.
- **Playground additions.** Top-p and repetition-penalty controls, and a token-probability view. The local server can return logprobs, which would let us look at calibration before and after training.
- **Preference tuning or RL.** DPO on pairs of replies (one good, one worse), or small RL loops. None of this is set up yet. When we get there, check which MLX trainers currently support these.

## Practical notes

- With 16 GB, only one model fits in memory at a time. The server holds one and swaps when the playground's model menu changes, which takes a few seconds. Training needs the server stopped.
- Don't edit `train.sh` while it's running. Bash reads a script as it goes, so an edit can change what the rest of the run does.
- Open the playground directly in Safari or Chrome. Previews embedded in other apps may block its requests, and the page shows a notice when it's inside a frame.
- The models are cached in `~/.cache/huggingface`, outside this folder.
