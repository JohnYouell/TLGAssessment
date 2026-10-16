SCALE_MAX = 5

SECTIONS = [
    {"id": i, "title": f"Section {i}", "chapters": f"Chapter {i}"} for i in range(1, 6)
]

DEFAULT_BANDS = [
    {"min_pct": 0, "label": "Warm-Up", "meaning": "Placeholder meaning text: you are at the beginning of this discipline. Every champion started with a first rep."},
    {"min_pct": 40, "label": "Building Strength", "meaning": "Placeholder meaning text: the foundation is forming. Keep showing up and the reps will compound."},
    {"min_pct": 65, "label": "Conditioned", "meaning": "Placeholder meaning text: this discipline is becoming part of your daily walk. Stay consistent."},
    {"min_pct": 85, "label": "Battle-Ready", "meaning": "Placeholder meaning text: you are consistently strong here, even under pressure. Help train others."},
]


def _questions(n):
    return [
        {"id": f"a{n}q{q}", "text": f"Placeholder question {q} for Assessment {n}.", "section": q}
        for q in range(1, 4)
    ]


ASSESSMENTS = [
    {
        "id": n,
        "title": f"Assessment {n}",
        "subtitle": f"Chapter {n}",
        "description": f"Placeholder description for Assessment {n}.",
        "questions": _questions(n),
        "bands": DEFAULT_BANDS,
    }
    for n in range(1, 8)
]

BASELINE_ASSESSMENT_ID = 1
FINAL_ASSESSMENT_ID = 7
