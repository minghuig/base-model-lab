# Multi-turn conversations: follow-up questions, corrections, "make it shorter",
# changes of topic, and thanks. Only the last reply is trained; the earlier turns
# are context, so the model learns to answer and stop even when the conversation
# looks like it's still going.

EXAMPLES = [
["what can i make with eggs, spinach and some feta",
"""A spinach and feta omelet is the quickest: wilt the spinach in a hot pan with a little butter, pour in two or three beaten eggs, and crumble the feta over one half before you fold it. If you have a bit more time, the same three things make a good frittata, which you finish under the broiler and can eat cold the next day.""",
"i don't have a broiler",
"""Then finish it on the stove. Once the edges have set, put a lid on the pan and turn the heat to low; the trapped steam cooks the top in five to eight minutes. If the bottom browns before the middle firms up, slide the frittata onto a plate, flip it back into the pan upside down, and give it two more minutes."""],

["what's compound interest",
"""It's interest calculated on both the money you started with and the interest that money has already earned. If you put $1,000 in an account paying 5 percent a year, you earn $50 the first year. The second year you earn 5 percent of $1,050, which is $52.50, and the amount grows a little faster every year because the base keeps getting bigger.""",
"explain it like i'm ten",
"""Imagine a jar of marbles that gets one new marble for every ten marbles inside, once a year. If you never take any out, the new marbles help make even more marbles the next year. At first the jar fills slowly, but after many years it's filling fast. Compound interest does the same thing with money."""],

["who wrote frankenstein",
"""Mary Shelley. She began it in 1816 during a rainy summer near Lake Geneva, when Lord Byron challenged his guests to each write a ghost story, and the novel was published in 1818.""",
"wait wasn't it percy shelley",
"""It was Mary. The confusion is understandable: the first edition was published anonymously, and Percy Shelley, her husband, wrote its preface and made some edits, so for a while some readers assumed the book was his. Her name appeared on the title page of the second edition in 1823, and scholars agree the novel is hers."""],

["suggest a name for a gray kitten",
"""Smoke is a classic, and it suits a cat that drifts silently from room to room. If you'd like something with more personality, Pebble, Earl Grey and Ash are all good, and Dusty works if the kitten turns out to be the type who hides under beds.""",
"something less obvious?",
"""Try Pewter, which sounds a little old-fashioned and dignified, or Fog, which is short and easy to call. Graphite suits a cat with a sharp streak. If you'd like a person's name, Gus or Mabel both have a pleasingly gray quality to them."""],

["write a text asking my neighbor to move their car out of my driveway",
"""Hi, it's [your name] from next door. I noticed your car is parked in my driveway, and I need to get my own car out soon. Would you mind moving it when you get a chance? Thanks so much!""",
"less formal, we're friendly",
"""Hey! Your car's in my driveway and I need to head out soon. Mind moving it when you get a sec? Thanks!"""],

["i failed my driving test",
"""I'm sorry. That's a frustrating one, especially after all the practice and the nerves of the day itself. Plenty of good drivers failed their first test, so it says less about you than it feels like right now. Do you know what tripped you up?""",
"second time. the examiner said i was too hesitant at intersections",
"""That's useful feedback, and a fixable one. Hesitation usually comes from not being sure who has the right of way, so spend your next practice sessions on intersections specifically: four-way stops, unprotected left turns, and merging. Say out loud what you're checking and why as you drive; it builds the habit of deciding quickly. Being careful is a good instinct. You just need the confidence to act on what you've already seen."""],

["how much water should i drink a day",
"""There's no single number that fits everyone. A common guideline is about 2.7 liters a day for women and 3.7 for men, but that counts water from all sources, including food, which supplies roughly a fifth of it. Most healthy people can simply drink when they're thirsty and drink more in hot weather or when they exercise. Pale yellow urine is a reasonable sign you're getting enough.""",
"does coffee count?",
"""Mostly, yes. Caffeine has a mild diuretic effect, but in the amounts people usually drink, a cup of coffee still leaves you with more water than you started with, and regular coffee drinkers build up a tolerance to the effect. It's still worth having plain water through the day, but your morning cup isn't working against you."""],

["how do i get candle wax out of a tablecloth",
"""Let the wax harden first, then scrape off as much as you can with a dull knife. Lay a paper towel over the spot and press it with a warm iron; the wax melts into the paper. Keep moving to fresh paper until nothing more comes up. If a colored stain remains, treat it with a little dish soap or stain remover before washing as usual.""",
"thanks. totally different question, how long do i boil an egg for a runny yolk",
"""About six minutes for a large egg lowered straight from the fridge into water that's already at a rolling boil. Then move it into cold water for a minute so it stops cooking and peels more easily. Six and a half minutes gives you a yolk that's jammy rather than runny."""],

["is it bad to crack your knuckles",
"""As far as the evidence goes, no. The pop comes from a sudden drop in pressure in the fluid that lubricates the joint, which forms a small gas bubble, and studies haven't found that habitual cracking causes arthritis. One doctor cracked the knuckles of only one hand for more than sixty years and found no difference between his hands. If cracking ever comes with pain or swelling, though, that's worth having looked at.""",
"my mom always said it gives you arthritis",
"""A lot of moms said that, and it's one of the most common health warnings people grow up with. It's an understandable worry, since the sound is alarming, but it hasn't held up: studies comparing habitual crackers with non-crackers haven't found more arthritis among the crackers. Your mom may simply have found the noise irritating, which is a perfectly good reason to ask someone to stop."""],

["how do i reverse a string in python",
"""Use slicing with a step of minus one: reversed_text = text[::-1]. The slice walks the string from the end to the beginning and builds a new string, since Python strings can't be changed in place.""",
"and a list?",
"""The same slice works: items[::-1] returns a new list in reverse order. If you want to reverse the list itself without making a copy, call items.reverse(), which changes it in place and returns None. That last detail catches people: writing items = items.reverse() leaves you with None."""],

["what's a good houseplant for a dark apartment",
"""A ZZ plant is about as forgiving as they come: it tolerates low light, goes weeks without water, and stays glossy through neglect. Snake plants and pothos are also good choices. Even these grow slowly in dim rooms, so water less often than the care tag suggests; overwatering kills far more low-light plants than darkness does.""",
"is zz safe for cats",
"""Not entirely. ZZ plants contain calcium oxalate crystals, which irritate the mouth and stomach if a cat chews the leaves, causing drooling, pawing at the mouth, or vomiting. It's rarely serious, but it's unpleasant, and snake plants and pothos carry the same risk. If your cat likes to nibble, a parlor palm or a cast iron plant is a safer bet, and both cope well with low light."""],

["how do i get rid of fruit flies",
"""Find what's attracting them first: overripe fruit, a damp sponge, the bottom of the trash can, or a drain with gunk in it. Then set a trap: a small bowl of apple cider vinegar with a drop of dish soap, which breaks the surface tension so the flies sink when they land. Empty and refill it every couple of days until they're gone.""",
"the trap worked, thank you!!",
"""Wonderful. There's something deeply satisfying about that little bowl of defeated flies."""],

["how do i start doing pushups if i can't do one",
"""Start at an incline. Do pushups with your hands on a kitchen counter or a sturdy table, keeping your body in a straight line from head to heels, and lower your chest until it nearly touches the edge. When you can do three sets of ten with good form, move to something lower, like the arm of a sofa or a step. Every few weeks, go a little lower until you reach the floor.""",
"my wrists hurt when i do them",
"""That's common, because a pushup bends your wrists back under a lot of weight. Try pushup handles, or making fists, so your wrists stay straight. Spreading your fingers wide and pressing through them also takes some load off. If the pain persists even with straight wrists, rest them for a while and have it looked at."""],

["how do you say thank you in japanese",
"""Arigatou, or more politely, arigatou gozaimasu. The polite form is the safe choice with strangers, shopkeepers and anyone older than you.""",
"and you're welcome?",
"""Dou itashimashite. In everyday conversation, though, people often answer thanks with something lighter, like iie, which literally means "no" and works like "oh, not at all." """.strip()],

["what's the tallest mountain in the us",
"""Denali, in Alaska, at 20,310 feet. It's also the tallest peak in North America.""",
"i thought it was mount whitney",
"""Mount Whitney is the tallest in the contiguous United States, at 14,505 feet, so it depends on whether you count Alaska. Including Alaska, Denali is far taller. Whitney sits in California's Sierra Nevada, and on a clear day you can see it from the town of Lone Pine."""],

["who first climbed mount everest",
"""Edmund Hillary, a beekeeper from New Zealand, and Tenzing Norgay, a Sherpa mountaineer, reached the summit together on May 29, 1953, as part of a British expedition.""",
"how many people have done it since",
"""Thousands, many of them more than once. The numbers rose sharply once commercial guiding took off in the 1990s, and on a clear day in late May, the busiest part of the season, hundreds of people may try for the summit. The total changes every season, so for a current figure, look up the Himalayan Database, which keeps the records."""],

["write a two-line poem about rain",
"""The rain came softly, testing every roof,
then settled in, as if it needed proof.""",
"make it sadder",
"""The rain kept knocking at the empty house,
as if the ones who answered might come back."""],

["should i put tomatoes in the fridge",
"""Ripe tomatoes keep their flavor best on the counter, out of direct sun. Cold breaks down the compounds that give them their taste and can make the flesh mealy. Once a tomato is fully ripe and you can't eat it within a day or two, the fridge is fine; let it come back to room temperature before you eat it.""",
"why does the cold ruin them",
"""Tomatoes are a warm-climate fruit, and below about 10°C (50°F) the enzymes that make many of their aroma compounds slow down or stop. The cold also damages cell membranes, so the flesh loses its firm, juicy texture and turns mealy. Some of the aroma comes back after a day at room temperature, but chilling for a week or so does lasting harm."""],

["what should i bring to a potluck",
"""Something that travels well and tastes good at room temperature: a big grain or pasta salad, a tray of roasted vegetables, or brownies, which almost everyone likes. Avoid anything that has to be served piping hot or assembled at the last minute, since you probably won't have the kitchen to yourself.""",
"i don't really cook",
"""Then bring something you don't have to cook. A good loaf of bread with a block of nice butter, a fruit platter, a box of pastries from a bakery, or drinks and a bag of ice are all welcome. Hosts tend to run short on drinks and ice more often than food, so those are a gift in disguise."""],

["can't sleep",
"""That's miserable, especially when you're watching the clock. If you've been lying there more than twenty minutes, get up and do something quiet in dim light, like reading something dull, until you feel sleepy again. Lying awake trying hard to sleep tends to keep you awake. What's keeping you up?""",
"just thinking about work stuff",
"""Try writing it down. Grab paper, list what's on your mind and the next small step for each item, then put the list somewhere out of sight. Your brain keeps circling partly because it's afraid of forgetting; once the list exists, it can let go a little. Tomorrow you can deal with the list. Tonight you just need to rest."""],

["what's the difference between git merge and rebase",
"""Both bring changes from one branch into another. Merge creates a new commit that ties the two histories together, keeping a record of exactly when the branches split and rejoined. Rebase replays your commits on top of the other branch as if you had started from there, giving you a straight, linear history but rewriting your commits in the process.""",
"which should i use",
"""For your own work that you haven't pushed yet, rebasing onto the main branch keeps history tidy, and many teams prefer it. Once a branch is shared, merge instead, because rewriting commits that other people have already pulled forces them to untangle the difference.""",
"ok that makes sense",
"""Good. The short version to remember: rebase what's private, merge what's shared."""],

["what should i pack for a weekend camping trip",
"""Start with shelter and sleep: a tent, a sleeping bag rated for the overnight low, and a sleeping pad. Then cooking: a stove, fuel, a lighter, a pot, and food that's easy to make. Add layers, including a warm jacket and a rain shell, a headlamp, a first aid kit, water and a way to treat more, and sunscreen. Check the campground's rules on fires and food storage before you go.""",
"is a sleeping pad really necessary",
"""For most trips, yes. The ground pulls heat out of your body far faster than the air does, and a sleeping bag does little underneath you because your weight squashes its insulation flat. A pad puts a layer between you and the cold ground. Without one, even a good bag on a mild night can leave you cold and stiff by morning."""],

["what's a good name for a sourdough starter",
"""People love giving starters punny names: Clint Yeastwood, Bread Pitt and Doughlores are all popular. If you'd prefer something gentler, a plain old-fashioned name like Herbert or Agnes suits a jar that may well outlive several of your houseplants.""",
"lol bread pitt",
"""He rises to every occasion."""],

["what's the best way to treat a minor burn",
"""Run cool, not icy, water over it for about twenty minutes, which is longer than most people expect but makes a real difference to how deep the burn goes. Then cover it loosely with a clean non-stick dressing or plastic wrap. Skip butter, oil and ice. A simple pain reliever can help with the sting.""",
"it's blistering, should i pop it",
"""No, leave it intact. The blister's skin protects the raw layer underneath from infection, and it usually drains on its own within a few days. If it breaks, wash it gently with soap and water and cover it. See a doctor if the burn is larger than your palm, is on your face, hands or a joint, or shows signs of infection like spreading redness or pus."""],

["recommend a movie for a cozy night in",
"""Paddington 2 is close to perfect for that: warm, funny, beautifully made, and gentle without being bland. If you'd like something more grown-up, Chef, about a cook who restarts his career with a food truck, is easygoing and will make you hungry.""",
"seen paddington 2. something older?",
"""Try Roman Holiday, from 1953, with Audrey Hepburn as a princess who slips away from her duties for a day in Rome with an American reporter played by Gregory Peck. It's light and charming, and the ending is more grown-up than you'd expect. The Philadelphia Story, from 1940, is another good choice if you like quick, witty dialogue."""],

["what does ephemeral mean",
"""Lasting a very short time. Mayflies are famously ephemeral, and so are soap bubbles and most internet trends.""",
"use it in a sentence about snow",
"""The snowman was magnificent but ephemeral: by noon the next day, all that remained was a scarf, two buttons, and a carrot in a puddle."""],

["what's a fair way to split a restaurant bill",
"""If everyone ordered roughly the same, split it evenly; it's quick and nobody feels nickel-and-dimed. If orders differ a lot, have each person pay for what they had, then divide shared items like appetizers and wine among the people who actually had some. Work out the tip as a percentage of each person's share, so it scales with what they ordered.""",
"the bill is $186 for four people with an 18% tip, even split",
"""Each person pays $54.87. The tip on $186 at 18 percent is $33.48, which makes the total $219.48, and divided four ways that's $54.87 each."""],

["can you help me write something for my sister",
"""Of course. What's the occasion? A birthday card, a thank-you, an apology and a wedding speech each call for something quite different.""",
"her graduation, she just finished nursing school",
"""Here's a card message you could use or adapt:

You did it. All those nights of studying, the exams, the clinical shifts that started before sunrise: they were for this. I've watched you work harder than anyone I know, and your patients are lucky to be getting you. I'm so proud of you. Congratulations, nurse!

If you tell me a little about her, like an inside joke or a story from school, I can make it more personal."""],

["why does bread go stale",
"""Mostly not because it dries out. In fresh bread, the starch is soft and loosely arranged after baking. As the loaf sits, those starch molecules slowly line up again into tight, crystal-like bundles, pushing water out of the way, and that's what makes the crumb firm and crumbly. It happens fastest at fridge temperatures, which is why refrigerated bread goes stale sooner than bread on the counter.""",
"can i fix it",
"""Often, yes, if it's stale rather than moldy. Run the loaf briefly under the tap or sprinkle it with water, then put it in an oven at about 175°C (350°F) for five to ten minutes. The heat loosens the starch again and the water turns to steam, so the inside softens while the crust crisps. Eat it soon, though, because it goes stale again quickly once it cools."""],

["gift ideas for my sister who just moved into her first apartment",
"""Practical things she won't think to buy are often the most appreciated: a small toolkit with a hammer, screwdrivers and a tape measure, a fire extinguisher, or a good set of kitchen knives. If you'd like something more personal, a framed print of her new city or a healthy plant gives the place some warmth.""",
"she doesn't cook much",
"""Then skip the knives and lean toward comfort and convenience. A cozy throw blanket, good bath towels, a set of nice glasses for having friends over, or a coffee maker if she drinks coffee would all get daily use. A gift card for a local takeout place she likes is also a kind, practical nod to how she actually lives."""],

["how do i get better at chess",
"""Play regularly, and review your games afterward, especially the losses, to find the moment things went wrong. Solve tactics puzzles for a few minutes a day, since most games below a strong club level are decided by a missed tactic rather than deep strategy. Learn a couple of openings well enough to reach a sensible middlegame, and play slower time controls so you have room to think.""",
"i hate studying openings",
"""Good news: at most levels you barely need to. Learn the basic principles, which are to control the center, bring out your knights and bishops quickly, castle early, and avoid moving the same piece twice without a reason, and you'll reach a playable middlegame in nearly every game. Put the time you'd spend memorizing lines into tactics puzzles instead; they'll win you far more games."""],

["how long can cooked rice sit out",
"""No more than about two hours at room temperature, or one hour if it's hot out. Rice can carry spores of a bacterium called Bacillus cereus that survive cooking, and if the rice sits warm, they grow and produce toxins that reheating won't destroy. Cool leftovers quickly and refrigerate them, and eat them within a day or so.""",
"oh no i left it out overnight",
"""Then it's safest to throw it out. It may look and smell fine, but the toxins don't change how it looks or smells, and they can cause vomiting within a few hours of eating. It's a cheap loss compared with a rough night.""",
"ok tossing it, thanks",
"""Good call. Next time, spreading the rice out on a plate or tray helps it cool fast enough to go straight into the fridge."""],

["my python script says ModuleNotFoundError: No module named 'requests'",
"""Python can't find the requests library, which doesn't come with Python itself. Install it by running pip install requests from the same environment you use to run the script.""",
"i installed it and still get the error",
"""Then it was probably installed for a different Python than the one running your script, which is very common on machines with more than one installed. Run python -m pip install requests, replacing python with the exact command you use to run the script, such as python3. That ties the install to that interpreter. If you use a virtual environment, activate it first."""],

["my group project partner isn't doing their part",
"""Talk to them directly, early, and in specifics. Something like: "We're due on the 12th and I haven't seen your section yet. Can you get me a draft by Friday?" A concrete deadline is harder to slide past than a general complaint. Sometimes people go quiet because they're stuck or overwhelmed, so it's worth asking whether something's getting in the way.""",
"we already talked and nothing changed",
"""Then it's time to protect yourself and the grade. Keep a short written record of what was agreed and what was delivered, with dates. Let your instructor know now, before the deadline, and keep it factual rather than angry: what each of you agreed to do and what's still missing. Most instructors would much rather hear about it early than sort it out after the grades are in."""],

["what's a recession",
"""A recession is a significant, broad decline in economic activity that lasts more than a few months. Output falls, businesses cut back, unemployment rises, and people spend less. A common shorthand is two consecutive quarters of shrinking GDP, though official judgments look at more than that, including jobs, income and sales.""",
"are we in one right now?",
"""I can't check current economic data, so I can't tell you what's happening right now. In the US, the official call comes from a committee at the National Bureau of Economic Research, and it often comes months after a recession has started. For the current picture, look at recent reports on GDP and unemployment from a news source you trust."""],

["write a haiku about coffee",
"""Dark cup in cold hands,
steam writing its slow letters,
the morning says yes.""",
"another one but funny",
"""Third cup since sunrise.
My pulse plays a drum solo.
Was it worth it? Yes."""],

["help me pick between a cat and a dog",
"""The biggest difference is time. A dog needs walks, training and company every day, and it's hard to leave one alone for long or travel on short notice. A cat is more independent: it needs feeding, a clean litter box and some play, but it won't mind if you work late. Dogs give you a reason to get outside and a very obvious kind of devotion; cats offer a quieter companionship on their own terms. How much are you home?""",
"i work from home but travel a lot",
"""That's a real conflict for a dog, since every trip means arranging a sitter or boarding, which adds up in cost and planning. A cat handles travel much better: for a weekend, a friend or a sitter dropping by once a day is usually enough. If you're set on a dog, a trusted sitter can make it work, but on what you've described, a cat fits your life more easily."""],

["give me a title for a blog post about learning to bake bread",
"""A few options: "The Loaf I Didn't Ruin," "Flour on Everything," or "Notes from a Beginner's Oven." If you want something straightforward, "What I Learned from Baking My First Ten Loaves" tells readers exactly what they're getting.""",
"i like the first one but make it less negative",
"""How about "The Loaf That Finally Worked"? It keeps the story of trial and error but lands on the success. "My First Good Loaf" is a quieter version of the same idea."""],

["how does a microwave heat food",
"""It fills the inside of the oven with microwaves, a kind of radio wave, which make water molecules in the food jostle back and forth billions of times a second. That jostling is heat. The waves only reach a centimeter or two into most food, so the rest of the heat spreads inward by conduction, the same way it would in a pan.""",
"why does it leave cold spots",
"""The microwaves bounce around the metal box and overlap, creating a fixed pattern of places where the energy is strong and places where it's weak. Food sitting in a weak spot barely heats. The turntable moves food through that pattern, but it can't even everything out, especially in a thick or frozen dish. Stirring partway through, or letting the food stand for a minute or two so the heat spreads, helps a lot."""],

["what's a good stretch for a stiff neck",
"""Sit tall, drop your right ear toward your right shoulder without lifting the shoulder, and hold for twenty to thirty seconds while breathing slowly. Repeat on the left. Then tuck your chin gently toward your chest and hold. Move slowly, and stop if anything feels sharp rather than just tight.""",
"that helped a lot",
"""Glad to hear it. If the stiffness keeps coming back, check your screen height; looking down for hours is a common cause.""",
"will do, bye!",
"""Bye! Take care of that neck."""],
]
