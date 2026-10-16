# Lord's Gym API regression tests: auth, assessments sequencing, results, master results
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api"


def new_session():
    s = requests.Session()
    email = f"TEST_user_{uuid.uuid4().hex[:8]}@example.com"
    r = s.post(f"{API}/auth/register", json={"name": "Tester Bob", "email": email, "password": "test1234", "marketing_opt_in": True})
    assert r.status_code == 200, r.text
    return s, email, r.json()


def answers(aid, v):
    return {f"a{aid}q{q}": (v[q - 1] if isinstance(v, list) else v) for q in range(1, 4)}


# --- Auth ---
class TestAuth:
    def test_register_sets_cookies_and_returns_user(self):
        s, email, data = new_session()
        assert data["email"] == email.lower()
        assert data["name"] == "Tester Bob"
        assert data["marketing_opt_in"] is True
        assert "password_hash" not in data
        assert "access_token" in s.cookies and "refresh_token" in s.cookies

    def test_cookie_flags(self):
        email = f"TEST_user_{uuid.uuid4().hex[:8]}@example.com"
        r = requests.post(f"{API}/auth/register", json={"name": "X", "email": email, "password": "test1234"})
        sc = r.headers.get("set-cookie", "").lower()
        assert "httponly" in sc and "secure" in sc and "samesite=none" in sc

    def test_duplicate_register(self):
        s, email, _ = new_session()
        r = requests.post(f"{API}/auth/register", json={"name": "X", "email": email, "password": "test1234"})
        assert r.status_code == 400

    def test_register_validation(self):
        r = requests.post(f"{API}/auth/register", json={"name": "X", "email": "bad", "password": "1"})
        assert r.status_code == 422

    def test_me_and_login(self):
        s, email, _ = new_session()
        assert s.get(f"{API}/auth/me").json()["email"] == email.lower()
        r = requests.post(f"{API}/auth/login", json={"email": email, "password": "wrongpw"})
        assert r.status_code == 401
        s2 = requests.Session()
        r = s2.post(f"{API}/auth/login", json={"email": email, "password": "test1234"})
        assert r.status_code == 200 and r.json()["email"] == email.lower()
        assert s2.get(f"{API}/auth/me").status_code == 200

    def test_unauthenticated(self):
        assert requests.get(f"{API}/auth/me").status_code == 401
        assert requests.get(f"{API}/assessments").status_code == 401

    def test_refresh_and_logout(self):
        s, _, _ = new_session()
        assert s.post(f"{API}/auth/refresh").status_code == 200
        r = s.post(f"{API}/auth/logout")
        assert r.status_code == 200
        assert s.get(f"{API}/auth/me").status_code == 401

    def test_brute_force_lockout(self):
        s, email, _ = new_session()
        codes = [requests.post(f"{API}/auth/login", json={"email": email, "password": "nope12"}).status_code for _ in range(6)]
        assert codes[:5] == [401] * 5
        assert codes[5] == 429

    def test_cors_credentials(self):
        r = requests.options(f"{API}/auth/me", headers={"Origin": BASE_URL, "Access-Control-Request-Method": "GET"})
        assert r.headers.get("access-control-allow-origin") == BASE_URL
        assert r.headers.get("access-control-allow-credentials") == "true"


# --- Assessments ---
class TestAssessments:
    def test_initial_list(self):
        s, _, _ = new_session()
        d = s.get(f"{API}/assessments").json()
        assert len(d["assessments"]) == 7
        assert [a["unlocked"] for a in d["assessments"]] == [True] + [False] * 6
        assert all(a["status"] == "not_started" for a in d["assessments"])
        assert d["master_unlocked"] is False

    def test_sequential_enforcement(self):
        s, _, _ = new_session()
        assert s.get(f"{API}/assessments/3").status_code == 403
        assert s.put(f"{API}/assessments/3/progress", json={"answers": answers(3, 3)}).status_code == 403
        assert s.post(f"{API}/assessments/3/submit", json={"answers": answers(3, 3)}).status_code == 403
        assert s.get(f"{API}/assessments/99").status_code == 404

    def test_progress_and_submit(self):
        s, _, _ = new_session()
        r = s.put(f"{API}/assessments/1/progress", json={"answers": {"a1s1q1": 2, "bogus": 3, "a1s1q2": 9}})
        assert r.status_code == 200 and r.json()["answered_count"] == 1
        a1 = s.get(f"{API}/assessments").json()["assessments"][0]
        assert a1["status"] == "in_progress" and a1["answered_count"] == 1
        assert s.get(f"{API}/assessments/1").json()["answers"] == {"a1s1q1": 2}
        assert s.post(f"{API}/assessments/1/submit", json={"answers": {"a1s1q1": 2}}).status_code == 400
        assert s.get(f"{API}/assessments/1/result").status_code == 404
        full = {f"a1s{a}q{b}": 5 for a in range(1, 6) for b in range(1, 6)}
        r = s.post(f"{API}/assessments/1/submit", json={"answers": full})
        assert r.status_code == 200 and r.json()["score"] == 125 and r.json()["designation"] == "Training Others"
        lst = s.get(f"{API}/assessments").json()["assessments"]
        assert lst[0]["status"] == "completed" and lst[1]["unlocked"] is True and lst[2]["unlocked"] is False
        assert s.post(f"{API}/assessments/1/submit", json={"answers": full}).status_code == 400
        assert s.put(f"{API}/assessments/1/progress", json={"answers": full}).status_code == 400
    # Scoring tiers & master results moved to test_lords_gym_content.py (iteration 2 real content)
