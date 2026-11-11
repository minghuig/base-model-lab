# How it works

## The server and the playground

`start-base-model.sh` starts `mlx_lm.server` on port 8080 through `server_launcher.py`, which adds the lab's fixes and the scoring behind Show surprise (see below). With no argument, it starts the largest base model that fits comfortably in memory: Mistral Nemo 12B base on 16 GB. It also downloads Llama 3.1 8B base, the model the lab trains. Give it a Hugging Face model ID to start a different one. The server holds one model at a time and switches when a request asks for another one or for a different add-on, which takes a few seconds.

The playground is a single HTML file. Its settings and API keys are kept in the browser's localStorage under `bmp.*`, one key per provider, and never in this folder.

## The training format

Each training conversation is rendered as:

```
<|begin_of_text|>User: {first message}

Assistant: {first reply}

User: {second message}

Assistant: {last reply}<|end_of_text|>
```

A single exchange is just the first and last lines. Only the last reply counts toward the loss (`mask_prompt: true`), and only the last reply ends with `<|end_of_text|>`. Earlier turns are context, the way a chat app sends the whole conversation each time and the model writes one reply. The model learns how to answer, not how to ask, and that it should stop after its reply even when the conversation looks like it's still going. The template lives in `lab_launcher.py`.

To continue a conversation in the playground, add a blank line, `User: ...`, a blank line and `Assistant:` after the model's reply.

We deliberately avoid Llama 3's chat tokens (`<|start_header_id|>`, `<|eot_id|>` and the rest). The base model never trained on them, so their embeddings are essentially untrained, and a small add-on would have to learn them from scratch. Plain `User:` / `Assistant:` transcripts already appear on the web, so the base model starts out with some idea of the format.

## The dataset

The conversations are written in one voice: plain, precise and warm. Length fits the question, from a one-word reply to about 170 words (median about 90). They use no markdown, no em dashes, and none of the stock assistant phrases.

| Batch | Category | Count | Added for |
|---|---|---|---|
| b01 | Science explanations | 28 | run 1 |
| b02 | History and technology | 28 | run 1 |
| b03 | How-to | 35 | run 1 |
| b04 | Advice | 35 | run 1 |
| b05 | Opinions and comparisons | 29 | run 1 |
| b06 | Creative writing | 37 | run 1 |
| b07 | Editing someone's text | 30 | run 1 |
| b08 | Playful questions | 30 | run 1 |
| b09 | Quick replies and small talk | 35 | run 1 |
| b10 | Work and tech | 25 | run 1 |
| b11 | Follow-ups: two- and three-turn conversations | 40 | run 2 |
| b12 | Questions about the assistant itself | 25 | run 2 |
| b13 | Things it can't see or know | 20 | run 2 |
| b14 | Short exchanges and conversation endings | 15 | run 2 |
| b15 | Personal-sounding questions that should just be answered | 26 | run 3 |

Each batch file starts with a comment saying what it's for. A batch's `EXAMPLES` items are either `(user, reply)` pairs or lists of alternating turns ending with a reply.

`build_dataset.py` writes `data/train.jsonl` and `data/valid.jsonl`, holding out three conversations per batch for validation. The split is seeded and batches are processed in name order, so rebuilding unchanged batches gives identical files, and adding a batch leaves the earlier batches' held-out conversations where they were. It also reports duplicates, reply lengths, markdown, em dashes, common first words, and a list of banned tics ("delve", "great question", "it's important to note" and so on). After editing a batch, run:

```
python3 dataset_src/build_dataset.py
```

"What's a fun activity I can do today?" was Ming's first question to a base model. It's deliberately in neither file, so it can serve as the headline test.

## Training settings

`config.yaml` trains on Llama and `config-nemo.yaml` on Nemo; they're the same recipe, and both have a comment on every line. `train.sh --config FILE` picks one. The main choices:

- **The add-on** is LoRA, rank 8 and scale 20, on the last 16 of the model's layers. Llama has 32 layers, so that's 10.5M trainable numbers, 0.13% of the model. Nemo has 40 wider ones, so 11.4M, 0.09%. Training runs on the 4-bit model.
- **Run length** is set in passes over the data, or epochs. `epochs` is the lab's own setting: `lab_launcher.py` counts `train.jsonl` and works out mlx-lm's `iters`, so a run stays one pass long when the data changes. `train.sh --epochs N` overrides it for one run.
- **The learning rate** warms up over 10 updates, then eases along a cosine curve to almost nothing by the last update (peak 4e-5). The final add-on is then a settled version of "has seen everything once." See [the runs](../runs/README.md) for why.
- **Snapshots and held-out scores** come every 25 updates, so a run can be cut short after the fact with `pick_checkpoint.sh`.
- **Each run gets its own folder**, `adapter_path` in the config: `adapters/prose`, `adapters/prose-v2`, and so on, and `adapters/nemo-prose` for Nemo. If the folder already has an add-on, `train.sh` asks before renaming the old one.
- **Memory.** Training holds the 4-bit model (about 4.5 GB for Llama, 6.9 GB for Nemo), plus a little for the add-on, its optimizer state and one batch's activations. The conversations are short (226 tokens at most), so that last part is small, and `grad_checkpoint` recomputes activations instead of storing them. Nemo should peak around 8 GB, under the 10 to 11 GB macOS lets the GPU use on a 16 GB Mac by default; that's an estimate, not yet measured. If Memory Pressure in Activity Monitor turns red, `batch_size: 1` roughly halves the batch's share.

