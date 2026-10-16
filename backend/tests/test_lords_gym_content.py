# Lord's Gym iteration 2: real content, scoring tiers, section scores, master results, auth regressions
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api"

SECTION_TITLES = ["From the Bleachers to the Floor", "What the Weight Costs", "Every Part Working Together", "The Daily Work", "Clean Form"]
CHAPTERS = ["Chapters 1–3", "Chapters 4–7", "Chapters 8–10", "Chapters 11–14", "Chapters 15–17"]
TITLES = {1: "Initial Spiritual Assessment", 2: "Section One Review", 3: "Section Two Review", 4: "Section Three Review",
          5: "Section Four Review", 6: "Section Five Review", 7: "Spiritual Progress Assessment"}


def new_session():
    s = requests.Session()
    email = f"TEST_user_{uuid.uuid4().hex[:8]}@example.com"
    r = s.post(f"{API}/auth/register", json={"name": "Tester Bob", "email": email, "password": "test1234"})
    assert r.status_code == 200, r.text
    return s, email


def core(aid, v):
    """v: int or dict section->int or callable(section, q)"""
    out = {}
    for sec in range(1, 6):
        for q in range(1, 6):
            if callable(v):
                out[f"a{aid}s{sec}q{q}"] = v(sec, q)
            elif isinstance(v, dict):
                out[f"a{aid}s{sec}q{q}"] = v[sec]
            else:
                out[f"a{aid}s{sec}q{q}"] = v
    return out


def review(aid, v):
    if isinstance(v, list):
        return {f"a{aid}q{i + 1}": v[i] for i in range(15)}
    return {f"a{aid}q{i}": v for i in range(1, 16)}


def complete_through(s, upto, a1=3, rv=3):
    for aid in range(1, upto + 1):
        ans = core(aid, a1) if aid in (1, 7) else review(aid, rv)
        r = s.post(f"{API}/assessments/{aid}/submit", json={"answers": ans})
        assert r.status_code == 200, (aid, r.text)


class TestContent:
    def test_list_titles_and_counts(self):
        s, _ = new_session()
        d = s.get(f"{API}/assessments").json()["assessments"]
        assert [a["title"] for a in d] == [TITLES[i] for i in range(1, 8)]
        assert [a["question_count"] for a in d] == [25, 15, 15, 15, 15, 15, 25]

    def test_a1_questions_and_sections(self):
        s, _ = new_session()
        d = s.get(f"{API}/assessments/1").json()
        assert len(d["questions"]) == 25
        assert [x["title"] for x in d["sections"]] == SECTION_TITLES
        assert [x["chapters"] for x in d["sections"]] == CHAPTERS
        assert d["questions"][0]["id"] == "a1s1q1" and d["questions"][0]["section"] == 1
        assert d["questions"][24]["id"] == "a1s5q5" and d["questions"][24]["section"] == 5

    def test_a7_same_questions_as_a1(self):
        s, _ = new_session()
        complete_through(s, 6)
        a1 = s.get(f"{API}/assessments/1").json()
        a7 = s.get(f"{API}/assessments/7").json()
        assert [q["text"] for q in a7["questions"]] == [q["text"] for q in a1["questions"]]
        assert a7["questions"][0]["id"] == "a7s1q1"


