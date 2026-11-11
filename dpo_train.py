"""Preference tuning (DPO) for the lab's add-ons. dpo.sh runs this.

It reads the pairs you picked in the playground's Compare mode
(prefs/pairs.jsonl: a prompt, the reply you chose, the reply you didn't), and
trains a copy of a starting add-on so your choices become more likely and the
others less likely.

How it works, in four steps:

1. Score a reply. A reply's score is the log of the probability the model
   gives it: the sum, over the reply's tokens, of the log-probability of each
   token given everything before it. These are the same numbers Show surprise
   colors. A reply that ended on its own includes the end-of-text token, so
   stopping is part of what's scored.

2. Score every pair with the starting add-on, once, before training. That
   frozen copy is the reference: training is measured as change from it.

3. For each pair, look at how much training has raised the chosen reply's
   score and the rejected reply's score, compared with the reference:

       margin = beta * ((chosen now - chosen before) - (rejected now - rejected before))

   The loss is -log(sigmoid(margin)). It's large when the margin is negative
   (the model has moved toward the reply you rejected) and shrinks toward
   zero as the margin grows, but more and more slowly. So the model gains
   little from pushing any one pair to extremes. Together with beta, that is
   the leash that keeps it close to the starting add-on and its voice.

4. Nudge the add-on's numbers to lower the loss, a few pairs at a time.

This is DPO (direct preference optimization). Classic RLHF trains a separate
reward model on the same pairs and then runs reinforcement learning against
it; DPO gets to a mathematically similar place directly from the pairs, with
only one model in memory.

Usage (dpo.sh runs this for you):
    python dpo_train.py --config dpo.yaml
"""

import argparse
import json
import math
import os
import random
import time

import lab_launcher  # noqa: F401  (applies the lab's tokenizer fix on import)
import mlx.core as mx
import mlx.nn as nn
import mlx.optimizers as optim
import yaml
from mlx.utils import tree_flatten, tree_map
from mlx_lm import load
from mlx_lm.lora import yaml_loader
from mlx_lm.tuner.trainer import grad_checkpoint
from mlx_lm.tuner.utils import linear_to_lora_layers

HERE = os.path.dirname(os.path.abspath(__file__))


def read_config(path):
    with open(path) as f:
        cfg = yaml.load(f, yaml_loader)
    defaults = {
        "beta": 0.1,
        "learning_rate": 1e-5,
        "epochs": 2,
        "pairs_per_update": 4,
        "valid_fraction": 0.1,
        "max_seq_length": 1024,
        "seed": 0,
        "grad_checkpoint": True,
    }
    for k, v in defaults.items():
        cfg.setdefault(k, v)
    for k in ("model", "start_adapter", "adapter_path", "pairs"):
        if not cfg.get(k):
            raise SystemExit(f"dpo.yaml needs a value for {k}.")
    return cfg


def lab_path(p):
    return p if os.path.isabs(p) else os.path.join(HERE, p)


def read_pairs(path):
    pairs = []
    with open(path) as f:
        for n, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                p = json.loads(line)
                if p["chosen"]["text"].strip() and p["rejected"]["text"].strip():
                    pairs.append(p)
            except (ValueError, KeyError, TypeError, AttributeError):
                print(f"(Skipping line {n} of {path}: it isn't a complete pair.)")
    return pairs


def tokenize_reply(tokenizer, prompt, reply, max_len):
    """Token ids for prompt + reply, and where the reply starts. A reply that
    ended on its own gets the end-of-text token, so stopping is scored too."""
    prompt_ids = tokenizer.encode(prompt)
    ids = tokenizer.encode(prompt + reply["text"])
    start = 0
    while start < min(len(prompt_ids), len(ids)) and prompt_ids[start] == ids[start]:
        start += 1
    start = max(start, 1)
    if reply.get("finish") == "stop":
        ids.append(tokenizer.eos_token_id)
    if len(ids) > max_len:
        ids = ids[:max_len]
    if start >= len(ids):
        return None
    return ids, start


