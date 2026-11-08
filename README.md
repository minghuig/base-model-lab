# Base model lab

A small lab for two things, on a 16 GB Apple silicon MacBook Pro: seeing what a language model is like before any post-training, and doing a bit of post-training ourselves.

It has three parts:

- **A playground** (`base-model-playground.html`). You write the start of a document and a base model continues it. It talks to a server on this Mac, to OpenRouter, or to Featherless. With the local server it can also show how surprised the model was by each token of a text.
- **A local server** (`start-base-model.sh`). It runs mlx-lm's server with Mistral Nemo 12B base and Llama 3.1 8B base. The playground can switch between them.
- **A fine-tune** (`train.sh` and friends). A LoRA add-on teaches Llama 3.1 8B base to answer as an assistant whose writing is genuinely good. It trains on 412 conversations written for this, some of them several turns long.

## Quick start

**Play with a base model.** In Terminal, run:

```
bash ~/Documents/base-model-lab/start-base-model.sh
```

The first run installs uv and mlx-lm and asks before downloading the models, about 12 GB for both. Leave that window open. Then open `base-model-playground.html` in Safari or Chrome and choose **Provider: Server on this Mac**.

**See what the model expected.** Select some text in the document, or nothing for all of it, and press **Show surprise**. Each token is colored by the probability the model gave it, given everything before it. Point at a token to see the model's top guesses for that spot. The end shows the chance the document ends right there. With a trained add-on picked, you get the model with and without it side by side. This is the quantity training scores: the loss is the average of minus the log of these probabilities over a reply.

**Train the add-on.** First stop the server with Control-C in its window, because training needs the memory. Then run:

```
bash ~/Documents/base-model-lab/train.sh
```

At the current settings (one pass over the data, which is 185 updates, with a held-out score and a snapshot every 25) this takes about 15 minutes. To train for a different number of passes (epochs) without editing `config.yaml`, add `--epochs`, as in `train.sh --epochs 2`. The add-on and its snapshots go in the folder named by `adapter_path` in `config.yaml`, and the output goes to `train-log.txt`. Give each run its own folder: run 1 is `adapters/prose`, run 2 is `adapters/prose-v2`, and the next run is set up as `adapters/prose-v3`.