class TestScoring:
    @pytest.mark.parametrize("v,score,label", [(2, 30, "In the Bleachers"), (3, 45, "On the Floor"), (4, 60, "Pressing Forward"), (5, 75, "Training Others"), (1, 15, "In the Bleachers")])
    def test_review_tiers(self, v, score, label):
        s, _ = new_session()
        complete_through(s, 1)
        r = s.post(f"{API}/assessments/2/submit", json={"answers": review(2, v)}).json()
        assert r["score"] == score and r["max_score"] == 75 and r["designation"] == label
        assert r["sections"] == []

    def test_review_boundaries(self):
        s, _ = new_session()
        complete_through(s, 1)
        # 33 -> Bleachers: 3*2 + 12*... use list: 12 twos + 3 threes = 33
        r = s.post(f"{API}/assessments/2/submit", json={"answers": review(2, [2] * 12 + [3] * 3)}).json()
        assert r["score"] == 33 and r["designation"] == "In the Bleachers"
        r = s.post(f"{API}/assessments/3/submit", json={"answers": review(3, [2] * 11 + [3] * 4)}).json()
        assert r["score"] == 34 and r["designation"] == "On the Floor"
        r = s.post(f"{API}/assessments/4/submit", json={"answers": review(4, [3] * 11 + [4] * 4)}).json()
        assert r["score"] == 49 and r["designation"] == "Pressing Forward"
        r = s.post(f"{API}/assessments/5/submit", json={"answers": review(5, [4] * 11 + [5] * 4)}).json()
        assert r["score"] == 64 and r["designation"] == "Training Others"
        r = s.post(f"{API}/assessments/6/submit", json={"answers": review(6, [4] * 12 + [5] * 3)}).json()
        assert r["score"] == 63 and r["designation"] == "Pressing Forward"

    def test_a1_sections_mixed(self):
        s, _ = new_session()
        r = s.post(f"{API}/assessments/1/submit", json={"answers": core(1, {1: 1, 2: 2, 3: 3, 4: 4, 5: 5})}).json()
        assert r["score"] == 75 and r["max_score"] == 125 and r["designation"] == "On the Floor"
        secs = r["sections"]
        assert [x["score"] for x in secs] == [5, 10, 15, 20, 25]
        assert [x["max"] for x in secs] == [25] * 5
        assert [x["designation"] for x in secs] == ["In the Bleachers", "In the Bleachers", "On the Floor", "Pressing Forward", "Training Others"]
        assert all(x["meaning"] for x in secs)
        assert [x["title"] for x in secs] == SECTION_TITLES
        g = s.get(f"{API}/assessments/1/result").json()
        assert g["sections"] == secs

    def test_section_boundaries(self):
        # section scores 11,12,16,17,21 and check; section 22 via another
        s, _ = new_session()
        def f(sec, q):
            base = {1: [3, 2, 2, 2, 2], 2: [3, 3, 2, 2, 2], 3: [4, 3, 3, 3, 3], 4: [4, 4, 3, 3, 3], 5: [5, 4, 4, 4, 4]}
            return base[sec][q - 1]
        r = s.post(f"{API}/assessments/1/submit", json={"answers": core(1, f)}).json()
        assert [x["score"] for x in r["sections"]] == [11, 12, 16, 17, 21]
        assert [x["designation"] for x in r["sections"]] == ["In the Bleachers", "On the Floor", "On the Floor", "Pressing Forward", "Pressing Forward"]
        assert r["score"] == 77 and r["designation"] == "On the Floor"

    def test_a7_total_tiers(self):
        s, _ = new_session()
        complete_through(s, 6)
        r = s.post(f"{API}/assessments/7/submit", json={"answers": core(7, 4)}).json()
        assert r["score"] == 100 and r["max_score"] == 125 and r["designation"] == "Pressing Forward"
        assert all(x["score"] == 20 and x["designation"] == "Pressing Forward" for x in r["sections"])

    def test_total_125_boundaries(self):
        cases = [(2, 50, "In the Bleachers"), (5, 125, "Training Others"), (1, 25, "In the Bleachers")]
        for v, score, label in cases:
            s, _ = new_session()
            r = s.post(f"{API}/assessments/1/submit", json={"answers": core(1, v)}).json()
            assert (r["score"], r["designation"]) == (score, label)
        # 55/56, 80/81, 105/106
        for target, label in [(55, "In the Bleachers"), (56, "On the Floor"), (80, "On the Floor"), (81, "Pressing Forward"), (105, "Pressing Forward"), (106, "Training Others")]:
            s, _ = new_session()
            vals = [target // 25] * 25
            for i in range(target - sum(vals)):
                vals[i] += 1
            it = iter(vals)
            r = s.post(f"{API}/assessments/1/submit", json={"answers": core(1, lambda a, b: next(it))}).json()
            assert (r["score"], r["designation"]) == (target, label), r


class TestMaster:
    def test_master_rows(self):
        s, _ = new_session()
        complete_through(s, 6, a1=2, rv=4)
        r = s.post(f"{API}/assessments/7/submit", json={"answers": core(7, {1: 5, 2: 4, 3: 3, 4: 2, 5: 1})})
        assert r.status_code == 200
        d = s.get(f"{API}/master-results").json()
        assert [x["section"] for x in d["rows"]] == SECTION_TITLES
        assert [x["chapters"] for x in d["rows"]] == CHAPTERS
        assert [x["day1"] for x in d["rows"]] == [10] * 5
        assert [x["today"] for x in d["rows"]] == [25, 20, 15, 10, 5]
        assert [x["change"] for x in d["rows"]] == [15, 10, 5, 0, -5]
        assert d["total"] == {"day1": 50, "today": 75, "change": 25, "max": 125}


class TestAuthRegression:
    def test_brute_force_lockout_429(self):
        s, email = new_session()
        codes = [requests.post(f"{API}/auth/login", json={"email": email, "password": "nope12"}).status_code for _ in range(6)]
        assert codes[:5] == [401] * 5, codes
        assert codes[5] == 429, codes
        # correct password also blocked during lockout
        assert requests.post(f"{API}/auth/login", json={"email": email, "password": "test1234"}).status_code == 429

    def test_smoke_user_results(self):
        s = requests.Session()
        r = s.post(f"{API}/auth/login", json={"email": "test_smoke@example.com", "password": "test1234"})
        if r.status_code != 200:
            pytest.skip("smoke user unavailable")
        for aid in range(1, 8):
            assert s.get(f"{API}/assessments/{aid}/result").status_code == 200, aid
        d = s.get(f"{API}/master-results").json()
        assert d["total"]["day1"] == 50 and d["total"]["today"] == 125
