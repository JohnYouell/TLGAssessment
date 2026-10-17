# Account settings (profile, prefs, password), share tracking, referrals, admin invites, cron opt-out filters
import os
import uuid
import asyncio
from datetime import datetime, timezone, timedelta

import bcrypt
import pytest
import requests
from pymongo import MongoClient


def _env(path, key):
    for line in open(path):
        if line.startswith(key + "="):
            return line.split("=", 1)[1].strip().strip('"')


BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or _env("/app/frontend/.env", "REACT_APP_BACKEND_URL")).rstrip("/")
MONGO_URL = _env("/app/backend/.env", "MONGO_URL")
DB_NAME = _env("/app/backend/.env", "DB_NAME")
db = MongoClient(MONGO_URL)[DB_NAME]
PW = "test1234"
ADMIN_EMAIL = "test_inv_admin@example.com"  # must be in ADMIN_EMAILS for admin tests
CREATED = []


def now_iso(delta=timedelta(0)):
    return (datetime.now(timezone.utc) + delta).isoformat()


def seed_user(email=None, password=PW, **extra):
    email = email or f"test_inv_{uuid.uuid4().hex[:8]}@example.com"
    CREATED.append(email)
    doc = {"name": "TEST Inv", "email": email,
           "password_hash": bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode() if password else "",
           "marketing_opt_in": False, "created_at": now_iso(), "last_activity_at": now_iso(),
           "has_access": False, "final_video_watched": False, "token_version": 0, **extra}
    return email, str(db.users.insert_one(doc).inserted_id)


def login(email, password=PW):
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return s


def cookie_header(s):
    return "; ".join(f"{c.name}={c.value}" for c in s.cookies)


@pytest.fixture(scope="module", autouse=True)
def cleanup():
    yield
    ids = [str(u["_id"]) for u in db.users.find({"email": {"$in": CREATED}})]
    db.share_events.delete_many({"user_id": {"$in": ids}})
    db.progress.delete_many({"user_id": {"$in": ids}})
    db.login_attempts.delete_many({"identifier": {"$in": CREATED}})
    db.users.delete_many({"email": {"$in": CREATED}})


# ---- Profile / preferences ----
class TestAccount:
    def test_unauth_401(self):
        assert requests.put(f"{BASE_URL}/api/account", json={"name": "x", "marketing_opt_in": False, "reminders_opt_in": True}).status_code == 401
        assert requests.get(f"{BASE_URL}/api/account/invites").status_code == 401

    def test_me_has_new_fields(self):
        e, _ = seed_user()
        d = login(e).get(f"{BASE_URL}/api/auth/me").json()
        assert d["reminders_opt_in"] is True and d["has_password"] is True

    def test_update_persists(self):
        e, uid = seed_user()
        s = login(e)
        r = s.put(f"{BASE_URL}/api/account", json={"name": "  TEST Renamed ", "marketing_opt_in": True, "reminders_opt_in": False})
        assert r.status_code == 200
        assert r.json()["name"] == "TEST Renamed" and r.json()["reminders_opt_in"] is False
        me = s.get(f"{BASE_URL}/api/auth/me").json()
        assert me["name"] == "TEST Renamed" and me["marketing_opt_in"] is True and me["reminders_opt_in"] is False and me["email"] == e
        # toggle marketing back off (remove_from_list)
        r = s.put(f"{BASE_URL}/api/account", json={"name": "TEST Renamed", "marketing_opt_in": False, "reminders_opt_in": True})
        assert r.status_code == 200 and r.json()["marketing_opt_in"] is False

    def test_email_not_changeable(self):
        e, uid = seed_user()
        s = login(e)
        s.put(f"{BASE_URL}/api/account", json={"name": "N", "email": "hacker@example.com", "marketing_opt_in": False, "reminders_opt_in": True})
        assert s.get(f"{BASE_URL}/api/auth/me").json()["email"] == e

    @pytest.mark.parametrize("name", ["", "   "])
    def test_empty_name_rejected(self, name):
        e, _ = seed_user()
        s = login(e)
        r = s.put(f"{BASE_URL}/api/account", json={"name": name, "marketing_opt_in": False, "reminders_opt_in": True})
        assert r.status_code == 422
        assert s.get(f"{BASE_URL}/api/auth/me").json()["name"] == "TEST Inv"


# ---- Password change ----
class TestPassword:
    def test_wrong_current(self):
        e, _ = seed_user()
        r = login(e).post(f"{BASE_URL}/api/account/password", json={"current_password": "wrong", "new_password": "newpass1"})
        assert r.status_code == 400 and "incorrect" in r.json()["detail"]

    def test_empty_current_with_password_account(self):
        e, _ = seed_user()
        r = login(e).post(f"{BASE_URL}/api/account/password", json={"current_password": "", "new_password": "newpass1"})
        assert r.status_code == 400

    def test_short_new(self):
        e, _ = seed_user()
        r = login(e).post(f"{BASE_URL}/api/account/password", json={"current_password": PW, "new_password": "123"})
        assert r.status_code == 422

    def test_change_success_and_token_version(self):
        e, _ = seed_user()
        s = login(e)
        old_cookies = cookie_header(s)
        r = s.post(f"{BASE_URL}/api/account/password", json={"current_password": PW, "new_password": "newpass1"})
        assert r.status_code == 200
        assert s.get(f"{BASE_URL}/api/auth/me").status_code == 200  # current session survives
        assert requests.get(f"{BASE_URL}/api/auth/me", headers={"Cookie": old_cookies}).status_code == 401
        assert requests.post(f"{BASE_URL}/api/auth/refresh", headers={"Cookie": old_cookies}).status_code == 401
        assert requests.post(f"{BASE_URL}/api/auth/login", json={"email": e, "password": PW}).status_code == 401
        assert requests.post(f"{BASE_URL}/api/auth/login", json={"email": e, "password": "newpass1"}).status_code == 200

    def test_google_only_set_password(self):
        e, uid = seed_user(password="", google_id="g123")
        s = requests.Session()
        # mint token via bumping: login impossible, so craft JWT directly
        import jwt
        tok = jwt.encode({"sub": uid, "type": "access", "v": 0, "exp": datetime.now(timezone.utc) + timedelta(minutes=10)},
                         _env("/app/backend/.env", "JWT_SECRET"), algorithm="HS256")
        h = {"Authorization": f"Bearer {tok}"}
        me = s.get(f"{BASE_URL}/api/auth/me", headers=h).json()
        assert me["has_password"] is False
        r = s.post(f"{BASE_URL}/api/account/password", json={"new_password": "setpass1"}, headers=h)
        assert r.status_code == 200 and r.json()["has_password"] is True
        assert requests.post(f"{BASE_URL}/api/auth/login", json={"email": e, "password": "setpass1"}).status_code == 200


