# Short exchanges, mostly the ends of conversations: thanks, "got it", "lol",
# a one-word "yes". The replies stay short, which also gives the model lots of
# practice at stopping as soon as it has said enough.

EXAMPLES = [
["what's the capital of canada",
"""Ottawa. People often guess Toronto or Montreal, the two biggest cities.""",
"oh right",
"""It's an easy one to mix up."""],

["how many tablespoons in a quarter cup",
"""Four.""",
"thanks",
"""You're welcome."""],

("cool thanks",
"""Of course."""),

["can you recommend a podcast about history",
"""Hardcore History, by Dan Carlin, is the classic: long, dramatic episodes on big subjects like the fall of the Roman Republic or the First World War. For shorter episodes, The Rest Is History, with the historians Tom Holland and Dominic Sandbrook, is lively and covers just about everything.""",
"perfect",
"""Enjoy. Fair warning: some of Dan Carlin's episodes run five or six hours."""],

("never mind, figured it out",
"""Glad you got there."""),

["what does RSVP stand for",
"""Répondez s'il vous plaît, French for "please reply." On an invitation, it means the host wants to know whether you're coming, whichever way you decide.""",
"lol i always thought it meant something else",
"""You're far from alone. Plenty of people use it as if it meant "reserve a spot." """.strip()],

["is a peanut a nut",
"""Not botanically. Peanuts are legumes, related to peas and beans, and they grow underground in pods rather than on trees. Cooks group them with nuts because they're used the same way, though a peanut allergy and a tree nut allergy are separate conditions.""",
"huh, i always thought it was a nut",
"""Most people do; the name doesn't help."""],

["when do i use who vs whom",
"""Use who where you'd say he or she, and whom where you'd say him or her. Who called? He called. To whom should I send it? Send it to him. The m in whom matches the m in him.""",
"got it",
"""Good. In casual speech, who is almost always fine; whom mostly matters in formal writing."""],

("bye",
"""Bye. Take care."""),

["tell me a fish pun",
"""What do you call a fish with no eyes? A fsh.""",
"lol",
"""Glad that landed. I have more, but some of them are a bit fishy."""],

["how do i ask for a deadline extension",
"""Ask as early as you can, keep it brief, and propose a specific new date. Something like: "I want to do this properly, and I'm going to need a few more days. Could I hand it in Thursday instead of Monday?" A short reason helps if you have one, but you don't need to over-explain. Asking early, with a plan, reads as responsible rather than disorganized.""",
"thanks, that's really helpful",
"""You're welcome. I hope they say yes."""],

["what's 7 times 8",
"""56.""",
"and 7 times 9",
"""63."""],

["i want to start meditating",
"""A good way to begin is very small: five minutes a day, sitting comfortably and paying attention to your breathing. Your mind will wander constantly, and that's not failure; noticing it wandered and coming back is the whole exercise. A regular time, like right after waking up, makes it easier to keep going. Would you like a simple first exercise?""",
"yes",
"""Sit somewhere quiet and set a timer for five minutes. Close your eyes and count your breaths, one on each exhale, up to ten, then start again at one. Whenever you lose count or catch yourself thinking about something else, just start over at one. That's it."""],

("thank you so much, you've been really helpful",
"""You're very welcome. I'm glad it helped."""),

["is it rude to leave a party without saying goodbye",
"""At a big party, slipping out quietly is usually fine; saying goodbye to everyone would interrupt the host more than it would help. At a small gathering, it's kinder to find the host and thank them before you go.""",
"hmm",
"""Is there a particular party you're thinking about?"""],
]
