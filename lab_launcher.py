"""Runs mlx-lm's LoRA trainer with the lab's chat format.

Each training example is a prompt/completion pair. mlx-lm turns a pair into
text with the tokenizer's chat template, and Llama 3.1 base has none, so this
supplies one:

    <|begin_of_text|>User: {prompt}

    Assistant: {completion}<|end_of_text|>

The start and end tokens are the base model's own start- and end-of-document
tokens, which it learned in pre-training, so "end of document" becomes "end of
my reply". With mask_prompt on, only " {completion}<|end_of_text|>" counts
toward the loss: the model is graded on answering, not on imitating users.

It also applies the same tokenizer fix as the playground server: some model
conversions end every prompt with an end-of-document token or leave off the
start token.

Usage (train.sh runs this for you):
    python lab_launcher.py --config config.yaml
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
        for message in messages:
            if message["role"] == "user":
                text += "User: " + message["content"] + "\n\nAssistant:"
            elif message["role"] == "assistant":
                text += " " + message["content"] + eos
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

if __name__ == "__main__":
    from mlx_lm.lora import main

    sys.argv = ["mlx_lm.lora"] + sys.argv[1:]
    main()
