# Base model lab

Hands-on experiments with language models on a 16 GB Apple silicon MacBook Pro: what a model is like before any post-training, and what a little post-training does to it.

- **A playground** (`base-model-playground.html`). Write the start of a document and a base model continues it. It works with a server on this Mac, OpenRouter or Featherless. With the local server, **Show surprise** colors each token by how unlikely the model found it.
- **A local server** (`start-base-model.sh`). It runs Mistral Nemo 12B base and Llama 3.1 8B base with mlx-lm, with or without a trained add-on.
- **A fine-tune** (`train.sh`). A LoRA add-on teaches Llama 3.1 8B base to answer as an assistant that writes plainly and well, trained on 438 conversations written for this.

## Quick start

Start the server, then open `base-model-playground.html` in Safari or Chrome and choose **Provider: Server on this Mac**. The first run installs mlx-lm and asks before downloading about 12 GB of models.

```
bash ~/Documents/base-model-lab/start-base-model.sh
```

To train an add-on, first stop the server with Control-C, because training needs the memory. One pass over the data takes about 15 minutes. Add `--epochs 2` for two passes.

```
bash ~/Documents/base-model-lab/train.sh
```

Then restart the server and pick the new add-on from the playground's **Trained add-on** menu. Leave **Stop at** empty, and prompt it in the training format:

```
User: what's a fun activity i can do today?

Assistant:
```

To use a snapshot from partway through a run instead, turn it into an add-on with `pick_checkpoint.sh`. For example, `pick_checkpoint.sh 150` takes update 150 of the current run, and `pick_checkpoint.sh 100 prose` takes update 100 of the run in `adapters/prose`.

## Files

| Path | What it is |
|---|---|
| `base-model-playground.html` | The playground: one HTML file, no build step. API keys stay in the browser. |
| `start-base-model.sh`, `server_launcher.py` | Install, download, and start `mlx_lm.server` with the lab's fixes and scoring. |
| `train.sh`, `lab_launcher.py`, `config.yaml` | Train an add-on with `mlx_lm.lora`, in the lab's chat format. |
| `pick_checkpoint.sh`, `list_adapters.sh` | Turn a snapshot into an add-on, and keep the playground's add-on menu up to date. |
| `dataset_src/` | The conversations in batches by category, and `build_dataset.py`, which checks them and writes `data/`. |
| `data/` | The generated training and held-out sets. Don't edit them by hand. |
| `runs/` | What each training run did and showed, with its log. |
| `docs/` | How everything works, and ideas for what's next. |

Trained add-ons go in `adapters/`, which is git-ignored.

## More

- [How it works](docs/how-it-works.md): the training format, the dataset, training settings, the surprise view, and the fixes on top of mlx-lm.
- [Training runs](runs/README.md): each run's settings, results, and what playing with it showed.
- [Ideas](docs/ideas.md): what to try next.

## Practical notes

- With 16 GB, only one model fits in memory at a time. The server swaps models when the playground asks for a different one, and training needs the server stopped.
- Don't edit `train.sh` while it's running. Bash reads a script as it goes.
- Open the playground straight from this folder. Previews inside other apps may block its requests, and the add-on menu reads `adapters/index.js` next to the page.