**When macOS stops training.** While the screen is on, macOS stops any GPU job that holds up drawing it for too long, and the run ends with `Command buffer execution failed: Impacting Interactivity`. Longer sequences make it more likely. SFT's conversations (226 tokens at most) trained fine with the screen on, but the first DPO run, with Compare replies up to about 1,100 tokens, was stopped at its first update. Both `train.sh` and `dpo.sh` set `AGX_RELAX_CDM_CTXSTORE_TIMEOUT=1`, an Apple driver setting that MLX's maintainers suggest for this, and run under `caffeinate -is`, which keeps the Mac awake with the lid closed while it's plugged in. With the lid closed the screen is off, so the problem goes away. If it still happens, the scripts say so. See [ml-explore/mlx#3267](https://github.com/ml-explore/mlx/issues/3267).

Snapshots are about 42 MB each. `list_adapters.sh` writes `adapters/index.js`, which has this Mac's paths in it. The playground reads that file to fill its add-on menu. Picking an add-on also picks the model it was trained on, and switching to a different model sets the add-on back to None, since an add-on only fits the model it was trained on.

## The surprise view

**Show surprise** colors each token by the probability the model gave it, given everything before it. Point at a token to see the model's top guesses for that spot. The chip at the end shows the chance the document ends right there. With a trained add-on picked, you get the model with and without it side by side.

With nothing selected, it scores the text the model wrote and shows your text in gray for context, without counting it, the way training only scores the reply. Select some text to score exactly that instead. The average it reports is the same loss training reports: the average of minus the log of these probabilities.

## Preference tuning (Compare and DPO)

SFT shows the model good replies and makes them more likely. Preference tuning shows it two of its own replies to the same prompt and which one you liked, and makes the liked one more likely relative to the other. It teaches the difference between two replies the model would actually write, which is often subtler than anything easy to write down as an example.

**Collecting pairs.** In the playground, pick the add-on to improve (normally the one `dpo.yaml` starts from), then press **Compare**. It writes two replies to the same prompt with your current temperature and max tokens. Press **A is better** or **B is better** (or the 1 and 2 keys) and it saves the pair and moves to the next prompt. **Skip** (S) moves on without saving, for when neither is better or both are bad; **New pair** writes two fresh replies to the same prompt. Prompts come from `prefs/prompts.js`, or choose **The document** to use what's in the document box. The list has 196 prompts, none of them in the training data or the probes; the last 44 aim at what the run 3 probes showed, including eight short conversations, where the replies answer a follow-up. An entry is a question or a conversation written as `[user, assistant, user]`, and the playground keeps your place in the list, so add new ones at the end. The server appends each pair to `prefs/pairs.jsonl`, one JSON object per line, with the prompt, both replies, how each ended (stopped on its own, or hit the length limit), and the model, add-on and settings that wrote them. This file is your picks: keep it, and don't regenerate it.

What makes a useful pick: judge the whole reply, including whether it stopped in the right place. If the two are nearly the same, skip; a pair only teaches the difference between its two replies. Aim for 100 to 200 pairs. Training refuses to start with fewer than 20.

**Training.** Stop the server, then run `dpo.sh`. It trains a copy of the starting add-on with DPO (direct preference optimization):

1. A reply's score is the log of the probability the model gives it: the sum, over its tokens, of the log-probability of each token given everything before it. These are the numbers Show surprise colors. A reply that stopped on its own includes the end-of-text token, so stopping is part of what's scored.
2. Before training, the starting add-on scores every reply once. That's the reference.
3. For each pair, `margin = beta × ((chosen now − chosen before) − (rejected now − rejected before))`, and the loss is `−log(sigmoid(margin))`. It starts at log 2 = 0.693, when nothing has moved, falls as the model moves toward your pick and away from the other, and flattens out as the margin grows. So there's little to gain from pushing any one pair to extremes. That, and beta, keep the model close to where it started.
4. Nudge the add-on's numbers to lower the loss, averaged over 4 pairs at a time.

Classic RLHF trains a separate reward model on the pairs and then runs reinforcement learning (PPO) against it, sampling new replies as it goes. DPO reaches a mathematically similar result directly from the pairs, with one model in memory, which is what fits on 16 GB. The trade-off is that it learns only from the replies you judged, not from new ones it writes during training.

