"""Builds data/train.jsonl and data/valid.jsonl from the conversation batches in
this folder (b01_*.py, b02_*.py, ...), and prints quality checks: counts, reply
lengths, duplicates, and a scan for AI tics the voice should avoid.

Run from the repo root:
    python3 dataset_src/build_dataset.py

Each batch file defines EXAMPLES, a list whose items are either
  - a (user, assistant) pair, for a single exchange, or
  - a list of turns that alternate user, assistant, user, assistant, ...
    and end with an assistant reply, for a longer conversation.

Every conversation becomes one line of {"messages": [...]}. Training only
scores the last reply; earlier turns are context (see lab_launcher.py).

The split is seeded, and batches are processed in name order, so adding a new
batch leaves the held-out conversations of the earlier batches unchanged.
Three conversations per batch are held out for validation.
"""

import importlib.util, json, random, re, glob, os, statistics, collections

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "data")


def turns_of(item, batch):
    turns = [t.strip() for t in item]
    ok = len(turns) >= 2 and len(turns) % 2 == 0 and all(turns)
    if not ok:
        raise SystemExit(f"{batch}: a conversation needs alternating user/assistant turns ending with the assistant: {turns[:1]}")
    return turns


batches = []
for path in sorted(glob.glob(os.path.join(HERE, "b[0-9][0-9]_*.py"))):
    name = os.path.basename(path)[:-3]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    batches.append((name, [turns_of(item, name) for item in mod.EXAMPLES]))

convs = [(b, t) for b, items in batches for t in items]
user_turns = [(b, u) for b, t in convs for u in t[0::2]]
replies = [(b, a) for b, t in convs for a in t[1::2]]          # every assistant turn, context included
finals = [(b, t[-1]) for b, t in convs]                        # the replies training scores

multi = sum(len(t) > 2 for _, t in convs)
print("per batch:", {b: len(e) for b, e in batches})
print("conversations:", len(convs), "| single exchange:", len(convs) - multi, "| multi-turn:", multi,
      "| assistant turns:", len(replies))

# duplicates: the same opening message, or the same whole conversation
openers = collections.Counter(t[0].lower() for _, t in convs)
print("duplicate opening messages:", [p for p, n in openers.items() if n > 1])

# the headline test question must stay out of training
leaks = [(b, u[:60]) for b, u in user_turns if re.search(r"\bfun\b", u, re.I) and re.search(r"\btoday\b", u, re.I)]
print("turns that look like the held-out 'fun activity today' question:", leaks)

# lengths of the scored replies
wc = [len(a.split()) for _, a in finals]
print("scored reply words: min", min(wc), "median", statistics.median(wc), "max", max(wc), "| total words", sum(wc))
print("short replies (<15 words):", sum(w < 15 for w in wc), "| long (>200):", sum(w > 200 for w in wc))

# tics and banned words, in every assistant turn
banned = [r"\bdelve", r"\btapestry", r"great question", r"in conclusion", r"i hope this helps", r"^certainly",
          r"as an ai", r"\barithmetic", r"\btestament to", r"\bnavigate the", r"\brealm\b", r"it's important to note",
          r"\bjourney\b", r"\bunlock", r"\bembark", r"\bvibrant\b", r"\bfoster\b", r"\bcrucial\b", r"\bleverage\b",
          r"\bas a language model\b", r"\babsolutely!", r"^great[,!]"]
for pat in banned:
    hits = [(b, a[:40]) for b, a in replies if re.search(pat, a, re.I | re.M)]
    if hits: print(f"  '{pat}':", hits)
print("em dashes in replies:", sum(a.count("—") for _, a in replies))
print("replies starting with 'I ':", sum(a.startswith("I ") for _, a in finals))
starts = collections.Counter(a.split()[0].strip('"').lower() for _, a in finals)
print("most common first words:", starts.most_common(8))
print("bullet/markdown lines:", sum(bool(re.search(r"^\s*([-*•]|#+)\s", a, re.M)) for _, a in replies))
print("turns that look like a transcript inside a turn:",
      [(b, a[:40]) for b, a in replies + user_turns if re.search(r"^(User|Assistant):", a, re.M)])

# split: 3 held out per batch, chosen at random
random.seed(7)
train, valid = [], []
for b, items in batches:
    idx = list(range(len(items))); random.shuffle(idx)
    hold = set(idx[:3])
    for i, turns in enumerate(items):
        roles = ["user", "assistant"] * (len(turns) // 2)
        row = {"messages": [{"role": r, "content": c} for r, c in zip(roles, turns)]}
        (valid if i in hold else train).append(row)
random.shuffle(train)
os.makedirs(OUT, exist_ok=True)
for name, rows in (("train", train), ("valid", valid)):
    with open(os.path.join(OUT, f"{name}.jsonl"), "w") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
print("train:", len(train), "valid:", len(valid))
print("held out:", [r["messages"][-2]["content"][:45] for r in valid])
