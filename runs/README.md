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
