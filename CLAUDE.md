# Notes for Claude

Start with README.md: it explains the parts, the training format, the mlx-lm
patches, and results so far.

- Ming runs the scripts herself in Terminal on a 16 GB Apple silicon Mac. Give
  her the exact command to run, with the full ~/Documents/base-model-lab/ path.
- Never edit train.sh while a training run is going: bash reads the script as
  it runs. Check train-log.txt; a run is over once it shows the last update's
  "save" line and the 100% progress bar.
- Only one model fits in memory. Training needs the server stopped, and the
  server swaps models rather than holding two.
- data/*.jsonl is generated. Edit dataset_src/b*.py, then run
  python3 dataset_src/build_dataset.py and read its quality report.
- Keep the playground a single self-contained HTML file with no build step.
  API keys stay in the browser's localStorage, never in this repo.
- The launchers patch mlx-lm internals. If mlx-lm is upgraded, check that the
  server still prints its tokenizer message, then try one continuation.
- After a training run worth keeping, save a cleaned copy of train-log.txt in
  runs/ (strip the color codes and progress bars), and add its results to the
  README.