**Pick the add-on.** With the current settings, the learning rate eases to almost nothing by the last update, so the final add-on (named after the run's folder, such as `prose-v3`) is usually the one to use. If the "val" loss in the log was clearly lowest partway through, turn that snapshot into an add-on instead. For update 175 of the current run:

```
bash ~/Documents/base-model-lab/pick_checkpoint.sh 175
```

That makes `adapters/prose-v2-step175`. For a snapshot from an earlier run, name the run's folder too, as in `pick_checkpoint.sh 100 prose`.

Restart the server and set up the playground:

- **Trained add-on:** pick it from the menu. The menu lists every add-on in `adapters/`, and picking one also picks the model it was trained on.
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
| `start-base-model.sh` | Installs the tools, downloads the models, and starts `mlx_lm.server` on port 8080 through `server_launcher.py`. With no argument it picks the largest base model that fits in memory. Give it a Hugging Face model ID to override that. |
| `server_launcher.py` | Starts `mlx_lm.server` with the fixes and the scoring described below. |
| `train.sh` | Checks the setup, refuses to run while the server is up, keeps any earlier add-on by renaming it, then runs `lab_launcher.py` with `config.yaml`. |
| `lab_launcher.py` | Runs `mlx_lm.lora` with the tokenizer fix and the `User:` / `Assistant:` chat template installed, and turns `epochs` into `iters`. |
| `config.yaml` | LoRA settings, with a comment on each line. `epochs` is the lab's own setting: `lab_launcher.py` counts `train.jsonl` and works out mlx-lm's `iters`, so the run stays the same number of passes when the data changes. `train.sh --epochs N` overrides it for one run. |
| `pick_checkpoint.sh` | Copies one saved snapshot into its own add-on folder, `<run folder>-step<N>/`. |
| `list_adapters.sh` | Writes `adapters/index.js`, the list behind the playground's add-on menu. The other scripts run it for you. |
| `data/train.jsonl`, `data/valid.jsonl` | 370 training and 42 held-out conversations, as `{"messages": [...]}` lines. They're generated, so don't edit them by hand. |
| `dataset_src/` | The conversations in fourteen batches by category, plus `build_dataset.py`, which runs quality checks and writes `data/`. |
| `runs/` | Logs from past training runs. The table under "Results so far" summarizes them. |

These are git-ignored: `adapters/`, where each snapshot is about 42 MB (`index.js` in there has this Mac's paths), and `train-log.txt`, which is overwritten on every run.

## How the training data is formatted

Each conversation is rendered as:

```
<|begin_of_text|>User: {first message}

Assistant: {first reply}

User: {second message}

Assistant: {last reply}<|end_of_text|>
```

A single exchange is just the first and last lines. Only the last reply counts toward the loss (`mask_prompt: true`), and only the last reply ends with `<|end_of_text|>`. Earlier turns are context, the way a chat app sends the whole conversation each time and the model writes one reply. The model learns how to answer, not how to ask, and that it should stop after its reply even when the conversation looks like it's still going.

To continue a conversation in the playground, add a blank line, `User: ...`, a blank line and `Assistant:` after the model's reply.

We deliberately avoid Llama 3's chat tokens (`<|start_header_id|>`, `<|eot_id|>` and the rest). The base model never trained on them, so their embeddings are essentially untrained, and a small add-on would have to learn them from scratch. Plain `User:` / `Assistant:` transcripts already appear on the web, so the base model starts out with some idea of the format.

## Fixes on top of mlx-lm

Both launchers patch mlx-lm at startup. The server's patches are in `server_launcher.py`, and training's are in `lab_launcher.py`. The server prints a line in parentheses when it fixes a tokenizer, and another if a patch fails. The training launcher applies its fixes silently.

1. **Start- and end-of-document tokens.** The mlx-community conversion of Mistral Nemo base appended `</s>` (end of document) to every prompt. The model was being asked to continue a document it had just been told was over. That's why replies were often in a random language, like the run that answered only in Arabic. The Llama 3.1 8B conversion had the opposite problem: it added no `<|begin_of_text|>`. The patch replaces the tokenizer's post-processor so every prompt starts with the start-of-document token and doesn't end with an end-of-document one. Training gets the same fix, so the add-on sees prompts the way the server sends them.
2. **The first word's leading space.** mlx_lm.server's streaming detokenizer trims the space before the first generated token. In a completion, that glued the continuation onto the prompt. The server patch turns the trim off.
3. **Chat template (training only).** `lab_launcher.py` gives the tokenizer the template above, so mlx_lm.lora's chat-formatting path produces our format.
4. **Scoring (server only).** A `/v1/completions` request carrying `"lab_score": "<text>"` doesn't generate anything. It returns, for each token of that text, the probability the model gave it after the request's `prompt`, its rank, the model's top 5 guesses, and the probability that the document ends right after the text. The request goes through the server's own queue (a seed marks it as not batchable, which routes it to the single-request path on the generation thread). So it waits for any generation in progress and loads the requested model and add-on exactly as a normal request would.

One related quirk: stop strings that begin with a newline (such as `"\nUser:"`) didn't fire reliably with mlx_lm.server. The playground's starters use `User:` and `Q:` instead.

These patches reach into mlx-lm internals (`TokenizerWrapper`, `BPEStreamingDetokenizer`, `SPMStreamingDetokenizer`, and for scoring `ResponseGenerator._serve_single` and `APIHandler.handle_completion`), so an mlx-lm upgrade could break them. They were written and tested against mlx-lm 0.32.2. After an upgrade, check the server's startup messages and try one playground continuation.

## The dataset

The 412 conversations are written in one voice: plain, precise and warm. Length fits the question, from a one-word reply to about 170 words (median about 90). They use no markdown, no em dashes, and none of the stock assistant phrases. The fourteen batches:

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
| b11 | Follow-ups: two- and three-turn conversations | 40 |
| b12 | Questions about the assistant itself | 25 |
| b13 | Things it can't see or know | 20 |
| b14 | Short exchanges and conversation endings | 15 |

Batches b11 to b14 were added for run 2, aimed at what run 1 got wrong (see "Results so far"). Each batch file starts with a comment saying what it's for.

`build_dataset.py` holds out three conversations per batch for validation. The split is seeded and batches are processed in name order, so a rebuild of unchanged batches gives identical files, and adding a batch leaves the earlier batches' held-out conversations unchanged. The 30 from run 1 are still the first 30 lines of `valid.jsonl`. It also reports duplicate prompts, reply lengths, markdown, em dashes, common first words, and a list of banned tics ("delve", "great question", "it's important to note" and so on). After editing a batch, run:

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

Playing with update 100 in the playground showed what the loss numbers don't:

- **It didn't reliably stop.** With no stop string, it often ran on into a made-up next `User:` turn and kept going. Update 450 did the same.
- **It talked as if it were a person.** "The fresh air never fails to lift my spirits," "a few suggestions I've been meaning to read myself." Only 3 of the 312 conversations touched on what the assistant is.
- **It invented the user's surroundings.** Asked for a fun activity, it described a specific park, the ducks, a food truck that "will likely be there for at least another hour."
- **It overdid the style and the length.** It got lush rather than plain, and one reply ran 229 words when the longest training reply is 169.
- **The voice faded over turns.** By a made-up third turn it was writing markdown bullet lists, which appear nowhere in the data.
- **The polish made made-up facts more convincing.** It recommended a Stephen Baxter novel that doesn't seem to exist and misdescribed *The Overstory*.

It also showed that held-out loss isn't a judge of quality. Update 450's first reply read better than update 100's, even though its held-out loss was much worse. An overtrained model bets heavily on its own favorite phrasings, and log loss punishes confident wrong bets on held-out text, while sampling still draws from those favorite phrasings.

### Run 2, 2026-11-07

Why: training longer on the same data would only memorize it, so run 2 changed the data instead. It added the four new batches above, about 100 conversations aimed at stopping, identity, grounding and keeping the voice across turns. Everything else matched run 1, except 300 updates with a held-out score and a snapshot every 25. One pass over the 370 training conversations is 185 updates. It took about 22 minutes. The full log is in `runs/2026-11-07-prose-v2-300-log.txt`.

| Update | start | 25 | 50 | 75 | 100 | 125 | 150 | **175** | 200 | 225 | 250 | 275 | 300 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Held-out loss | 2.452 | 1.907 | 1.877 | 1.837 | 1.821 | 1.814 | 1.810 | **1.797** | 1.975 | 1.956 | 2.004 | 1.993 | 1.983 |

Average training loss was 1.92 over the first pass and 1.08 over the second. It fell from 1.85 at update 180 to 0.92 at update 200, right after the second pass began.

What it means: held-out loss fell steadily through the first pass and jumped as soon as the second began. That's the same memorizing pattern as run 1, easier to see with a score every 25 updates. The best snapshot is update 175 (`pick_checkpoint.sh 175`, giving `adapters/prose-v2-step175`).

These numbers aren't directly comparable with run 1's, because the held-out set grew from 30 to 42 conversations. The starting loss was higher (2.45 against 2.38), probably because the new held-out conversations, like questions about the assistant itself, are harder for the untrained model. To compare the runs, use Show surprise on the same text with each add-on, or compare samples.

### Next run, set up and not yet run

Both runs did best at the end of the first pass through the data: every update before it is on a conversation the model hasn't seen, and every update after it is a repeat. So instead of training longer and picking a snapshot, the config now trains for exactly one pass, or epoch (`epochs: 1`, 185 updates) with a learning rate schedule. It warms up over 10 updates, then eases down along a cosine curve to almost nothing by the last update, so the final add-on is a settled version of "has seen everything once." The peak is 4e-5, twice run 2's constant 2e-5, because easing off roughly halves the average step size. It's the same data as run 2, so this run tests the schedule alone. If it works, the end of training is the add-on to use, with no snapshot to pick. Its held-out loss is directly comparable with run 2's.

## Ideas for what's next

- **Three-way comparison.** Use the same prompts on three setups: the base model with the plain `User:` / `Assistant:` format, the base model with a style header (a written description of the voice, or a few example exchanges, placed before the conversation), and the trained add-on. The prompts are the held-out conversations plus the fun-activity question. This tests how much of a "personality" a prompt alone can buy, versus training.
- **Playground additions.** Top-p and repetition-penalty controls, and a token-probability view. The local server can return logprobs, which would let us look at calibration before and after training.
- **A blind comparison.** Run the held-out prompts through the base model and each add-on, shuffle the replies, and have Ming pick the best and worst of each without knowing which is which. That answers "is it better?" more fairly than one sample at a time, and the picks are exactly the data DPO needs.
- **Preference tuning or RL.** DPO on pairs of replies (one good, one worse), or small RL loops. A good first DPO target is stopping: the same reply twice, once ending cleanly (preferred) and once running on into a made-up next turn (rejected). It's narrow and easy to measure, by counting how many of 10 samples stop on their own. None of this is set up yet. When we get there, check which MLX trainers currently support DPO.

## Practical notes

- With 16 GB, only one model fits in memory at a time. The server holds one and swaps when the playground's model menu changes, which takes a few seconds. Training needs the server stopped.
- Don't edit `train.sh` while it's running. Bash reads a script as it goes, so an edit can change what the rest of the run does.
- Open the playground directly in Safari or Chrome, from this folder. Previews embedded in other apps may block its requests, and the page shows a notice when it's inside a frame. The add-on menu reads `adapters/index.js` next to the page, so a copy of the page opened from somewhere else only shows add-ons that have worked before plus Other folder.
- The models are cached in `~/.cache/huggingface`, outside this folder.
