SCALE_MAX = 5


def _tiers(mins):
    return [{"min": m, **t} for m, t in zip(mins, TIER_TEXT)]


TIER_TEXT = [
    {"label": "In the Bleachers", "meaning": "You’ve been watching. This movement is where you step on the floor."},
    {"label": "On the Floor", "meaning": "You’ve started. Consistency is your next lift."},
    {"label": "Pressing Forward", "meaning": "You’re growing steadily. Keep pressing toward the goal."},
    {"label": "Training Others", "meaning": "Strength in this area is meant to be shared. Who are you helping grow?"},
]

SECTION_TIERS = _tiers([5, 12, 17, 22])
TOTAL_125_TIERS = _tiers([25, 56, 81, 106])
REVIEW_TIERS = _tiers([15, 34, 49, 64])

SECTIONS = [
    {"id": 1, "title": "From the Bleachers to the Floor", "chapters": "Chapters 1–3"},
    {"id": 2, "title": "What the Weight Costs", "chapters": "Chapters 4–7"},
    {"id": 3, "title": "Every Part Working Together", "chapters": "Chapters 8–10"},
    {"id": 4, "title": "The Daily Work", "chapters": "Chapters 11–14"},
    {"id": 5, "title": "Clean Form", "chapters": "Chapters 15–17"},
]

CORE_QUESTIONS = {
    1: [
        "I serve somewhere in my church regularly enough that my absence would be noticed.",
        "When someone corrects me, I listen and learn before I explain.",
        "When I’m frustrated, I respond with controlled strength rather than harshness.",
        "I remain patient with God when he doesn’t move on my timetable.",
        "I show people love, even when they are difficult to love.",
    ],
    2: [
        "When pressure comes, I ask what Christ is developing in me rather than only how to get out of it.",
        "I honestly bring my weakness into the open instead of hiding it.",
        "When life gets heavy, I move toward prayer rather than isolation.",
        "When fear is loudest, I keep my attention on Jesus instead of letting fear make my decisions.",
        "I let Christ rebuild me through a past wound rather than letting it define my identity.",
    ],
    3: [
        "I am connected to someone in this body closely enough for them to see me struggle.",
        "I intentionally help one other person grow rather than only receiving.",
        "I can serve unnoticed without needing recognition for what I do.",
        "I willingly release real responsibility to someone else without keeping control.",
        "I spend private time with Christ apart from public worship and ministry.",
    ],
    4: [
        "I consistently open the Word and quickly adjust when it confronts me.",
        "Consistent habits mark my life more than inspirational moments.",
        "I am secure in who I am in Christ rather than in the approval of others.",
        "I keep obeying when progress is slow and no one notices.",
        "My private practice prepares me for the weight Christ is adding rather than reaching for a shortcut.",
    ],
    5: [
        "I release what I know is slowing me down.",
        "When the Holy Spirit convicts me, I repent right away rather than renaming it.",
        "I stop tolerating what I am asking God to free me from.",
        "I keep no part of my life off limits to Christ.",
        "Jesus holds the center of my attention and decisions.",
    ],
}

