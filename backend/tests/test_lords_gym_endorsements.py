# Endorsements: public GET, admin PUT (RBAC, validation, book trimming, persistence)
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
ADMIN = ("test_admin@example.com", "test1234")
MEMBER = ("test_endo_member@example.com", "test1234")
URL = f"{BASE_URL}/api/admin/endorsements"
ITEM = {"text": "TEST_ great book", "name": "TEST_Name", "position": "Pastor", "books": ["Book A"]}


def login(creds):
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": creds[0], "password": creds[1]})
    if r.status_code != 200:
        pytest.skip(f"login failed {r.status_code} {r.text}")
    return s


@pytest.fixture(scope="module")
def admin():
    s = login(ADMIN)
    yield s
    s.put(URL, json={"layout": "cards", "items": []})


@pytest.fixture(scope="module")
def member():
    return login(MEMBER)


def test_public_get_default():
    r = requests.get(f"{BASE_URL}/api/endorsements")
    assert r.status_code == 200
    d = r.json()
    assert d["layout"] in ("cards", "spotlight", "list")
    assert isinstance(d["items"], list)


def test_unauth_401():
    assert requests.put(URL, json={"layout": "cards", "items": []}).status_code == 401


def test_member_403(member):
    assert member.put(URL, json={"layout": "cards", "items": []}).status_code == 403


@pytest.mark.parametrize("payload", [
    {"layout": "grid", "items": []},
    {"layout": "cards", "items": [{**ITEM, "text": ""}]},
    {"layout": "cards", "items": [{**ITEM, "name": ""}]},
    {"layout": "cards", "items": [{**ITEM, "name": "   "}]},
    {"layout": "cards", "items": [{**ITEM, "text": "  \n "}]},
])
def test_validation_422(admin, payload):
    assert admin.put(URL, json=payload).status_code == 422


def test_put_trims_books_and_persists(admin):
    items = [
        {"text": "  TEST_ one ", "name": " TEST_A ", "position": "Pastor, X", "books": ["  Book 1 ", "", "   ", "Book 2"]},
        {"text": "TEST_ two", "name": "TEST_B", "position": "", "books": []},
    ]
    r = admin.put(URL, json={"layout": "spotlight", "items": items})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["layout"] == "spotlight"
    assert d["items"][0]["books"] == ["Book 1", "Book 2"]
    assert d["items"][0]["name"] == "TEST_A"
    assert d["items"][0]["text"] == "TEST_ one"
    g = requests.get(f"{BASE_URL}/api/endorsements").json()
    assert g["layout"] == "spotlight"
    assert [i["name"] for i in g["items"]] == ["TEST_A", "TEST_B"]
    assert g["items"][0]["books"] == ["Book 1", "Book 2"]
    assert "_id" not in g and "updated_by" not in g


def test_cleanup_to_default(admin):
    r = admin.put(URL, json={"layout": "cards", "items": []})
    assert r.status_code == 200
    g = requests.get(f"{BASE_URL}/api/endorsements").json()
    assert g == {"layout": "cards", "items": []}