def reply_logprob(model, ids, start):
    """Sum of log-probabilities of ids[start:], each given everything before it."""
    x = mx.array(ids[:-1])[None]
    targets = mx.array(ids[1:])[None]
    logits = model(x)
    token_lp = -nn.losses.cross_entropy(logits, targets, reduction="none")[0]
    return token_lp[start - 1 :].sum()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=os.path.join(HERE, "dpo.yaml"))
    cfg = read_config(ap.parse_args().config)
    random.seed(cfg["seed"])
    mx.random.seed(cfg["seed"])

    pairs_file = lab_path(cfg["pairs"])
    pairs = read_pairs(pairs_file)
    if len(pairs) < 2:
        raise SystemExit(f"Found {len(pairs)} usable pairs in {pairs_file}; collect more in the playground's Compare mode first.")

    start_dir = lab_path(cfg["start_adapter"])
    out_dir = lab_path(cfg["adapter_path"])

    # DPO measures change from the starting add-on, so the cleanest signal comes
    # from pairs that add-on wrote. Others still work; say how many there are.
    def short(x):
        return os.path.basename(str(x).rstrip("/")) if x else "no add-on"
    want = (short(cfg["model"]), short(start_dir))
    other = {}
    for p in pairs:
        got = (short(p.get("model")), short(p.get("adapter")))
        if got != want:
            other[got] = other.get(got, 0) + 1
    if other:
        listed = ", ".join(f"{n} from {m} + {a}" for (m, a), n in sorted(other.items(), key=lambda kv: -kv[1]))
        print(f"Note: {sum(other.values())} of {len(pairs)} pairs were written by something other than "
              f"{want[0]} + {want[1]} ({listed}). They still count, but pairs the starting add-on wrote teach it most directly.")
    with open(os.path.join(start_dir, "adapter_config.json")) as f:
        adapter_cfg = json.load(f)

    print(f"Loading {cfg['model']} with the add-on {os.path.basename(start_dir)}…")
    model, tokenizer = load(cfg["model"])
    model.freeze()
    linear_to_lora_layers(model, adapter_cfg["num_layers"], adapter_cfg["lora_parameters"])
    model.load_weights(os.path.join(start_dir, "adapters.safetensors"), strict=False)
    if cfg["grad_checkpoint"]:
        grad_checkpoint(model.layers[0])

    examples = []
    for p in pairs:
        c = tokenize_reply(tokenizer, p["prompt"], p["chosen"], cfg["max_seq_length"])
        r = tokenize_reply(tokenizer, p["prompt"], p["rejected"], cfg["max_seq_length"])
        if c and r:
            examples.append({"chosen": c, "rejected": r, "prompt": p["prompt"]})
    random.shuffle(examples)
    n_valid = int(len(examples) * cfg["valid_fraction"]) if len(examples) >= 10 else 0
    valid, train = examples[:n_valid], examples[n_valid:]
    print(f"{len(examples)} pairs: {len(train)} to train on, {len(valid)} held out to check against.")

    # Reference scores: the starting add-on, before any training.
    print("Scoring every reply with the starting add-on (the reference)…")
    t0 = time.time()
    model.eval()
    for ex in examples:
        rc = reply_logprob(model, *ex["chosen"])
        rr = reply_logprob(model, *ex["rejected"])
        mx.eval(rc, rr)
        ex["ref"] = (rc.item(), rr.item())
    print(f"Done in {time.time() - t0:.0f}s.")

    beta = cfg["beta"]

    def pair_loss(model, c_ids, c_start, r_ids, r_start, ref_c, ref_r):
        pc = reply_logprob(model, c_ids, c_start)
        pr = reply_logprob(model, r_ids, r_start)
        margin = beta * ((pc - ref_c) - (pr - ref_r))
        return -nn.log_sigmoid(margin), (margin, pc - ref_c, pr - ref_r)

    def run(ex, mdl):
        return pair_loss(mdl, *ex["chosen"], *ex["rejected"], *ex["ref"])

    loss_and_grad = nn.value_and_grad(model, lambda m, ex: run(ex, m))

    def evaluate(items):
        if not items:
            return None
        model.eval()
        tot = {"loss": 0.0, "acc": 0, "margin": 0.0, "dc": 0.0, "dr": 0.0}
        for ex in items:
            loss, (margin, dc, dr) = run(ex, model)
            mx.eval(loss, margin, dc, dr)
            tot["loss"] += loss.item()
            tot["acc"] += margin.item() > 0
            tot["margin"] += margin.item()
            tot["dc"] += dc.item()
            tot["dr"] += dr.item()
        k = len(items)
        return {key: v / k for key, v in tot.items()}

    def report(tag, m):
        print(f"  {tag}: loss {m['loss']:.3f} | prefers your pick {m['acc'] * 100:.0f}% | "
              f"margin {m['margin']:+.3f} | chosen score {m['dc']:+.2f}, rejected {m['dr']:+.2f} (change from start)")

    optimizer = optim.Adam(learning_rate=cfg["learning_rate"])
    per_update = max(1, int(cfg["pairs_per_update"]))
    updates_per_epoch = math.ceil(len(train) / per_update)
    print(f"\nTraining: {cfg['epochs']} epoch(s), {updates_per_epoch} updates each, {per_update} pairs per update, "
          f"beta {beta}, learning rate {cfg['learning_rate']}.")
    print("At the start, every margin is 0 and the loss is log(2) = 0.693, because the model hasn't moved yet.")
    print("Watch the held-out pairs: if 'prefers your pick' rises there, it's learning what you like, not just these pairs.\n")

    os.makedirs(out_dir, exist_ok=True)

    def save(path):
        weights = dict(tree_flatten(model.trainable_parameters()))
        mx.save_safetensors(path, weights)

    update = 0
    t0 = time.time()
    for epoch in range(1, int(cfg["epochs"]) + 1):
        random.shuffle(train)
        for u in range(updates_per_epoch):
            chunk = train[u * per_update : (u + 1) * per_update]
            model.train()
            grads_sum, stats = None, []
            for ex in chunk:
                (loss, (margin, dc, dr)), grads = loss_and_grad(model, ex)
                grads_sum = grads if grads_sum is None else tree_map(mx.add, grads_sum, grads)
                mx.eval(loss, margin, grads_sum)
                stats.append((loss.item(), margin.item()))
            grads_avg = tree_map(lambda g: g / len(chunk), grads_sum)
            optimizer.update(model, grads_avg)
            mx.eval(model.trainable_parameters(), optimizer.state)
            update += 1
            if update % 5 == 0 or u == updates_per_epoch - 1:
                avg_loss = sum(s[0] for s in stats) / len(stats)
                acc = sum(s[1] > 0 for s in stats) / len(stats)
                print(f"epoch {epoch} update {update}: loss {avg_loss:.3f}, prefers your pick on {acc * 100:.0f}% of this update's pairs "
                      f"({time.time() - t0:.0f}s)")
        m = evaluate(train)
        report(f"epoch {epoch}, training pairs", m)
        if valid:
            report(f"epoch {epoch}, held out", evaluate(valid))
        save(os.path.join(out_dir, f"epoch{epoch}_adapters.safetensors"))

    save(os.path.join(out_dir, "adapters.safetensors"))
    adapter_cfg = dict(adapter_cfg)
    adapter_cfg["dpo"] = {
        "start_adapter": cfg["start_adapter"],
        "pairs": len(examples),
        "beta": beta,
        "learning_rate": cfg["learning_rate"],
        "epochs": cfg["epochs"],
        "pairs_per_update": per_update,
    }
    with open(os.path.join(out_dir, "adapter_config.json"), "w") as f:
        json.dump(adapter_cfg, f, indent=4)
    print(f"\nSaved the add-on to {out_dir}.")


if __name__ == "__main__":
    main()
