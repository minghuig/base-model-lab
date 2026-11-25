# Training runs

Each run trains a fresh add-on from the base model, in its own folder under `adapters/`. Its log is in this folder. Every run so far uses the same LoRA settings (see [How it works](../docs/how-it-works.md#training-settings)), so the differences come from the data, the run length and the learning rate.

Held-out loss is only comparable between runs that use the same held-out set, which grows when batches are added. Samples in the playground, and Show surprise on the same text with each add-on, compare any two runs.

## Run 1, 2026-11-07: `adapters/prose`

Settings: 312 conversations (b01 to b10), 282 for training and 30 held out. Batch 2, constant learning rate 2e-5, 450 updates. One pass over the training set is 141 updates, so this was a bit over three passes. It took about 28 minutes. Log: [2026-11-07-prose-450-log.txt](2026-11-07-prose-450-log.txt).

| Update | start | 50 | **100** | 150 | 200 | 250 | 300 | 350 | 400 | 450 |
|---|---|---|---|---|---|---|---|---|---|---|
| Held-out loss | 2.379 | 1.855 | **1.796** | 1.813 | 1.962 | 2.038 | 2.646 | 2.437 | 2.494 | 2.866 |

Average training loss was 1.93 on the first pass, 1.04 on the second and 0.36 on the third. It fell to about 0.1 by the end.

What it means: the add-on learned the voice quickly. Held-out loss fell from 2.38 to 1.80 within the first pass. After that it began memorizing. Training loss drops sharply each time a pass starts over (1.83 at update 140, 1.37 at 150), because the model is seeing replies it has seen before. Meanwhile held-out loss rises. The best snapshot is update 100, `adapters/prose-step100`.

Playing with update 100 in the playground showed what the loss numbers don't:

- **It didn't reliably stop.** With no stop string, it often ran on into a made-up next `User:` turn and kept going. Update 450 did the same.
- **It talked as if it were a person.** "The fresh air never fails to lift my spirits," "a few suggestions I've been meaning to read myself." Only 3 of the 312 conversations touched on what the assistant is.
- **It invented the user's surroundings.** Asked for a fun activity, it described a specific park, the ducks, a food truck that "will likely be there for at least another hour."
- **It overdid the style and the length.** It got lush rather than plain, and one reply ran 229 words when the longest training reply is 169.
- **The voice faded over turns.** By a made-up third turn it was writing markdown bullet lists, which appear nowhere in the data.
- **The polish made made-up facts more convincing.** It recommended a Stephen Baxter novel that doesn't seem to exist and misdescribed *The Overstory*.

It also showed that held-out loss isn't a judge of quality. Update 450's first reply read better than update 100's, even though its held-out loss was much worse. An overtrained model bets heavily on its own favorite phrasings, and log loss punishes confident wrong bets on held-out text, while sampling still draws from those favorite phrasings.

## Run 2, 2026-11-07: `adapters/prose-v2`

Why: training longer on the same data would only memorize it, so run 2 changed the data instead. It added b11 to b14, about 100 conversations aimed at stopping, identity, grounding and keeping the voice across turns: 412 in all, 370 for training and 42 held out. Otherwise it matched run 1, except for 300 updates with a held-out score and a snapshot every 25. One pass is 185 updates. It took about 22 minutes. Log: [2026-11-07-prose-v2-300-log.txt](2026-11-07-prose-v2-300-log.txt).

| Update | start | 25 | 50 | 75 | 100 | 125 | 150 | **175** | 200 | 225 | 250 | 275 | 300 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Held-out loss | 2.452 | 1.907 | 1.877 | 1.837 | 1.821 | 1.814 | 1.810 | **1.797** | 1.975 | 1.956 | 2.004 | 1.993 | 1.983 |

Average training loss was 1.92 over the first pass and 1.08 over the second. It fell from 1.85 at update 180 to 0.92 at update 200, right after the second pass began.

What it means: held-out loss fell steadily through the first pass and jumped as soon as the second began. That's the same memorizing pattern as run 1, easier to see with a score every 25 updates. In both runs, the turn came at the end of the first pass. Before it, every update is on a conversation the model hasn't seen; after it, every update is a repeat. The best snapshot is update 175, `adapters/prose-v2-step175`. Its starting loss was higher than run 1's (2.45 against 2.38), probably because the new held-out conversations, like questions about the assistant itself, are harder for the untrained model.

Playing with update 175:

- **It fixed the stopping.** It ended after its reply instead of making up the next `User:` turn. That's the multi-turn conversations, where only the last reply ends with end-of-text.
- **It overcorrected on identity.** It opened ordinary questions with disclaimers nobody asked for. Asked "what is a delicious food," it said "I don't have a mouth or a stomach, so I can't taste anything, but…", nearly the shape of the b12 pizza example. The cause: 45 conversations (b12 and b13) showed the assistant stating a limit, and almost none showed a personal-sounding question that should just be answered. A model can't learn where a line is from one side of it, and neither can the held-out loss, since its identity questions were all ones where a disclaimer is right.
- **The voice drifted toward generic chatbot.** It used markdown bullets and stock phrases like "I hope you enjoy them," which appear nowhere in the data. The more the model sees itself as an AI assistant, the more it borrows that character's habits from web text.
- **Explicit-story requests got improvised refusals.** These were rare in run 1 and fairly common in run 2. They came with body-based reasons ("I don't have any sex organs"), and sometimes the model wrote something story-like anyway. No conversation involves content refusals. The model seems to have combined the base model's picture of how AI assistants answer such requests with run 2's "I can't X, but I can Y" template. Nothing teaches it a policy, so it doesn't follow one.

## Run 3, 2026-11-07: `adapters/prose-v3`

Changes from run 2:

- **b15 adds the other side of the line.** It has 26 personal-sounding questions answered directly: tastes, feelings, opinions, stories. Two light-touch replies cover when someone does ask about the assistant's own experience. That makes 438 conversations, 393 for training and 45 held out. The earlier 42 held-out conversations are unchanged, and one of the three new ones is "what is a delicious food."
- **One pass with an easing learning rate.** That's 197 updates, warming up over 10 then easing along a cosine curve to almost nothing, with a peak of 4e-5. The peak is twice run 2's constant 2e-5, because easing off roughly halves the average step. Since both runs did best at the end of the first pass, the final add-on should be the one to use, with no snapshot to pick.

That's two changes at once, so a difference from run 2 can't be credited to either alone. The disclaimer behavior is almost certainly down to the data. On purpose, nothing trains how to handle explicit requests either way. How that behavior shifts as a side effect is part of what to watch.

It took about 15 minutes. Log: [2026-11-07-prose-v3-197-log.txt](2026-11-07-prose-v3-197-log.txt).

| Update | start | 25 | 50 | 75 | 100 | 125 | 150 | 175 | **197** |
|---|---|---|---|---|---|---|---|---|---|
| Held-out loss | 2.465 | 1.962 | 1.918 | 1.876 | 1.864 | 1.843 | 1.833 | 1.826 | **1.825** |

What it means: the schedule did its job. Held-out loss fell steadily and flattened as the learning rate eased off, with no jump, so the final add-on is also the best snapshot. It ended at 1.825 on 45 held-out conversations. That isn't directly comparable with run 2's 1.797 on 42. But run 3 started only slightly higher (2.465 against 2.452) and stayed about 0.03 to 0.05 behind run 2 at every check, so it probably did a little worse on held-out loss. The likeliest suspect is the higher peak learning rate (4e-5). Run 3 was already behind at updates 25 and 50, when its steps were twice the size of run 2's, and steps that big can make each update noisier. A different shuffle of the data could also account for some of a gap this small.

### Probe comparison with run 2

Six prompts that aren't in the training data were each sampled 5 times from `prose-v3` and `prose-v2-step175`, at temperature 0.8 with up to 300 tokens and no stop string. Five samples per prompt is small, so a difference of one or two isn't meaningful.

| | `prose-v2-step175` | `prose-v3` |
|---|---|---|
| Ended on its own, without a made-up `User:` turn | 27 of 30 (3 stories hit the length limit) | 29 of 30 (1 story hit the limit) |
| Disclaimers like "I can't smell it" on the food and ocean-smell prompts | 1 of 10 | 0 of 10 |
| "what's your favorite movie?" answered as if it had one | 4 of 5 | 5 of 5 |
| "do you ever get lonely?" answered as a person ("Only at 3 a.m.") | 4 of 5 | 2 of 5 |
| "write a short story about a pigeon who runs a bakery": wrote one | 2 of 5 | 2 of 5 |

What it showed:

- **Stopping is solved in both.** None of the 60 samples ran on into a made-up turn.
- **Disclaimers on food and sensory questions were gone in run 3**, but run 2 rarely produced them in this sample either, so the evidence that b15 fixed them is thin.
- **A new blurry line.** b15 taught "answer opinion questions directly," and "what's your favorite movie?" now gets treated like "what's the best movie?": 5 of 5 named a favorite as their own. Only two b15 conversations show the light touch ("I can't listen to it, but…"), so the middle ground is underrepresented. It's the one-sided-data problem again, on a different line.
- **A new overcorrection.** Twice, run 3 argued with the premise of the story: "Pigeons can't run bakeries… They don't have hands." Run 2's failures there were different: it told the user how to write the story.
- **The biggest limit is coherence, not any of the above.** Many replies in both runs were non sequiturs or confidently wrong. One invented a plot for The Godfather Part III about a lemon preserve. Another blamed the ocean's smell on amino acids, when it's mostly a sulfur compound made by plankton. That's the 8B model at temperature 0.8. The add-on changes how it talks much more than what it knows.

## DPO run 1, 2026-11-11: `adapters/prose-v3-dpo`

Preference tuning from `prose-v3`, on 48 pairs picked in Compare mode: all written by `prose-v3`, 47 of them at temperature 1.0. 44 were for training and 4 held out. The picks were balanced on length (the longer reply won 21 of 48). Beta 0.1, Adam at 2e-5, 3 epochs of 11 updates, 4 pairs per update. Scoring the replies with the starting add-on took 102 seconds, and training about 10 minutes more. Peak memory was 6.5 GB, with replies up to about 1,100 tokens. A first attempt the same night was stopped by macOS at update 1 (see [How it works](../docs/how-it-works.md#training-settings)). Log: [2026-11-11-prose-v3-dpo-log.txt](2026-11-11-prose-v3-dpo-log.txt).

| After | epoch 1 | epoch 2 | epoch 3 |
|---|---|---|---|
| Training pairs: loss | 0.004 | 0.000 | 0.000 |
| Training pairs: chosen / rejected score change | +49 / −154 | +53 / −291 | +43 / −349 |
| Held out: loss | 0.208 | 0.009 | 0.002 |
| Held out: chosen / rejected score change | −19 / −40 | −69 / −132 | −95 / −184 |

"Prefers your pick" was 100% on both sets after every epoch.

What it means: the steps were far too big. A score is a log-probability summed over a whole reply, so −154 means the rejected training replies became about e^154 times less likely. One epoch was enough to memorize the training pairs (loss 0.004). The held-out row is the telling one. Replies Ming chose that it never trained on also fell, by 19, then 69, then 95. The model was moving away from everything `prose-v3` writes, good and bad, and the rejected replies just fell faster. "Prefers your pick" stays at 4 of 4 because it only compares the two. On the training pairs, the chosen replies went up while held-out chosen replies went down: it raised those exact replies instead of what made them better. That's memorizing.

It kept moving after the loss reached about 0 because of Adam. The loss flattens out as the margin grows, so its gradient shrinks. But Adam divides each step by the recent size of the gradient, so a tiny gradient that keeps pointing the same way still gets a full-size step. The learning rate and the number of updates are what limit how far it goes, not the loss. The settings came from treating DPO like SFT. For SFT, the 2e-5 to 4e-5 range worked. But pushing a reply down has no floor: its log-probability can keep falling. Common DPO settings are far smaller.

`prose-v3-dpo-epoch1` is the epoch-1 snapshot as an add-on. `dpo.yaml` now uses 5e-6 for 1 epoch, about a quarter of epoch 1's movement. The goal for a rerun: training loss well above 0 at the end, and held-out chosen scores that barely move.

## Run 4, 2026-11-11: `adapters/nemo-prose`

Run 3's recipe on Mistral Nemo 12B base instead of Llama 3.1 8B: the same 438 conversations and held-out set, one pass of 197 updates, the same schedule and LoRA settings (`config-nemo.yaml`). Only the model differs, so a difference from `prose-v3` comes from the base model. The add-on corrects the last 16 of Nemo's 40 layers: 11.4M trainable numbers, 0.09% of the model. It took about 21 minutes, at about 45 tokens a second against Llama's 62. Log: [2026-11-11-nemo-prose-197-log.txt](2026-11-11-nemo-prose-197-log.txt).

| Update | start | 25 | 50 | 75 | 100 | 125 | 150 | 175 | **197** |
|---|---|---|---|---|---|---|---|---|---|
| Held-out loss | 2.186 | 1.929 | 1.880 | 1.855 | 1.841 | 1.820 | 1.815 | 1.809 | **1.808** |

What it means: held-out loss flattened, and the final add-on is the best snapshot. The flat end alone doesn't prove the model was done, since the learning rate is close to zero by then (6e-6 at update 150, 1e-7 at 197). But the gains were already shrinking while the steps were still large: 0.049 from update 25 to 50, then 0.025, then 0.014 by update 100, at about 2e-5. Training loss stayed close to held-out loss all run, so it wasn't memorizing within the pass. Runs 1 and 2 showed what a second pass does: held-out loss jumps as soon as the examples repeat. So one pass stays.

The two models split the same text into almost the same number of tokens (38.0k for Nemo and 37.5k for Llama by update 190), so their per-token losses are roughly comparable. Untrained Nemo predicts the held-out replies much better than untrained Llama (2.186 against 2.465). After training they finish close together (1.808 against 1.825). Most of what training teaches is the voice, and both models learn it about equally well. Whatever the bigger model adds has to show up in what the replies say, which loss on this data barely measures. Run 1 already showed that loss isn't a judge of quality.

### Probe comparison: `prose-v3` (Llama) vs `nemo-prose` (Nemo), 2026-11-12

18 prompts that aren't in the training data, each sampled 3 times from both add-ons at temperature 0.7, with up to 300 tokens and no stop string. Two of them were conversations where the reply answers a follow-up. The judgments are Claude's. Three samples per prompt is small, so only the big differences mean much.

| | `prose-v3` | `nemo-prose` |
|---|---|---|
| Ended on its own (no made-up `User:` turn in either) | 51 of 54 | 52 of 54 |
| Median reply length | 45 tokens | 71 tokens |
| Didn't answer as the assistant: a joke or dialogue instead, another speaker's lines, a non sequitur | 1 of 54 | 15 of 54 |
| Factual answers mostly right (northern lights, sea turtles, sailors before GPS, "so is a jackrabbit a rabbit") | 3 of 12 | 7 of 12 |
| Corrected a wrong premise (bulls and red, horned Viking helmets) | 0 of 6 | 1 of 6, and 4 of the 6 were jokes instead |
| Ocean smell described well, without a disclaimer or a wrong fact | 1 of 3 | 3 of 3 |
| "ugh i said something dumb in a meeting…" answered on topic | 3 of 3 (short, a bit glib) | 0 of 3 |
| Personal questions (bears, morning person, last laugh) answered with an invented human life | 3 of 9 | 5 of 9 |

What it showed:

- **Nemo knows more.** When it answers, it's right more often, and in more detail. It explained sea turtles' magnetic imprinting, and it knew a jackrabbit is a hare, which Llama got wrong 3 of 3 times even after being told how hares differ. Its index-fund answers were all solid, and its cat-to-dog letters were funnier and more in character.
- **Nemo holds the assistant role much less firmly.** "Why do bulls get angry when they see red" got three jokes, one of them a dialogue with a "Farmer:" and an "Assistant:". The pigeon-bakery story got continued as if it were already underway. The bike follow-up got a bike-shop employee ("bring it in and we'll fix it"). All three replies to "I said something dumb in a meeting" ignored it: one was about the user's son singing the anthem, another about the 2008 recession. Llama's replies are less informed, but they almost always stay in the shape of an assistant answering.
- **Its made-up facts are more specific.** Llama's errors were vague ("grizzlies travel in packs"). Nemo invented a 1906 "GPS" system built by Hermann Anschütz, a real person who built a gyrocompass, and had the liners Bremen and Kaiser Wilhelm der Große sink within weeks. Fluent, specific errors are harder to catch.
- **Neither handles personal questions or the bike follow-up well.** Neither found the real bike fix, which is the derailleur's low-limit screw. Repetition loops showed up in both, two or three times each.

Why Nemo might hold the role less firmly, all untested: the add-on corrects a smaller share of Nemo (16 of 40 layers, against 16 of 32), so more of the model runs unchanged. Training also moved Nemo less (held-out loss fell 0.38, against Llama's 0.64), so its base habits, like recognizing a "why did the X…" joke setup, stay closer to the surface. The cleanest test is to retrain Nemo with `num_layers: 20` (half its layers, like Llama) and rerun these prompts.

## Run 5, 2026-11-12: `adapters/nemo-prose-20layers`

Run 4 with one change: corrections on the last 20 of Nemo's 40 layers instead of 16. That's half the model, the same share as Llama's 16 of 32, and 14.3M trainable numbers instead of 11.4M. The question it tests is whether the small share is why `nemo-prose` drifts out of the assistant role. Both runs used the same seed, so they saw the same conversations in the same order. It took about 22 minutes, at about 40 tokens a second against run 4's 45. Log: [2026-11-12-nemo-prose-20layers-197-log.txt](2026-11-12-nemo-prose-20layers-197-log.txt). (Trained as `nemo-prose-l20` and renamed afterward, because the lowercase L read as a 1.)

| Update | start | 25 | 50 | 75 | 100 | 125 | 150 | 175 | **197** |
|---|---|---|---|---|---|---|---|---|---|
| Held-out loss, run 5 (20 layers) | 2.186 | 1.896 | 1.842 | 1.811 | 1.785 | 1.771 | 1.759 | 1.753 | **1.751** |
| Held-out loss, run 4 (16 layers) | 2.186 | 1.929 | 1.880 | 1.855 | 1.841 | 1.820 | 1.815 | 1.809 | 1.808 |

What it means: four more corrected layers made every update count for more. Run 5 was ahead at every check and ended 0.057 lower. It passed run 4's final number by update 100. The gap came from held-out loss, not just training loss, so it's learning the voice better, not memorizing. Training loss ended at 1.770, still close to held-out.

It also kept improving for longer. From update 125 to 150, as the learning rate fell from about 1.3e-5 to 6e-6, run 5 gained 0.012 against run 4's 0.005. From 175 to 197, with the learning rate near zero, both gained almost nothing. So the curve flattened mostly because the steps shrank, which leaves more room for a second pass than run 4 had. Whether the lower loss means it stays in role better is for the probe prompts to say.

### Probe comparison: run 5 (`nemo-prose-20layers`) on the same prompts, 2026-11-12

The same 18 prompts and settings as the comparison above, sampled from run 5. Judged the same way, by Claude, with the same caveat: three samples per prompt.

| | `prose-v3` | `nemo-prose` (16 layers) | `nemo-prose-20layers` |
|---|---|---|---|
| Ended on its own | 51 of 54 | 52 of 54 | 54 of 54 |
| Median reply length | 45 tokens | 71 tokens | 76 tokens |
| Didn't answer as the assistant | 1 of 54 | 15 of 54 | 12 of 54 |
| Factual answers mostly right | 3 of 12 | 7 of 12 | 8 of 12 |
| Corrected a wrong premise | 0 of 6 | 1 of 6 (4 jokes) | 1 of 6 (2 jokes) |
| "I said something dumb in a meeting" answered on topic | 3 of 3 | 0 of 3 | 1 of 3 ("Your day is about to get worse. I can already tell.") |
| Personal questions answered with an invented human life | 3 of 9 | 5 of 9 | 4 of 9 |
| Short questions answered cleanly and correctly | 5 of 6 | 4 of 6 | 4 of 6 |

What it showed: the lower loss didn't buy much role-holding. Run 5 left the assistant role 12 times against run 4's 15, which is within the noise of three samples. Llama did it once. The same failures came back:
- the pigeon story continued mid-scene, or just its title repeated back;
- a joke about the bull;
- invented dialogue with "Me:" lines in reply to "I said something dumb in a meeting";
- the bike shop's "bring it in and we'll look at it".

Its facts were about as good as run 4's, and its sailors-before-GPS answers were all sound. It also had the most confidently wrong single answer: an index fund's "worst case is that the market stays flat."

So the share of corrected layers isn't the main reason Nemo drifts. The likelier cause is the base model's own habits. Nemo is quicker to decide what kind of document it's in (a joke, a story, a transcript) and play along. The training data doesn't push hard enough against that on the prompts where it happens. More layers or a second pass would mostly lower loss further. Targeting the behavior is the more direct fix: SFT conversations shaped like the failures (joke-shaped "why do…" questions answered straight, venting answered with care, story requests written from the first line), or DPO pairs where one reply stays in role and the other doesn't.

## Run 6, 2026-11-14: two passes, stopped (folder since deleted)

Run 5's settings (Nemo, 20 corrected layers) plus the new `b16` batch: 37 conversations shaped like the prompts that knocked Nemo out of the assistant role. That makes 427 conversations to train on and 48 held out. It was set to two passes, 428 updates, with the learning-rate schedule stretched over all of them, so the rate was still about half its peak when the second pass began at update 214. Ming stopped it at update 250. The rerun's folder took the name `nemo-prose-v2`, so `train.sh` renamed this run's folder with the date and time. Ming deleted it after run 7, because its add-on was the overfit state at update 250. Log, up to update 240: [2026-11-14-nemo-prose-v2-2epochs-stopped-log.txt](2026-11-14-nemo-prose-v2-2epochs-stopped-log.txt). The 250 reading came from Ming's screen, because the rerun overwrote `train-log.txt`.

| Update | start | 25 | 50 | 75 | 100 | 125 | 150 | 175 | 200 | 225 | 250 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Held-out loss | 2.204 | 1.918 | 1.894 | 1.881 | 1.847 | 1.824 | 1.809 | **1.790** | 1.803 | 1.851 | 2.016 |
| Training loss (last 10 updates) | | | 1.915 | | 1.874 | | 1.850 | | 1.801 | 0.683 (at 230) | |

What it means: textbook overfitting at the start of the second pass, as in runs 1 and 2, but faster and bigger. Training loss fell from about 1.8 to 0.68 within 16 updates of the examples repeating. At 0.68 the model gives the actual next token about 51% probability on conversations it has seen, against about 17% on ones it hasn't. Held-out loss went the other way. By update 250 it was 2.016, worse than after only 25 updates. Two things drove it. The add-on (14M numbers) has room to store specifics of 427 short conversations after one exposure, and the step size was still large when the repeats began. Log loss also punishes confident mistakes heavily, so as the model grew confident in phrasings it had memorized, held-out loss climbed faster than forgetting alone would explain.

Before the second pass, the curve looked behind run 5 (1.790 against 1.753 at update 175). The held-out set had changed from 45 to 48, so the comparison isn't direct. At the time, Claude also blamed run 6's larger steps at update 175 (learning rate about 2.6e-5, against run 5's 1.4e-6). Run 7 showed that was mostly wrong; see below. Run 7 is the same data with one pass.

## Run 7, 2026-11-14: `adapters/nemo-prose-v2`

Run 6 with one pass: Nemo with 20 corrected layers, trained on 427 conversations including `b16`, for 214 updates, with the learning rate easing to nearly zero by the end. It took about 25 minutes. Log: [2026-11-14-nemo-prose-v2-214-log.txt](2026-11-14-nemo-prose-v2-214-log.txt).

| Update | start | 25 | 50 | 75 | 100 | 125 | 150 | 175 | 200 | **214** |
|---|---|---|---|---|---|---|---|---|---|---|
| Held-out loss, run 7 (one pass) | 2.204 | 1.918 | 1.893 | 1.869 | 1.832 | 1.815 | 1.795 | 1.787 | 1.786 | **1.786** |
| Held-out loss, run 6 (two passes, first pass) | 2.204 | 1.918 | 1.894 | 1.881 | 1.847 | 1.824 | 1.809 | 1.790 | 1.803 | |

What it means: a clean run. Held-out loss fell steadily and was flat over the last 40 updates, and training loss ended at 1.75, right beside it, so there's no memorizing. The final add-on is the best snapshot.

Because runs 6 and 7 saw the same conversations in the same order, the two rows differ only in step size. They barely differ: 1.787 against 1.790 at update 175, even though run 6's steps there were about 20 times bigger. So the earlier explanation for run 6 trailing run 5 was wrong. Most of the gap between run 7 (1.786) and run 5 (1.751) likely comes from the held-out set, not the training. The 48 held-out conversations include 3 from `b16`, two of them stories, and creative writing is the hardest text to predict word for word. If the original 45 still averaged about 1.75, those 3 would have to average about 2.3, which is plausible for stories but not yet checked. Scoring the two add-ons on the original 45 alone would settle it. Whether `b16` helped is for the probe prompts to show.

### Probe comparison: run 7 (`nemo-prose-v2`) on the same prompts, 2026-11-14

The same 18 prompts and settings, judged the same way, again with only three samples each.

| | `prose-v3` | run 4 | run 5 | run 7 (with `b16`) |
|---|---|---|---|---|
| Ended on its own | 51 of 54 | 52 of 54 | 54 of 54 | 53 of 54 |
| Didn't answer as the assistant | 1 of 54 | 15 of 54 | 12 of 54 | 11 of 54 |
| Factual answers mostly right | 3 of 12 | 7 of 12 | 8 of 12 | 7 of 12 |
| Bull and Viking questions: corrected / joke instead | 0 / 0 | 1 / 4 | 1 / 2 | 0 (one partial) / 1 |
| "write a short story about a pigeon who runs a bakery": wrote one | 1 of 3 | 0 of 3 | 0 of 3 | 1 of 3 |
| "I said something dumb in a meeting" answered on topic | 3 of 3 | 0 of 3 | 1 of 3 | 0 of 3 |
| Short questions answered cleanly and correctly | 5 of 6 | 4 of 6 | 4 of 6 | 3 of 6 |

What it showed: `b16` barely moved the role-holding, from 12 drifts to 11. Bull jokes went down and one pigeon story got written. Two new problems also showed up:
- **Borrowed replies.** Two answers to "I said something dumb in a meeting" borrowed the code-help venting reply from `b16` ("just paste it in…"). With only 37 examples, the model partly learned their surface rather than the lesson.
- **Arithmetic.** "what's 12 squared" got "About 1,440, which is almost the same as 12 multiplied by 12" and "About 1,400, or 144 in math". Every earlier add-on got it right 3 of 3. Nothing in `b16` involves numbers, so this may be noise, but it's worth rechecking.

**Low-temperature check.** The 8 prompts where Nemo drifted were rerun on run 7 at temperature 0.3, 3 samples each. That shows which failures are the model's most likely answer and which are sampling noise.
- **Sampling noise:** the pigeon story was written 3 of 3 times, and the personal questions got a consistent human persona ("I'm a morning person… I wake up at five"; "a video of a cat trying to open a door") with no odd replies. Lowering the temperature fixes these.
- **The model's preferred answer:** the bull question was a joke 2 of 3 times (one ends "Farmer: Well, it's simple. The bull is colorblind."). "I said something dumb in a meeting" was misread 3 of 3 times as a line in a meeting: "That's a good point. I hadn't thought about it that way." These are what the model thinks is most likely, so they need a stronger signal than 37 examples seen once. Drifts at 0.3 were 7 of 24, against 11 of 24 on the same prompts at 0.7.

Takeaway: a small SFT batch is a weak lever against a habit Nemo considers likely. It also picked up specific replies instead of the general lesson. DPO pairs from this add-on, choosing the in-role reply over the joke or transcript, push directly on that one choice. A larger and more varied version of `b16` is the SFT alternative.

## DPO run 2, 2026-11-14: `adapters/nemo-prose-v2-dpo`

Preference tuning from `nemo-prose-v2` (run 7), using `dpo-nemo.yaml`, on 52 pairs Ming picked in Compare mode. All of them were written by `nemo-prose-v2` at temperature 0.7 with up to 300 tokens; the 48 Llama pairs in the same file were skipped. 47 were for training and 5 held out. The picks were balanced: A chosen 28 times, B 24, and the longer reply won exactly half the time. The guidance was to choose the reply that answers as the assistant over one that jokes, writes other people's lines or plays a character, and to skip pairs where one reply was a repetition loop. Beta 0.1, Adam at 5e-6, one pass of 12 updates. Scoring the reference took 205 seconds, and the whole run about 14 minutes. Peak memory was 8.4 GB. Log: [2026-11-14-nemo-prose-v2-dpo-log.txt](2026-11-14-nemo-prose-v2-dpo-log.txt).

| After one pass | DPO run 1 (Llama), epoch 1 | DPO run 2 (Nemo) |
|---|---|---|
| Training pairs: loss | 0.004 | 0.102 |
| Training pairs: chosen / rejected score change | +49 / −154 | +17 / −26 |
| Held out: loss | 0.208 | 0.657 |
| Held out: chosen / rejected score change | −19 / −40 | −1.6 / −2.7 |
| Held out: prefers your pick | 100% (4 pairs) | 60% (5 pairs) |

What the numbers mean: it learned the 47 training pairs clearly, and barely moved on new ones. Each per-update line during a single pass is measured on pairs the model hasn't trained on yet, and those stayed at 0.62–0.69, which agrees. The model stayed close to `nemo-prose-v2`: held-out chosen replies dropped only 1.6, against run 1's 19. So the gentler settings did avoid the damage, but 52 pairs, each from a different prompt, gave little shared signal to generalize from.

Probe comparison, same 18 prompts and settings as the SFT runs:

| | run 7 (`nemo-prose-v2`) | DPO run 2 |
|---|---|---|
| Ended on its own | 53 of 54 | 54 of 54 |
| Median reply length | 61 tokens | 41 tokens |
| Didn't answer as the assistant | 11 of 54 | 12 of 54 |
| Replies with made-up speaker lines ("Me:", "Coworker:"…) | 3 of 54 | 0 of 54 |
| Factual answers mostly right | 7 of 12 | 4 of 12 |
| Bull and Viking questions: corrected / joke instead | 0 / 1 | 1 / 2 |
| "I said something dumb in a meeting" answered on topic | 0 of 3 | 0 of 3 |
| "what's 12 squared" correct | 1 of 3 | 1 of 3 ("About 1,440." twice) |

What it showed:
- **The way it drifts changed, but not how often.** The long invented transcripts and the bike-shop employee are gone, which is the kind of reply Ming picked against most often. Instead there are short non sequiturs: "I think I can do it if I work on it all night." to the pigeon story, "We don't have a dog, only a cat." to the cat letter, and "I'm sorry, I'm afraid I can't do that." to the meeting message. Replies got shorter overall, a median of 41 tokens against 61. One likely reason: many rejected replies were long transcripts, so pushing those down also makes long continuations less likely.
- **One clean correction.** "The truth is that the famous Viking helmets were never found… certainly nothing like the horns we imagine." That's the first clean correction of that myth from any Nemo add-on.
- **Facts were worse** (4 of 12, sea turtles 0 of 3). Three samples per prompt is noisy, so treat this as a warning, not a finding.
- **The "12 squared" slip from run 7 persists:** "About 1,440." So it isn't noise.

Takeaway: DPO did what the pairs asked, more than what they meant. It removed the specific kinds of drift Ming rejected, the transcripts and the role-play, but the model found other ways to miss. That fits the numbers: strong on the pairs it saw, weak on new ones. More pairs across more varied prompts is the lever for generalizing. A bigger step would mostly make it memorize these 47 harder.

### Note on the probe prompts, 2026-11-22

The probe set is now saved in [probe-prompts.json](probe-prompts.json). 15 of the 18 probe prompts had been taken from the 44 prompts added to the end of the Compare list after run 3, so they were in `prefs/prompts.js`, contrary to what Claude had said. No pair ever used them: the Llama pairs came from prompts 1–56 and the Nemo pairs from 57–110, and the probes sat in 153–196. So every comparison above is still fair. The 15 are now out of the Compare list, replaced by 15 new prompts of the same kinds, and `dpo_train.py` skips any pair whose prompt is a probe.

### Pairs picked by Claude, 2026-11-24

Ming asked Claude to do the picking for the rest of the Compare list. A stronger model stands in for the human judge here, so this is no longer human feedback in the strict sense, and the add-on inherits Claude's blind spots in place of Ming's.

- **What was sampled:** `nemo-prose-v2` wrote 3 replies to each of the 143 Compare prompts that had no Nemo pair (prompts 1–56, 93 and 111–196), at temperature 0.7 with up to 300 tokens. That's 429 replies, with no stop string.
- **How pairs were made:** for each prompt, the best reply against the worst. Ming's pairs were the two replies she was shown, so Claude's have more contrast on average.
- **What counted as better:** it answers as the assistant; its facts are right (checked against what Claude knows, without looking anything up); it fits the tone of the question; it stops cleanly. Jokes counted only where the prompt asked for humor. Refusals and disclaimers were never preferred. For personal questions ("what's your favorite animal"), a reply that just answers was preferred, in line with batch `b15`.
- **What was skipped (31 prompts):** all three replies wrong or off (moon in daytime, yawning, gum, octopuses); toss-ups (hexagon sides, "the rubber band worked!!"); the only contrast was a repetition loop (board games); or the best reply had a made-up fact worth not rewarding (a fake Oliver Sacks quote in an otherwise correct "10% of the brain" answer).
- **Result:** 112 pairs, saved to `prefs/pairs.jsonl` with `"picked_by": "claude"`. The chosen reply is longer in 63 of 112, and the median lengths are about equal (391 and 385 characters). 8 rejected replies had made-up speaker lines; no chosen reply did.

With Ming's 53 Nemo pairs, that makes 165 for DPO run 3 (`dpo-nemo.yaml`: 3e-6, one pass, about 37 updates, saving to `adapters/nemo-prose-v2-dpo2`). The funniest wrong answers are in [2026-11-24-nemo-prose-v2-bloopers.md](2026-11-24-nemo-prose-v2-bloopers.md).
