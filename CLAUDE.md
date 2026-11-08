# Notes for Claude

Start with README.md for the overview. Then:
- docs/how-it-works.md: training format, dataset, training settings, the
  surprise view, and the mlx-lm patches.
- runs/README.md: every training run's settings, results, and what playing
  with it showed. Read this before planning the next run.
- docs/ideas.md: what to try next.

- Ming runs the scripts herself in Terminal on a 16 GB Apple silicon Mac. Give
  her the exact command to run, with the full ~/Documents/base-model-lab/ path.
- Never edit train.sh while a training run is going: bash reads the script as
  it runs. Check train-log.txt; a run is over once it shows the last update's
  "save" line and the 100% progress bar.
- Only one model fits in memory. Training needs the server stopped, and the
  server swaps models rather than holding two.
- data/*.jsonl is generated. Edit dataset_src/b*.py, then run
  python3 dataset_src/build_dataset.py and read its quality report. Items are
  (user, reply) pairs or lists of alternating turns; only the last reply is
  trained. Add new batches with a higher number so earlier held-out
  conversations stay put.
- Give each training run its own adapter_path in config.yaml (adapters/prose,
  adapters/prose-v2, ...). Run length is set by "epochs" (or
  train.sh --epochs N), which lab_launcher.py turns into mlx-lm's "iters" and
  the lr_schedule's "auto" decay steps; don't set iters by hand.
  pick_checkpoint.sh and list_adapters.sh keep the playground's add-on menu
  in sync.
- Keep the playground a single self-contained HTML file with no build step.
  API keys stay in the browser's localStorage, never in this repo.
- The launchers (server_launcher.py, lab_launcher.py) patch mlx-lm internals,
  written against mlx-lm 0.32.2. If mlx-lm is upgraded, check that the server
  still prints its tokenizer message, then try one continuation and one
  Show surprise.
- You can test server and training changes without the Mac; see "Testing
  changes without the Mac" in docs/how-it-works.md.
- After a training run worth keeping, save a cleaned copy of train-log.txt in
  runs/ (strip the color codes and progress bars), and add its results to
  runs/README.md, including what samples in the playground showed. Held-out loss
  alone has misled us before.