The log reports, for the training pairs and for 10% held out: the loss, **prefers your pick** (the share of pairs where the model has moved toward your choice more than toward the other), the average margin, and how each reply's score changed. Often both scores fall, the rejected one faster. That's normal for DPO, but if the chosen score falls a lot, the model is drifting from everything it used to write, not just the rejected replies. The held-out numbers are the honest check: if "prefers your pick" rises there, it's learning what you like rather than these exact replies. With few pairs the held-out set is small, so its numbers jump around.

Settings are in `dpo.yaml`: `beta` 0.1, learning rate 2e-5, 3 epochs, which suit about 50 pairs. How far training moves the model is roughly the learning rate times the number of updates, so with 150 pairs, 1e-5 and 2 epochs give about the same total. The result goes to `adapters/prose-v3-dpo`, with a snapshot after each epoch (`epoch1_adapters.safetensors`). To try the epoch-1 snapshot, copy the folder and rename that file to `adapters.safetensors` in the copy, then run `list_adapters.sh`. If an add-on is already in the output folder, `dpo.sh` asks, then renames the old one with the date and time rather than overwriting it. The new add-on's `adapter_config.json` records what it was trained from, under `dpo`.

DPO only knows what the pairs show. If every pair you prefer is the shorter reply, it may learn "shorter" rather than "better". Mixing in pairs where the longer reply wins keeps it honest, as the contrast examples did for SFT.

## Fixes on top of mlx-lm

Both launchers patch mlx-lm at startup: `server_launcher.py` for the server and `lab_launcher.py` for training. The server prints a line in parentheses when it fixes a tokenizer, and another if a patch can't be applied.

1. **Start- and end-of-document tokens.** The mlx-community conversion of Mistral Nemo base appended `</s>` (end of document) to every prompt. The model was being asked to continue a document it had just been told was over, which is why replies were often in a random language, like the run that answered only in Arabic. The Llama 3.1 8B conversion had the opposite problem: it added no `<|begin_of_text|>`. The patch replaces the tokenizer's post-processor so every prompt starts with the start-of-document token and doesn't end with an end-of-document one. Training gets the same fix, so the add-on sees prompts the way the server sends them. With Nemo's own tokenizer, every training conversation comes out with exactly one `<s>` at the start and one `</s>` after the last reply, and the prompt is an exact prefix of the whole, so the loss mask lines up. (Recent versions of transformers warn that this conversion's pre-tokenizer pattern is wrong; turning on their fix changes none of the 438 conversations.)
2. **The first word's leading space.** mlx_lm.server's streaming detokenizer trims the space before the first generated token. In a completion, that glued the continuation onto the prompt. The server patch turns the trim off.
3. **Chat template (training only).** `lab_launcher.py` gives the tokenizer the template above, so mlx_lm.lora's chat-formatting path produces our format.
4. **Scoring (server only).** A `/v1/completions` request carrying `"lab_score": "<text>"` doesn't generate anything. It returns, for each token of that text, the probability the model gave it after the request's `prompt`, its rank, the model's top 5 guesses, and the probability that the document ends right after the text. The model reads the document in 256-token chunks, carrying its cache forward, so memory stays small; prompt plus text can be up to 4,096 tokens. The request goes through the server's own queue (a seed marks it as not batchable, which routes it to the single-request path on the generation thread). So it waits for any generation in progress and loads the requested model and add-on exactly as a normal request would.
5. **Saving preference pairs (server only).** `POST /lab/preference` appends a pair from Compare mode to `prefs/pairs.jsonl`, after checking it has a prompt and two different replies. `GET /lab/preference` returns how many pairs are saved. These are new routes on the server's own handler, not changes to existing ones.

One related quirk: stop strings that begin with a newline (such as `"\nUser:"`) didn't fire reliably with mlx_lm.server, so the playground's starters use `User:` and `Q:` instead.

These patches reach into mlx-lm internals (`TokenizerWrapper`, `BPEStreamingDetokenizer`, `SPMStreamingDetokenizer`, for scoring `ResponseGenerator._serve_single` and `APIHandler.handle_completion`, and for pairs `APIHandler.do_POST` and `do_GET`), so an mlx-lm upgrade could break them. They were written and tested against mlx-lm 0.32.2. After an upgrade, check the server's startup messages, then try one continuation and one Show surprise.

## Testing changes without the Mac

MLX also runs on Linux, on the CPU (`pip install "mlx[cpu]" mlx-lm==0.32.2`). A tiny, randomly initialized llama model (from `mlx_lm.models.llama`), with a small byte-level BPE tokenizer trained on `data/` and saved with transformers, is enough to run `server_launcher.py` or `lab_launcher.py` for real. That's how the scoring patch, the multi-turn masking, Compare mode and DPO training were checked. The outputs are nonsense, but the mechanics are the real ones.
