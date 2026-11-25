# Where we left off, and what's next

## Where we left off (2026-11-24)

- **Latest add-on:** `nemo-prose-v2-dpo2`, from DPO run 3. It started from `nemo-prose-v2` (SFT run 7) and trained on 165 pairs: 53 Ming picked and 112 Claude picked.
- **How add-ons are compared:** the 18 prompts in `runs/probe-prompts.json`, 3 samples each at temperature 0.7. The main number is how often a reply doesn't answer as the assistant. Llama `prose-v3` does that in 1 of 54 replies, `nemo-prose-v2` in 11, and `nemo-prose-v2-dpo2` in 9.
- **What still fails on Nemo:**
  - Venting gets a non sequitur. "ugh i said something dumb in a meeting…" is 0 of 3 on every Nemo add-on.
  - "what's 12 squared" gets "About 1,440." This started with run 7.
  - Joke-shaped questions ("why do bulls get angry when they see red") still sometimes get a joke.
  - Any board game question gets Patchwork, because the training data has one board game conversation.
- **What we learned:** a few dozen SFT conversations (`b16`) or a few hundred DPO pairs fix what they show and little else. A second pass over the SFT data overfits at once (run 6). DPO needs small steps: 2e-5 wrecked the model (DPO run 1), and 3e-6 to 5e-6 for one pass is safe.
- **Everything is recorded** in [runs/README.md](../runs/README.md): each run, each comparison, and what went wrong.

## What to try next

- **A concentrated dose on one habit.** Write about 100 prompts that are all variations of one stubborn failure, such as venting messages. Have Claude sample three replies each and pick, then run DPO. This tests whether many pairs close to a failure fix it, where 165 pairs spread over everything didn't. It's the most direct follow-up.
- **Find out what broke "12 squared".** Runs 4 and 5 got it right; run 7 and both DPO add-ons say "About 1,440." Something in `b16` or in the `b14` short-answer batch is the likely cause. Check which training replies start with "About", and try a handful of plain arithmetic examples.
- **Fix the Patchwork template.** Add a few more board game conversations that recommend different games, so one reply stops standing in for the whole topic. It's a small, clear test of "one example becomes the template".
- **A second DPO round on the DPO add-on.** Collect pairs written by `nemo-prose-v2-dpo2` itself and train from it. Each round then works on what the current model actually gets wrong, which is how preference tuning is usually repeated.
- **Settle the run 5 against run 7 question.** Their held-out losses (1.751 and 1.786) were measured on different held-out sets. Score both add-ons on the original 45 conversations to see whether `b16` cost anything.
- **Turn the probes into one command.** Claude runs them today by driving the server from the Claude desktop app's browser panel and judging the replies by reading them. A script that samples the probes and saves the replies to a file would let Ming run them, and would keep the replies; today they live only in that browser.
- **Lower the temperature.** At 0.3, `nemo-prose-v2` wrote the pigeon story 3 of 3 times and stopped giving odd answers to personal questions. Some drift is sampling noise that a lower setting removes for free.
- **A blind comparison.** Show replies from two add-ons side by side without saying which is which, and have Ming pick. Compare mode could do this with two add-ons in place of two samples from one.
- **Three-way comparison.** The same prompts on the base model with the plain `User:` / `Assistant:` format, the base model with a written style header, and a trained add-on. This tests how much of a personality a prompt alone can buy.
- **Playground additions.** Top-p and repetition-penalty controls, which would also tame the Patchwork loops. Comparing two add-ons in the surprise view.
