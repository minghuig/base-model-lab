"""Starts mlx_lm.server with the lab's fixes. start-base-model.sh runs this.

1. Keep the first word's leading space. The server drops the space before the
   first word it sends back. That suits chat replies, but here it glues the
   first word onto your text ("species of" + " owl" comes back as
   "species ofowl").

2. Fix special tokens. Some model conversions get them wrong. mlx-community's
   Mistral Nemo puts an end-of-document token after every prompt, so the model
   thinks your document is finished and starts a new, unrelated one; its
   Llama 3.1 8B leaves off the start-of-document token the model was trained
   with.

3. Score a given text ("surprise" view). A /v1/completions request with a
   "lab_score" string doesn't generate anything. It returns, for every token of
   that string, the probability the model gave it given everything before it,
   the model's top guesses, and the probability that the document ends right
   after the string. This is the same quantity training scores (the loss is the
   average of minus the log of these probabilities), and it's what the
   playground's "Show surprise" button draws.

Each fix prints a line in parentheses if it can't be applied, and the server
still starts. These patches reach into mlx-lm internals (written against
mlx-lm 0.32), so an upgrade could break them.
"""

import sys

import mlx_lm.tokenizer_utils as tu

# 1. Keep the first word's leading space.
try:
    tu.BPEStreamingDetokenizer._maybe_trim_space = lambda self, text: text
    _spm_init = tu.SPMStreamingDetokenizer.__init__
    tu.SPMStreamingDetokenizer.__init__ = (
        lambda self, tokenizer, trim_space=True: _spm_init(self, tokenizer, trim_space=False)
    )
except Exception as e:
    print(f"(Couldn't keep the first word's leading space: {e})")

# 2. Start-of-document token on, end-of-document token off.
try:
    from tokenizers.processors import TemplateProcessing

    _wrapper_init = tu.TokenizerWrapper.__init__

    def _init(self, tokenizer, *args, **kwargs):
        _wrapper_init(self, tokenizer, *args, **kwargs)
        try:
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
            print("(Fixed this model's tokenizer so prompts start with a start-of-document token and don't end with an end-of-document one.)")
        except Exception as e:
            print(f"(Couldn't check the tokenizer's end-of-document setting: {e})")

    tu.TokenizerWrapper.__init__ = _init
except Exception as e:
    print(f"(Couldn't patch the tokenizer: {e})")

# 3. Scoring. The request goes through the server's own queue, so it runs on the
# generation thread, after any generation in progress, with the requested model
# and add-on loaded exactly as a normal request would load them.
MAX_SCORE_TOKENS = 1500
TOP_K = 5

