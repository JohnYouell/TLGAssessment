# Verse Choice Panel: public /api/verses, admin PUT /api/admin/verses, RBAC & validation
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
ADMIN = ("john.youell@newlifeokc.org", "AdminTest123")
MEMBER = ("test_member@example.com", "AdminTest123")


def login(creds):
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": creds[0], "password": creds[1]})
    if r.status_code != 200:
        pytest.skip(f"login failed {r.status_code} {r.text}")
    return s, r


@pytest.fixture(scope="module")
def admin():
    s, _ = login(ADMIN)
    original = s.get(f"{BASE_URL}/api/verses").json()["verses"]
    yield s
    s.put(f"{BASE_URL}/api/admin/verses", json={"verses": original})


@pytest.fixture(scope="module")
def member():
    return login(MEMBER)[0]


# Public verses
def test_public_verses_defaults():
    r = requests.get(f"{BASE_URL}/api/verses")
    assert r.status_code == 200
    v = r.json()["verses"]
    assert len(v) >= 1
    assert all({"text", "ref", "translation"} <= set(x) for x in v)


# Auth: cookies + is_admin
def test_login_cookies_httponly():
    _, r = login(ADMIN)
    sc = r.headers.get("set-cookie", "")
    assert "access_token" in sc and "httponly" in sc.lower()


def test_me_is_admin_true(admin):
    r = admin.get(f"{BASE_URL}/api/auth/me")
    assert r.status_code == 200 and r.json()["is_admin"] is True


def test_me_is_admin_false(member):
    r = member.get(f"{BASE_URL}/api/auth/me")
    assert r.status_code == 200 and r.json()["is_admin"] is False


# RBAC
def test_member_put_forbidden(member):
    r = member.put(f"{BASE_URL}/api/admin/verses", json={"verses": [{"text": "x", "ref": "y"}]})
    assert r.status_code == 403


def test_anon_put_unauthorized():
    r = requests.put(f"{BASE_URL}/api/admin/verses", json={"verses": [{"text": "x", "ref": "y"}]})
    assert r.status_code == 401


# Admin update + persistence
def test_admin_put_and_persist(admin):
    payload = {"verses": [{"text": "TEST_ verse one", "ref": "John 3:16", "translation": "NIV"},
                          {"text": "TEST_ verse two", "ref": "Psalm 23:1", "translation": "KJV"}]}
    r = admin.put(f"{BASE_URL}/api/admin/verses", json=payload)
    assert r.status_code == 200 and r.json()["verses"] == payload["verses"]
    g = requests.get(f"{BASE_URL}/api/verses").json()["verses"]
    assert g == payload["verses"]


# Validation
@pytest.mark.parametrize("body", [
    {"verses": []},
    {"verses": [{"text": "a" * 301, "ref": "x"}]},
    {"verses": [{"text": "", "ref": "x"}]},
    {"verses": [{"text": "x", "ref": ""}]},
    {"verses": [{"text": "x", "ref": "r" * 61}]},
    {"verses": [{"text": "x", "ref": "y"}] * 31},
])
def test_validation_422(admin, body):
    assert admin.put(f"{BASE_URL}/api/admin/verses", json=body).status_code == 422


def test_whitespace_only_text(admin):
    # Expected: rejected; documents current behaviour
    r = admin.put(f"{BASE_URL}/api/admin/verses", json={"verses": [{"text": "   ", "ref": "   "}]})
    assert r.status_code == 422, f"whitespace-only accepted: {r.status_code}"
