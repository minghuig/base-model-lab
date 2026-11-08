"""Builds data/train.jsonl and data/valid.jsonl from the conversation batches in
this folder (b01_*.py ... b10_*.py), and prints quality checks: counts, reply
lengths, duplicate prompts, and a scan for AI tics the voice should avoid.

Run from the repo root:
    python3 dataset_src/build_dataset.py

The split is seeded, so rebuilding unchanged batches gives the same files.
Three conversations per batch are held out for validation.
"""

import importlib.util, json, random, re, glob, os, statistics, collections

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "data")

batches = []
for path in sorted(glob.glob(os.path.join(HERE, "b[0-9][0-9]_*.py"))):
    spec = importlib.util.spec_from_file_location(os.path.basename(path)[:-3], path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    batches.append((os.path.basename(path)[:-3], [(p.strip(), c.strip()) for p, c in mod.EXAMPLES]))

all_ex = [(b, p, c) for b, exs in batches for p, c in exs]
print("per batch:", {b: len(e) for b, e in batches}, "| total:", len(all_ex))

# duplicates
prompts = collections.Counter(p.lower() for _, p, _ in all_ex)
print("duplicate prompts:", [p for p, n in prompts.items() if n > 1])

# lengths
wc = [len(c.split()) for _, _, c in all_ex]
print("reply words: min", min(wc), "median", statistics.median(wc), "max", max(wc), "| total words", sum(wc))
print("short replies (<15 words):", sum(w < 15 for w in wc), "| long (>200):", sum(w > 200 for w in wc))

# tics and banned words
banned = [r"\bdelve", r"\btapestry", r"great question", r"in conclusion", r"i hope this helps", r"^certainly",
          r"as an ai", r"\barithmetic", r"\btestament to", r"\bnavigate the", r"\brealm\b", r"it's important to note",
          r"\bjourney\b", r"\bunlock", r"\bembark", r"\bvibrant\b", r"\bfoster\b", r"\bcrucial\b", r"\bleverage\b"]
for pat in banned:
    hits = [(b, p[:40]) for b, p, c in all_ex if re.search(pat, c, re.I | re.M)]
    if hits: print(f"  '{pat}':", hits)
print("em dashes in replies:", sum(c.count("—") for _, _, c in all_ex))
print("replies starting with 'I ':", sum(c.startswith("I ") for _, _, c in all_ex))
starts = collections.Counter(c.split()[0].strip('"').lower() for _, _, c in all_ex)
print("most common first words:", starts.most_common(8))
print("bullet/markdown lines:", sum(bool(re.search(r"^\s*([-*•]|#+)\s", c, re.M)) for _, _, c in all_ex))
print("leading/trailing whitespace issues:", sum(c != c.strip() or p != p.strip() for _, p, c in all_ex))

# split: 3 held out per batch, chosen at random
random.seed(7)
train, valid = [], []
for b, exs in batches:
    idx = list(range(len(exs))); random.shuffle(idx)
    hold = set(idx[:3])
    for i, (p, c) in enumerate(exs):
        (valid if i in hold else train).append({"prompt": p, "completion": c})
random.shuffle(train)
os.makedirs(OUT, exist_ok=True)
for name, rows in (("train", train), ("valid", valid)):
    with open(os.path.join(OUT, f"{name}.jsonl"), "w") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
print("train:", len(train), "valid:", len(valid))
print("held out:", [r["prompt"][:45] for r in valid])