try:
    import json
    from queue import Queue

    import mlx.core as mx
    import mlx_lm.server as srv

    def _score(model, tokenizer, prompt, text, stream):
        prompt_ids = list(tokenizer.encode(prompt))
        full_ids = list(tokenizer.encode(prompt + text))
        if len(full_ids) > MAX_SCORE_TOKENS:
            raise ValueError(f"That's {len(full_ids)} tokens; the surprise view handles up to {MAX_SCORE_TOKENS}.")
        # Where the scored text starts. Usually right after the prompt's tokens;
        # if the text starts mid-word, its first token may also cover the end
        # of the prompt.
        n = 0
        while n < min(len(prompt_ids), len(full_ids)) and prompt_ids[n] == full_ids[n]:
            n += 1
        start = max(n, 1)
        if start >= len(full_ids):
            raise ValueError("There's no text to score.")

        with mx.stream(stream):
            logits = model(mx.array(full_ids)[None])[0]
            # Position i predicts token i + 1; the last position predicts what
            # would come after the text.
            logits = logits[start - 1:].astype(mx.float32)
            logprobs = logits - mx.logsumexp(logits, axis=-1, keepdims=True)
            targets = mx.array(full_ids[start:])
            actual = mx.take_along_axis(logprobs[:-1], targets[:, None], axis=-1)[:, 0]
            ranks = (logprobs[:-1] > actual[:, None]).sum(axis=-1) + 1
            top_ids = mx.argpartition(-logprobs, kth=TOP_K - 1, axis=-1)[:, :TOP_K]
            top_lps = mx.take_along_axis(logprobs, top_ids, axis=-1)
            eos_ids = sorted(getattr(tokenizer, "eos_token_ids", None) or [tokenizer.eos_token_id])
            end_lp = mx.logsumexp(logprobs[-1][mx.array(eos_ids)])
            mx.eval(actual, ranks, top_ids, top_lps, end_lp)

        actual, ranks = actual.tolist(), ranks.tolist()
        top_ids, top_lps = top_ids.tolist(), top_lps.tolist()

        def decode(ids):
            try:
                return tokenizer.decode(ids, clean_up_tokenization_spaces=False)
            except TypeError:
                return tokenizer.decode(ids)

        def tok_text(i):
            return decode([i])

        tokens = []
        prev = decode(full_ids[:start])
        for k, j in enumerate(range(start, len(full_ids))):
            cur = decode(full_ids[: j + 1])
            if cur.endswith("�"):
                piece = ""  # part of a character that the next token finishes
            else:
                piece = cur[len(prev):]
                prev = cur
            alts = sorted(zip(top_lps[k], top_ids[k]), reverse=True)
            tokens.append({
                "text": piece,
                "logprob": actual[k],
                "rank": ranks[k],
                "top": [{"text": tok_text(i), "logprob": lp} for lp, i in alts],
            })
        end_alts = sorted(zip(top_lps[-1], top_ids[-1]), reverse=True)
        return {
            "tokens": tokens,
            "end": {
                "logprob": end_lp.item(),
                "top": [{"text": tok_text(i), "logprob": lp} for lp, i in end_alts],
            },
            # Characters at the end of the prompt that the first scored token
            # also covers (when the text starts in the middle of a word).
            "overlap": len(decode(prompt_ids)) - len(decode(full_ids[:start])),
        }

    _serve_single = srv.ResponseGenerator._serve_single

    def _serve_single_or_score(self, request, stream):
        rqueue, req, args = request
        text = getattr(req, "lab_score", None)
        if not isinstance(text, str):
            return _serve_single(self, request, stream)
        try:
            result = _score(self.model_provider.model, self.model_provider.tokenizer, req.prompt, text, stream)
            result["model"] = args.model.model
            result["adapter"] = args.model.adapter
            rqueue.put({"lab_score": result})
        except Exception as e:
            rqueue.put(e)

    srv.ResponseGenerator._serve_single = _serve_single_or_score

    _handle_text_completions = srv.APIHandler.handle_text_completions

    def _handle_text_completions_or_score(self):
        req = _handle_text_completions(self)
        text = self.body.get("lab_score")
        if isinstance(text, str):
            req.lab_score = text
        return req

    srv.APIHandler.handle_text_completions = _handle_text_completions_or_score

    _handle_completion = srv.APIHandler.handle_completion

    def _handle_completion_or_score(self, request, stop_words):
        if not isinstance(getattr(request, "lab_score", None), str):
            return _handle_completion(self, request, stop_words)
        try:
            # A seed makes the request "not batchable", which sends it to
            # _serve_single on the generation thread, where it's scored.
            args = srv.GenerationArguments(
                model=srv.ModelDescription(
                    model=self.requested_model,
                    draft=getattr(self, "requested_draft_model", None),
                    adapter=self.adapter,
                ),
                sampling=srv.SamplingArguments(
                    temperature=0.0, top_p=1.0, top_k=0, min_p=0.0,
                    xtc_probability=0.0, xtc_threshold=0.0,
                ),
                logits=srv.LogitsProcessorArguments(
                    logit_bias=None, repetition_penalty=1.0, repetition_context_size=20,
                    presence_penalty=0.0, presence_context_size=20,
                    frequency_penalty=0.0, frequency_context_size=20,
                ),
                stop_words=[], max_tokens=1, num_draft_tokens=0,
                logprobs=False, top_logprobs=-1, seed=0, chat_template_kwargs=None,
            )
            rqueue = Queue()
            self.response_generator.requests.put((rqueue, request, args))
            wait = getattr(self.response_generator, "_await_response", None)
            result = wait(rqueue) if wait else rqueue.get()
            if isinstance(result, Exception):
                raise result
            body, status = result, 200
        except Exception as e:
            body, status = {"error": str(e)}, 400
        self._set_completion_headers(status)
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    srv.APIHandler.handle_completion = _handle_completion_or_score
except Exception as e:
    print(f"(Couldn't add the surprise view to the server: {e})")

from mlx_lm.server import main

sys.argv = ["mlx_lm.server"] + sys.argv[1:]
main()