# ---- Share events / invites ----
class TestShares:
    def test_unauth_401(self):
        assert requests.post(f"{BASE_URL}/api/share-events", json={"source": "spread", "channel": "email"}).status_code == 401

    @pytest.mark.parametrize("body", [{"source": "bad", "channel": "email"}, {"source": "spread", "channel": "fax"}, {"source": "spread"}, {}])
    def test_invalid_422(self, body):
        e, _ = seed_user()
        assert login(e).post(f"{BASE_URL}/api/share-events", json=body).status_code == 422

    def test_counts_and_referral(self):
        e, uid = seed_user()
        s = login(e)
        assert s.get(f"{BASE_URL}/api/account/invites").json() == {"shares": 0, "joined": 0}
        for src, ch in [("spread", "email"), ("spread", "sms"), ("train", "copy")]:
            assert s.post(f"{BASE_URL}/api/share-events", json={"source": src, "channel": ch}).json() == {"ok": True}
        assert db.share_events.count_documents({"user_id": uid}) == 3
        seed_user(referred_by=uid)
        assert s.get(f"{BASE_URL}/api/account/invites").json() == {"shares": 3, "joined": 1}


# ---- Admin invites ----
class TestAdminInvites:
    def test_non_admin_403(self):
        e, _ = seed_user()
        assert login(e).get(f"{BASE_URL}/api/admin/invites").status_code == 403

    def test_unauth_401(self):
        assert requests.get(f"{BASE_URL}/api/admin/invites").status_code == 401

    def test_rows_sorted(self):
        if db.users.find_one({"email": ADMIN_EMAIL}) is None:
            seed_user(ADMIN_EMAIL)
        a = login(ADMIN_EMAIL)
        e1, u1 = seed_user(name="TEST A")
        e2, u2 = seed_user(name="TEST B")
        s1 = login(e1)
        for _ in range(3):
            s1.post(f"{BASE_URL}/api/share-events", json={"source": "spread", "channel": "copy"})
        s2 = login(e2)
        s2.post(f"{BASE_URL}/api/share-events", json={"source": "train", "channel": "sms"})
        seed_user(referred_by=u2)
        seed_user(referred_by="not-an-objectid")  # must not crash
        r = a.get(f"{BASE_URL}/api/admin/invites")
        assert r.status_code == 200
        rows = {x["email"]: x for x in r.json()["rows"]}
        assert rows[e1]["spread"] == 3 and rows[e1]["train"] == 0 and rows[e1]["shares"] == 3 and rows[e1]["joined"] == 0
        assert rows[e2]["train"] == 1 and rows[e2]["shares"] == 1 and rows[e2]["joined"] == 1
        order = [x["email"] for x in r.json()["rows"]]
        assert order.index(e2) < order.index(e1)  # joined first
        assert "_id" not in r.json()["rows"][0]


# ---- Cron opt-out filters (run against isolated temp DB with email senders stubbed) ----
def test_cron_filters_skip_opted_out():
    import subprocess, sys
    code = r'''
import os, sys, asyncio
os.environ["DB_NAME"] = "tmp_cron_test_db"
sys.path.insert(0, "/app/backend")
import server
sent = []
async def fake(email, name): sent.append(email)
server.send_reminder_email = fake
server.send_nudge_email = fake
from datetime import datetime, timezone, timedelta
old = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
async def main():
    d = server.db
    await d.users.delete_many({}); await d.progress.delete_many({})
    base = {"name":"T","password_hash":"","created_at":old,"last_activity_at":old}
    ids = {}
    for e, opt in [("in@example.com", True), ("out@example.com", False), ("legacy@example.com", None)]:
        doc = {**base, "email": e}
        if opt is not None: doc["reminders_opt_in"] = opt
        ids[e] = str((await d.users.insert_one(doc)).inserted_id)
    await server.run_day2_reminders()
    day2 = sorted(sent); sent.clear()
    for uid in ids.values():
        await d.progress.insert_one({"user_id": uid, "assessment_id": 1, "status": "completed"})
    await d.users.update_many({}, {"$set": {"last_activity_at": old}})
    await server.run_journey_nudges()
    print("DAY2", day2); print("NUDGE", sorted(sent))
    await server.client.drop_database("tmp_cron_test_db")
asyncio.run(main())
'''
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd="/app/backend", timeout=60)
    assert out.returncode == 0, out.stderr
    assert "DAY2 ['in@example.com', 'legacy@example.com']" in out.stdout
    assert "NUDGE ['in@example.com', 'legacy@example.com']" in out.stdout
