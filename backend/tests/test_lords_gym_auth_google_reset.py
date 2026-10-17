# Auth tests: email/password regression, Google (error path), forgot/reset password, refresh, token_version
import os
import hashlib
import secrets
import uuid
from datetime import datetime, timezone, timedelta

import bcrypt
import pytest
import requests
from pymongo import MongoClient
from bson import ObjectId


def _env(path, key):
    for line in open(path):
        if line.startswith(key + "="):
            return line.split("=", 1)[1].strip().strip('"')


BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or _env("/app/frontend/.env", "REACT_APP_BACKEND_URL")).rstrip("/")
MONGO_URL = _env("/app/backend/.env", "MONGO_URL")
DB_NAME = _env("/app/backend/.env", "DB_NAME")
db = MongoClient(MONGO_URL)[DB_NAME]
PW = "test1234"


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def seed_user(email, password=PW, **extra):
    doc = {"name": "TEST User", "email": email.lower(),
           "password_hash": bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode() if password else "",
           "marketing_opt_in": False, "created_at": now_iso(), "last_activity_at": now_iso(),
           "has_access": False, "final_video_watched": False, "token_version": 0, **extra}
    return str(db.users.insert_one(doc).inserted_id)


def seed_token(uid, email, expires_delta=timedelta(hours=1), used=False):
    raw = secrets.token_urlsafe(32)
    db.password_reset_tokens.insert_one({"token_hash": hashlib.sha256(raw.encode()).hexdigest(), "user_id": uid,
                                         "email": email, "used": used, "created_at": now_iso(),
                                         "expires_at": datetime.now(timezone.utc) + expires_delta})
    return raw


CREATED = []


def em():
    e = f"test_auth_{uuid.uuid4().hex[:8]}@example.com"
    CREATED.append(e)
    return e


def cookie_header(s):
    return "; ".join(f"{c.name}={c.value}" for c in s.cookies)


@pytest.fixture(scope="module", autouse=True)
def cleanup():
    yield
    # only this worker's users (safe under pytest-xdist)
    ids = [str(u["_id"]) for u in db.users.find({"email": {"$in": CREATED}})]
    db.progress.delete_many({"user_id": {"$in": ids}})
    db.password_reset_tokens.delete_many({"email": {"$in": CREATED}})
    db.login_attempts.delete_many({"identifier": {"$in": CREATED}})
    db.users.delete_many({"email": {"$in": CREATED}})


# --- Email/password regression ---
class TestPasswordAuth:
    def test_login_me_logout(self):
        e = em(); seed_user(e)
        s = requests.Session()
        r = s.post(f"{BASE_URL}/api/auth/login", json={"email": e, "password": PW})
        assert r.status_code == 200 and r.json()["email"] == e
        sc = r.headers.get("set-cookie", "")
        assert "access_token" in sc and "HttpOnly" in sc and "refresh_token" in sc
        me = s.get(f"{BASE_URL}/api/auth/me")
        assert me.status_code == 200 and me.json()["email"] == e and "_id" not in me.json()
        assert s.post(f"{BASE_URL}/api/auth/logout").status_code == 200
        s.cookies.clear()
        assert s.get(f"{BASE_URL}/api/auth/me").status_code == 401

    def test_wrong_password(self):
        e = em(); seed_user(e)
        assert requests.post(f"{BASE_URL}/api/auth/login", json={"email": e, "password": "nope999"}).status_code == 401

    def test_google_only_user_password_login_401(self):
        e = em(); seed_user(e, password=None, google_id="g123")
        r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": e, "password": "anything"})
        assert r.status_code == 401
        r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": e, "password": ""})
        assert r.status_code == 401

    def test_lockout(self):
        e = em(); seed_user(e)
        codes = [requests.post(f"{BASE_URL}/api/auth/login", json={"email": e, "password": "bad123"}).status_code for _ in range(6)]
        assert codes[:5] == [401] * 5 and codes[5] == 429

    def test_refresh(self):
        e = em(); seed_user(e)
        s = requests.Session()
        s.post(f"{BASE_URL}/api/auth/login", json={"email": e, "password": PW})
        r = s.post(f"{BASE_URL}/api/auth/refresh")
        assert r.status_code == 200 and r.json() == {"ok": True}
        assert "access_token" in r.headers.get("set-cookie", "")
        assert s.get(f"{BASE_URL}/api/auth/me").status_code == 200
        assert requests.post(f"{BASE_URL}/api/auth/refresh").status_code == 401

    def test_register_regression(self):
        e = em()
        s = requests.Session()
        r = s.post(f"{BASE_URL}/api/auth/register", json={"name": "TEST Reg", "email": e, "password": PW, "marketing_opt_in": False})
        assert r.status_code == 200 and r.json()["email"] == e
        u = db.users.find_one({"email": e})
        assert u["password_hash"].startswith("$2b$")
        assert s.get(f"{BASE_URL}/api/auth/me").json()["email"] == e


