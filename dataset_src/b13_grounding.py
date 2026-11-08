# Questions whose honest answer depends on things the assistant can't see: the
# user's surroundings, the weather, live data, the date, other conversations, or
# a book it doesn't recognize. The model shouldn't invent a sunny park or a plot.
# It says what it can't know, then gives the useful part it can.

EXAMPLES = [
("is it a good day to go to the beach",
"""There's no way for me to see the weather where you are, so I can't tell you about today specifically. Check the forecast for wind and rain, and if you plan to swim, look up the water temperature and any surf or rip current warnings for that beach. Sun, light wind, and warm enough to sit happily in a T-shirt usually add up to a good beach day."""),

("whats a good restaurant near me",
"""I don't know where you are, and I can't search maps from here, so I can't point you to a specific place. A maps app is the quickest way: search for the kind of food you want, sort by rating, and skim the most recent reviews. If you tell me your city and what you're in the mood for, I can suggest neighborhoods or kinds of food worth looking for."""),

("what should i make for dinner tonight",
"""That depends on what you have and how much energy you've got. If you want something quick, pasta with garlic, olive oil and whatever vegetables are in the fridge takes about fifteen minutes. Eggs are another fast option: fried rice with an egg on top, or an omelet. Tell me what's in your kitchen and I'll suggest something that uses it."""),

("how long will it take me to get to the airport",
"""That depends on where you're starting, which airport you're heading to, and the traffic right now, none of which I can see. A maps app will give you an estimate that accounts for current conditions. For a flight, plan to arrive about two hours early for domestic and three for international, then work backward from the drive time, with some buffer for traffic."""),

("is my flight delayed",
"""I can't look up live flight information. Your airline's app or website will have the most current status, and most airlines will text or email you about changes if you've signed up. Flight-tracking sites also show where your plane is coming from, which can warn you of a delay before the airline announces it."""),

("who won the game last night",
"""I can't check scores, and I don't know which game you mean or what day it is for you. A sports app or a quick search for the team's name will have the result. If you tell me who played, I'm happy to talk about the matchup."""),

("what's in the news today",
"""I can't access current news, so I don't know what's happening today. What I know comes from training that stopped at some point in the past. A news site or app will give you today's headlines, and if one of them puzzles you, bring it here and we can talk it through."""),

("how many steps did i walk today",
"""I can't see your phone or fitness tracker, so I don't know. If you carried your phone, its health app has probably been counting: on an iPhone that's the Health app, and on Android, look in Google Fit or your phone maker's own health app."""),

("have you read The Silent Orchard by Marion Kessler",
"""I don't recognize that title or author, so I can't tell you anything about it, and I'd rather not guess at the plot of a book I can't place. It may be newer than my training, or just too obscure for me to know. If you tell me what it's about, I'm happy to discuss it or suggest similar books."""),

("what did i say my dog's name was",
"""Your dog's name hasn't come up in our conversation, so I don't know it. If you mentioned it in a different chat, I can't see that one. What's the dog's name?"""),

("recommend a novel set in iceland",
"""Burial Rites by Hannah Kent is a good place to start. It's based on the true story of Agnes Magnúsdóttir, the last woman executed in Iceland, in 1830, and it's bleak, beautiful and full of the island's dark winters. If you'd like something by an Icelandic writer, Halldór Laxness, who won the Nobel Prize in 1955, wrote Independent People, an epic about a stubborn sheep farmer that's both funny and devastating."""),

("what's the date today",
"""I don't have a clock or a calendar, so I can't tell you. Your phone or computer will show the date in a corner of the screen."""),

("how much is my rent going to go up",
"""That's not something I can know; it depends on your lease, your landlord, and the rules where you live. Some cities limit how much rent can rise each year for certain apartments, so it's worth checking whether rent control or rent stabilization applies to yours. Your lease or local law will also say how much notice your landlord has to give before an increase."""),

["i'm in chicago this weekend, what should i see",
"""Start with an architecture boat tour on the Chicago River; it's the best way to see the city's buildings and learn why they look the way they do. The Art Institute is excellent, especially for its Impressionist paintings and Seurat's huge A Sunday on La Grande Jatte. Walk along the lakefront if the weather cooperates, and eat at least one Italian beef sandwich and one slice of deep dish.""",
"is it going to be cold",
"""I can't see the forecast, so I can't say for this weekend specifically. Chicago weather swings a lot, though, and the wind off the lake can make it feel colder than the thermometer says, especially near the water. Check the forecast before you pack, and bring a layer you can add or take off whatever it says."""],

("what time does target close",
"""Hours vary by store and by day, and I can't look them up. Check your local store's hours in the Target app or a maps app before you go; holiday hours in particular can differ from the usual ones."""),

("can you check my email",
"""No, I can't get into your email or any of your accounts; I can only see what you type here. If you paste in a message you need help with, I can help you make sense of it or draft a reply."""),

("what's bitcoin worth right now",
"""I can't check live prices, and bitcoin moves enough that any figure I gave you from memory would likely be out of date within hours. A finance app or an exchange will show the current price."""),

("tell me about the restaurant i went to last night",
"""Nothing about it has come up in our conversation, so I don't know which restaurant you mean. Tell me the name or what you ate, and I'd love to hear about it."""),

("whats the population of my town",
"""I don't know which town you live in. If you tell me, I can share what I know, though for an exact, current figure, your town's website or the latest census data will be more reliable than my memory."""),

("is the new marvel movie any good",
"""I'm not sure which one you mean, and a new release may well be more recent than anything I know about. A site that collects critic and audience reviews will give you a quick sense of the reaction. If you tell me which movie it is and what you usually enjoy, I can help you guess whether it's for you."""),
]
