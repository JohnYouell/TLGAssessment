# Lord's Gym iteration 3: marketing_opt_in capture at signup + PDF Training Scorecard endpoint
import os
import uuid
import fitz  # pymupdf
import pytest
import requests
from pymongo import MongoClient

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api"

SECTION_TITLES = ["From the Bleachers to the Floor", "What the Weight Costs", "Every Part Working Together", "The Daily Work", "Clean Form"]
CHAPTERS = ["Chapters 1–3", "Chapters 4–7", "Chapters 8–10", "Chapters 11–14", "Chapters 15–17"]


def _db():
    env = {}
    for line in open("/app/backend/.env"):
        if "=" in line:
            k, v = line.strip().split("=", 1)
            env[k] = v.strip('"')
    return MongoClient(env["MONGO_URL"])[env["DB_NAME"]]


def register(opt=None, name="TEST Scorecard Athlete"):
    s = requests.Session()
    email = f"TEST_pdf_{uuid.uuid4().hex[:8]}@example.com"
    body = {"name": name, "email": email, "password": "test1234"}
    if opt is not None:
        body["marketing_opt_in"] = opt
    r = s.post(f"{API}/auth/register", json=body)
    assert r.status_code == 200, r.text
    return s, email.lower(), r.json()


def core(aid, v):
    return {f"a{aid}s{sec}q{q}": (v[sec] if isinstance(v, dict) else v) for sec in range(1, 6) for q in range(1, 6)}


def complete_all(s, a1=2, a7=None):
    for aid in range(1, 8):
        if aid == 1:
            ans = core(1, a1)
        elif aid == 7:
            ans = core(7, a7 if a7 is not None else 4)
        else:
            ans = {f"a{aid}q{i}": 3 for i in range(1, 16)}
        r = s.post(f"{API}/assessments/{aid}/submit", json={"answers": ans})
        assert r.status_code == 200, (aid, r.text)


# --- marketing_opt_in ---
class TestOptIn:
    @pytest.mark.parametrize("opt", [True, False])
    def test_optin_persisted(self, opt):
        s, email, data = register(opt)
        assert data["marketing_opt_in"] is opt
        assert s.get(f"{API}/auth/me").json()["marketing_opt_in"] is opt
        doc = _db().users.find_one({"email": email})
        assert doc["marketing_opt_in"] is opt

    def test_optin_default_false(self):
        s, email, data = register(None)
        assert data["marketing_opt_in"] is False
        assert _db().users.find_one({"email": email})["marketing_opt_in"] is False

    def test_optin_survives_login(self):
        s, email, _ = register(True)
        r = requests.post(f"{API}/auth/login", json={"email": email, "password": "test1234"})
        assert r.status_code == 200
        assert r.json()["marketing_opt_in"] is True


# --- scorecard PDF ---
class TestScorecard:
    def test_unauthenticated_401(self):
        assert requests.get(f"{API}/master-results/scorecard").status_code == 401

    def test_incomplete_403(self):
        s, _, _ = register(False)
        assert s.get(f"{API}/master-results/scorecard").status_code == 403
        r = s.post(f"{API}/assessments/1/submit", json={"answers": core(1, 3)})
        assert r.status_code == 200
        assert s.get(f"{API}/master-results/scorecard").status_code == 403

    def test_pdf_ok_and_content(self):
        s, _, _ = register(True, name="TEST Scorecard Athlete")
        complete_all(s, a1={1: 1, 2: 2, 3: 3, 4: 4, 5: 5}, a7={1: 5, 2: 4, 3: 3, 4: 2, 5: 1})
        m = s.get(f"{API}/master-results").json()
        r = s.get(f"{API}/master-results/scorecard")
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("application/pdf")
        cd = r.headers.get("content-disposition", "")
        assert "attachment" in cd and "Lords-Gym-Training-Scorecard.pdf" in cd
        assert r.content[:5] == b"%PDF-"
        doc = fitz.open(stream=r.content, filetype="pdf")
        assert doc.page_count == 1
        text = doc[0].get_text()
        for t in SECTION_TITLES + CHAPTERS:
            assert t in text, t
        assert "TOTAL OUT OF 125" in text
        assert "TEST Scorecard Athlete" in text
        assert "TRAINING SCORECARD" in text
        for row in m["rows"]:
            assert f"{row['day1']} / {row['max']}" in text
            assert f"{row['today']} / {row['max']}" in text
        # changes +20,+10,0,-10,-20
        for c in ["+20", "+10", "-10", "-20"]:
            assert c in text, c
        assert m["total"]["day1"] == 75 and m["total"]["today"] == 75 and m["total"]["change"] == 0

    def test_existing_pdf_user(self):
        s = requests.Session()
        r = s.post(f"{API}/auth/login", json={"email": "test_pdf@example.com", "password": "test1234"})
        if r.status_code != 200:
            pytest.skip("test_pdf user unavailable")
        r = s.get(f"{API}/master-results/scorecard")
        assert r.status_code == 200 and r.content[:5] == b"%PDF-"