# --- Google ---
class TestGoogle:
    def test_bad_session(self):
        r = requests.post(f"{BASE_URL}/api/auth/google", json={"session_id": "invalid"})
        assert r.status_code == 401 and "Google" in r.json()["detail"]

    def test_empty_session_422(self):
        assert requests.post(f"{BASE_URL}/api/auth/google", json={"session_id": ""}).status_code == 422


# --- Forgot / reset ---
class TestForgotReset:
    def test_forgot_unknown_same_response(self):
        r = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={"email": em()})
        assert r.status_code == 200 and r.json() == {"ok": True}

    def test_forgot_invalid_email_422(self):
        assert requests.post(f"{BASE_URL}/api/auth/forgot-password", json={"email": "notanemail"}).status_code == 422

    def test_forgot_rate_limit(self):
        e = em(); uid = seed_user(e)
        # pre-seed 3 recent tokens, so we don't send real emails
        for _ in range(3):
            seed_token(uid, e)
        r = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={"email": e.upper()})
        assert r.status_code == 200 and r.json() == {"ok": True}
        assert db.password_reset_tokens.count_documents({"email": e}) == 3

    def test_forgot_creates_token(self):
        e = em(); seed_user(e)
        r = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={"email": e})
        assert r.status_code == 200
        doc = db.password_reset_tokens.find_one({"email": e})
        assert doc and doc["used"] is False and len(doc["token_hash"]) == 64

    def test_reset_full_flow(self):
        e = em(); uid = seed_user(e)
        old = requests.Session()
        assert old.post(f"{BASE_URL}/api/auth/login", json={"email": e, "password": PW}).status_code == 200
        raw = seed_token(uid, e)
        s = requests.Session()
        r = s.post(f"{BASE_URL}/api/auth/reset-password", json={"token": raw, "password": "newpass99"})
        assert r.status_code == 200 and r.json()["email"] == e
        assert s.get(f"{BASE_URL}/api/auth/me").status_code == 200
        assert db.users.find_one({"_id": ObjectId(uid)})["token_version"] == 1
        # old session dead (access + refresh)
        assert old.get(f"{BASE_URL}/api/auth/me").status_code == 401
        assert old.post(f"{BASE_URL}/api/auth/refresh").status_code == 401
        # old pw fails, new works
        assert requests.post(f"{BASE_URL}/api/auth/login", json={"email": e, "password": PW}).status_code == 401
        assert requests.post(f"{BASE_URL}/api/auth/login", json={"email": e, "password": "newpass99"}).status_code == 200
        # reuse fails
        r2 = requests.post(f"{BASE_URL}/api/auth/reset-password", json={"token": raw, "password": "another99"})
        assert r2.status_code == 400 and "invalid or has expired" in r2.json()["detail"]

    def test_reset_expired(self):
        e = em(); uid = seed_user(e)
        raw = seed_token(uid, e, expires_delta=timedelta(minutes=-5))
        r = requests.post(f"{BASE_URL}/api/auth/reset-password", json={"token": raw, "password": "newpass99"})
        assert r.status_code == 400 and "invalid or has expired" in r.json()["detail"]

    def test_reset_unknown_token(self):
        r = requests.post(f"{BASE_URL}/api/auth/reset-password", json={"token": "x" * 40, "password": "newpass99"})
        assert r.status_code == 400

    def test_reset_short_password(self):
        e = em(); uid = seed_user(e)
        raw = seed_token(uid, e)
        assert requests.post(f"{BASE_URL}/api/auth/reset-password", json={"token": raw, "password": "123"}).status_code == 422
        assert db.password_reset_tokens.find_one({"token_hash": hashlib.sha256(raw.encode()).hexdigest()})["used"] is False

    def test_reset_clears_lockout_and_sets_password_for_google_user(self):
        e = em(); uid = seed_user(e, password=None, google_id="g1")
        for _ in range(5):
            requests.post(f"{BASE_URL}/api/auth/login", json={"email": e, "password": "bad123"})
        raw = seed_token(uid, e)
        assert requests.post(f"{BASE_URL}/api/auth/reset-password", json={"token": raw, "password": "newpass99"}).status_code == 200
        assert requests.post(f"{BASE_URL}/api/auth/login", json={"email": e, "password": "newpass99"}).status_code == 200

    def test_reset_invalidates_other_tokens(self):
        e = em(); uid = seed_user(e)
        a, b = seed_token(uid, e), seed_token(uid, e)
        assert requests.post(f"{BASE_URL}/api/auth/reset-password", json={"token": a, "password": "newpass99"}).status_code == 200
        assert requests.post(f"{BASE_URL}/api/auth/reset-password", json={"token": b, "password": "newpass77"}).status_code == 400