REVIEW_QUESTIONS = {
    2: [
        "I use the gifts Christ gave me to serve the body.",
        "Someone in my church would notice quickly if I began to drift.",
        "I see hardship as evidence that I belong to God, not that he has left me.",
        "I rest before I am depleted, without walking away from the work God gave me.",
        "I pursue growth because I am already God’s child, not to earn His approval.",
        "I am honest about my spiritual condition rather than guessing based on a good Sunday.",
        "When I am wrong, I admit it and apologize.",
        "I am gentle with people who are weaker or slower than I am.",
        "I remain patient with people who test me again and again.",
        "I use my strength to help other people.",
        "I am settled in one church family rather than sampling several.",
        "I let go of good things that compete with what God is building in me.",
        "I keep practicing spiritual disciplines on days I don’t feel like it.",
        "I stay faithful when pressure lasts longer than I expected.",
        "I am ready to be used for something I cannot yet see.",
    ],
    3: [
        "I am willing to stay in a hard season long enough for it to do its work in me.",
        "I am honest with God about my pain while I am still experiencing it.",
        "I measure my trial against what God is forming in me rather than against someone else’s experience.",
        "What I carry has made me more compassionate toward people who are struggling.",
        "I keep trusting God when he seems to step back and let me carry the weight.",
        "I look to God for fresh strength each day rather than relying on yesterday’s.",
        "I keep going with an assignment even when no end date is in sight.",
        "I fix my eyes on what is unseen when what I can see feels heavy.",
        "I take the next step God shows me even when I cannot see the whole plan.",
        "When I start to sink, I cry out to Jesus instead of hiding my failure.",
        "I continue to worship even when my circumstances have not improved.",
        "I accept God’s grace even when he does not remove what I asked him to.",
        "I release to God what I cannot control.",
        "I am ready to ask for help before the weight becomes a crisis.",
        "I am willing to share my story if it helps someone else who is struggling.",
    ],
    4: [
        "I ask for help when the weight is heavier than I can carry alone.",
        "I give a trusted person permission to ask me hard questions.",
        "When conflict comes, I treat the people around me as allies, not enemies.",
        "I support others without taking over what God has asked them to carry.",
        "I stay with people through long seasons, not just a single crisis.",
        "I let others see how I live out my faith, including my struggles.",
        "I see potential in people others have written off.",
        "I celebrate when someone I’ve helped goes further than I have.",
        "I think beyond the person in front of me to the people they will reach.",
        "My life teaches the same thing my words do.",
        "I test the voices shaping me against Scripture.",
        "I do tasks that seem beneath my title or experience.",
        "I serve with discernment, recognizing which needs are mine to meet.",
        "I give even when it disrupts my schedule, comfort, or plans.",
        "When someone in my church family is hurting, I show up to help them rebuild.",
    ],
    5: [
        "I am hungry for God’s Word and do not treat it merely as an obligation.",
        "I slow down to meditate on Scripture rather than rushing to the next thing.",
        "I pass on to others what God is teaching me.",
        "I depend on the strength of the Lord rather than relying on my own strength.",
        "I put on the whole armor of God rather than only the pieces I find easiest to embrace.",
        "I can name specifically what is opposing me spiritually.",
        "I continue to stand firm after I have done everything I know to do.",
        "I pray, worship, serve, and obey even when my feelings resist.",
        "When I am tired, I rest without retreating from what God has asked of me.",
        "When I miss a day, I pick back up the next day instead of quitting.",
        "I am faithful with the small responsibilities God has already entrusted to me.",
        "I remember and record what God has done in me, so discouragement does not get the final word.",
        "I measure the giants in front of me against what God has already done, not against their size.",
        "I refuse to step outside God’s ways to reach something I believe he has promised.",
        "My prayer life is about being near God, not only asking him for things.",
    ],
    6: [
        "I am honest about good things in my life that have grown heavy enough to slow me down.",
        "I do not defend what God is asking me to release.",
        "I rely on God’s grace to break what entangles me, not just to excuse it.",
        "I take the next step toward God’s purpose instead of leaving it for someday.",
        "I keep running the course God marked out after something has been cut away.",
        "I let God deal with my character before I ask him for more responsibility.",
        "I do not let past faithfulness excuse present compromise.",
        "I confront what is contaminating me instead of managing it.",
        "I cut off the access point of a compromise, not just the behavior.",
        "I guard what I feed my mind, because it shapes my heart.",
        "I do not let my strengths or successes make a compromise feel safe.",
        "I notice when something I have tolerated has started making my decisions.",
        "I listen when trusted people point out what I have stopped noticing.",
        "I deal with long-standing compromises even when everyone, including me, is used to them.",
        "I refuse to go back to what God has already set me free from.",
    ],
}


def _core(aid):
    return [
        {"id": f"a{aid}s{s}q{i + 1}", "text": t, "section": s}
        for s, qs in CORE_QUESTIONS.items()
        for i, t in enumerate(qs)
    ]


def _review(aid):
    return [{"id": f"a{aid}q{i + 1}", "text": t, "section": None} for i, t in enumerate(REVIEW_QUESTIONS[aid])]


REVIEW_META = {
    2: ("Section One Review", "Chapters 1–3"),
    3: ("Section Two Review", "Chapters 4–7"),
    4: ("Section Three Review", "Chapters 8–10"),
    5: ("Section Four Review", "Chapters 11–14"),
    6: ("Section Five Review", "Chapters 15–17"),
}

ASSESSMENTS = [
    {
        "id": 1, "title": "Initial Spiritual Assessment", "subtitle": "Day 1 Baseline",
        "description": "25 questions across the five sections of the book. Each section is scored out of 25.",
        "questions": _core(1), "has_sections": True,
        "total_tiers": TOTAL_125_TIERS, "section_tiers": SECTION_TIERS,
    },
    *[
        {
            "id": aid, "title": title, "subtitle": chapters,
            "description": f"15 questions reviewing {chapters}. Scored out of 75.",
            "questions": _review(aid), "has_sections": False,
            "total_tiers": REVIEW_TIERS, "section_tiers": None,
        }
        for aid, (title, chapters) in REVIEW_META.items()
    ],
    {
        "id": 7, "title": "Spiritual Progress Assessment", "subtitle": "Today",
        "description": "The same 25 questions from Day 1. Scored per section out of 25 and in total out of 125.",
        "questions": _core(7), "has_sections": True,
        "total_tiers": TOTAL_125_TIERS, "section_tiers": SECTION_TIERS,
    },
]

BASELINE_ASSESSMENT_ID = 1
FINAL_ASSESSMENT_ID = 7

SECTION_REVIEW_IDS = list(REVIEW_META)

for _a in ASSESSMENTS:
    _a["kind"] = {1: "initial", 7: "final"}.get(_a["id"], "section")
    _a["tier"] = "free" if _a["id"] == 1 else "paid"
