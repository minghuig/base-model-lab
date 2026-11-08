"""Runs mlx-lm's LoRA trainer with the lab's chat format.

Each training example is a conversation (a list of messages). mlx-lm turns it
into text with the tokenizer's chat template, and Llama 3.1 base has none, so
this supplies one:

    <|begin_of_text|>User: {first message}

    Assistant: {first reply}

    User: {second message}

    Assistant: {last reply}<|end_of_text|>

A single exchange is just the first and last lines. The start and end tokens
are the base model's own start- and end-of-document tokens, which it learned in
pre-training, so "end of document" becomes "end of my reply". Only the last
reply gets one: that's where the server should stop, even when the earlier
turns make the conversation look like it's still going.

With mask_prompt on, only " {last reply}<|end_of_text|>" counts toward the
loss. Earlier turns are context, the way a chat app sends the whole
conversation each time and the model writes one reply.

It also applies the same tokenizer fix as the playground server: some model
conversions end every prompt with an end-of-document token or leave off the
start token.

It also reads one setting mlx-lm doesn't have: "epochs" in config.yaml, the
number of passes over the training data, which --epochs N overrides. It works
out the matching number of updates, so the run stays the right length when
the dataset changes.

Usage (train.sh runs this for you):
    python lab_launcher.py --config config.yaml [--epochs N]
"""

import sys

import mlx_lm.tokenizer_utils as tu
from tokenizers.processors import TemplateProcessing


def fix_special_tokens(tokenizer):
    """Make plain encoding add the start token only, never the end token."""
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


def make_chat_template(bos, eos):
    def render(messages, add_generation_prompt=False, **kwargs):
        text = bos
        for i, message in enumerate(messages):
            if message["role"] == "user":
                text += "User: " + message["content"] + "\n\nAssistant:"
            elif message["role"] == "assistant":
                last = i == len(messages) - 1
                text += " " + message["content"] + (eos if last else "\n\n")
            else:
                raise ValueError(f"Unexpected role in training data: {message['role']}")
        return text

    return render


_wrapper_init = tu.TokenizerWrapper.__init__


def _init(self, tokenizer, *args, **kwargs):
    _wrapper_init(self, tokenizer, *args, **kwargs)
    fix_special_tokens(tokenizer)
    self._chat_template = make_chat_template(tokenizer.bos_token or "", tokenizer.eos_token)
    self.has_chat_template = True


tu.TokenizerWrapper.__init__ = _init

def resolve_epochs(config_path, override=None):
    """Turns the lab's "epochs" setting into mlx-lm's "iters".

    One pass is every training conversation once: the number of lines in
    train.jsonl divided by batch_size, rounded up. If lr_schedule's arguments
    say "auto" for the number of decay steps, that becomes the updates left
    after warmup, so the learning rate reaches its end value on the last
    update. Returns the path of a resolved copy of the config, or the original
    path if there's nothing to resolve.
    """
    import math
    import os
    import tempfile

    import yaml
    from mlx_lm.lora import yaml_loader

    with open(config_path) as f:
        config = yaml.load(f, yaml_loader)
    epochs = config.pop("epochs", None)
    if override is not None:
        epochs = override
    if epochs is None:
        return config_path
    epochs = float(epochs)
    if epochs <= 0:
        raise SystemExit("epochs needs to be above zero.")

    data = os.path.join(os.path.dirname(os.path.abspath(config_path)), config.get("data", "data"), "train.jsonl")
    with open(data) as f:
        n = sum(1 for line in f if line.strip())
    batch = int(config.get("batch_size", 4))
    per_pass = math.ceil(n / batch)
    iters = max(1, int(round(epochs * per_pass)))
    config["iters"] = iters

    schedule = config.get("lr_schedule")
    if schedule and "auto" in schedule.get("arguments", []):
        steps = max(1, iters - int(schedule.get("warmup", 0)))
        schedule["arguments"] = [steps if a == "auto" else a for a in schedule["arguments"]]

    print(f"One epoch (a pass over all {n} training conversations, {batch} per update) is {per_pass} updates. "
          f"Training for {epochs:g} epoch{'' if epochs == 1 else 's'}: {iters} updates.")
    fd, path = tempfile.mkstemp(prefix="lab-config-", suffix=".yaml")
    with os.fdopen(fd, "w") as f:
        yaml.safe_dump(config, f)
    return path


if __name__ == "__main__":
    from mlx_lm.lora import main

    args = sys.argv[1:]
    override = None
    if "--epochs" in args:
        i = args.index("--epochs")
        override = args[i + 1]
        del args[i:i + 2]
    if "--config" in args:
        i = args.index("--config") + 1
        args[i] = resolve_epochs(args[i], override)
    elif override is not None:
        raise SystemExit("--epochs needs a --config file to adjust.")
    sys.argv = ["mlx_lm.lora"] + args
    main()
