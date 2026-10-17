# Book & Sharing settings: GET /api/sharing (public) and PUT /api/admin/sharing (admin only)
# Requires: python tests/seed_rep7_users.py seed (TEST_free7 + admin john.youell)
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
PW = "Test1234!"
DEFAULT_SUBJECT = "Join me at The Lord's Gym"
DEFAULT_MESSAGE = ("I've been working through The Lord's Gym: Discipleship Training, One Rep at a Time, and it's been helping me grow "
                   "in my walk with Christ, one rep at a time. I'd love for you to grab a copy of the book and join the conversation with me.")


def login(email):
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": PW})
    if r.status_code != 200:
        pytest.skip(f"login failed for {email}: {r.status_code}")
    return s


@pytest.fixture(scope="module")
def admin():
    s = login("john.youell@newlifeokc.org")
    yield s
    s.put(f"{BASE_URL}/api/admin/sharing", json={"book_url": "", "share_subject": DEFAULT_SUBJECT, "share_message": DEFAULT_MESSAGE})


@pytest.fixture(scope="module")
def user():
    return login("TEST_free7@example.com")


# Public GET
def test_get_sharing_defaults():
    r = requests.get(f"{BASE_URL}/api/sharing")
    assert r.status_code == 200
    d = r.json()
    assert d == {"book_url": "", "share_subject": DEFAULT_SUBJECT, "share_message": DEFAULT_MESSAGE}


# Authorization
def test_put_unauthenticated():
    r = requests.put(f"{BASE_URL}/api/admin/sharing", json={"book_url": "", "share_subject": "x", "share_message": "y"})
    assert r.status_code == 401


def test_put_non_admin(user):
    r = user.put(f"{BASE_URL}/api/admin/sharing", json={"book_url": "", "share_subject": "x", "share_message": "y"})
    assert r.status_code == 403


# Validation
@pytest.mark.parametrize("payload", [
    {"book_url": "ftp://x.com", "share_subject": "s", "share_message": "m"},
    {"book_url": "javascript:alert(1)", "share_subject": "s", "share_message": "m"},
    {"book_url": "www.amazon.com", "share_subject": "s", "share_message": "m"},
    {"book_url": "https://a.com/b c", "share_subject": "s", "share_message": "m"},
    {"book_url": "", "share_subject": "", "share_message": "m"},
    {"book_url": "", "share_subject": "   ", "share_message": "m"},
    {"book_url": "", "share_subject": "s", "share_message": ""},
    {"book_url": "", "share_subject": "s"},
])
def test_put_validation(admin, payload):
    r = admin.put(f"{BASE_URL}/api/admin/sharing", json=payload)
    assert r.status_code == 422


# Save + persist + restore
def test_put_saves_and_persists(admin):
    payload = {"book_url": "  https://example.com/TEST_book  ", "share_subject": "TEST subject", "share_message": "TEST message line"}
    r = admin.put(f"{BASE_URL}/api/admin/sharing", json=payload)
    assert r.status_code == 200
    assert r.json()["book_url"] == "https://example.com/TEST_book"
    g = requests.get(f"{BASE_URL}/api/sharing").json()
    assert g == {"book_url": "https://example.com/TEST_book", "share_subject": "TEST subject", "share_message": "TEST message line"}
    assert "updated_by" not in g
    r = admin.put(f"{BASE_URL}/api/admin/sharing", json={"book_url": "", "share_subject": DEFAULT_SUBJECT, "share_message": DEFAULT_MESSAGE})
    assert r.status_code == 200
    assert requests.get(f"{BASE_URL}/api/sharing").json()["book_url"] == ""
