# Editable About/Contact pages: public GET, admin PUT, validation, RBAC
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
ADMIN = ("john.youell@newlifeokc.org", "AdminTest123")
MEMBER = ("test_member@example.com", "AdminTest123")
VALID = {"eyebrow": "TEST_Eyebrow", "title": "TEST_Title", "body": "Para one\n\nPara two", "photo_url": ""}


def login(creds):
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": creds[0], "password": creds[1]})
    if r.status_code != 200:
        pytest.skip(f"login failed {r.status_code} {r.text}")
    return s


@pytest.fixture(scope="module")
def admin():
    return login(ADMIN)


@pytest.fixture(scope="module")
def member():
    return login(MEMBER)


# Public GET
@pytest.mark.parametrize("slug", ["about", "contact"])
def test_public_get_shape(slug):
    r = requests.get(f"{BASE_URL}/api/pages/{slug}")
    assert r.status_code == 200
    d = r.json()
    assert set(d.keys()) == {"eyebrow", "title", "body", "photo_url"}
    assert d["title"] and d["body"]


def test_unknown_slug_404():
    assert requests.get(f"{BASE_URL}/api/pages/xyz").status_code == 404


def test_admin_put_unknown_slug_404(admin):
    assert admin.put(f"{BASE_URL}/api/admin/pages/xyz", json=VALID).status_code == 404


# Admin PUT persistence
@pytest.mark.parametrize("slug", ["about", "contact"])
def test_admin_put_persists(admin, slug):
    payload = {**VALID, "title": f"TEST_{slug}", "photo_url": "https://i.ibb.co/DftrRsNf/TLG-logo-WHT.png"}
    r = admin.put(f"{BASE_URL}/api/admin/pages/{slug}", json=payload)
    assert r.status_code == 200, r.text
    assert r.json()["title"] == f"TEST_{slug}"
    g = requests.get(f"{BASE_URL}/api/pages/{slug}").json()
    assert g == payload


def test_whitespace_stripped(admin):
    r = admin.put(f"{BASE_URL}/api/admin/pages/about", json={**VALID, "title": "  TEST_trim  "})
    assert r.status_code == 200
    assert requests.get(f"{BASE_URL}/api/pages/about").json()["title"] == "TEST_trim"


# Validation
@pytest.mark.parametrize("bad", [
    {"title": ""}, {"body": ""}, {"title": "   "}, {"photo_url": "http://x"},
    {"photo_url": "javascript:alert(1)"}, {"photo_url": "https://a b"}, {"title": "x" * 81}, {"eyebrow": "x" * 41},
])
def test_validation_422(admin, bad):
    r = admin.put(f"{BASE_URL}/api/admin/pages/about", json={**VALID, **bad})
    assert r.status_code == 422, r.text


# RBAC
def test_member_forbidden(member):
    assert member.put(f"{BASE_URL}/api/admin/pages/about", json=VALID).status_code == 403


def test_anonymous_unauthorized():
    assert requests.put(f"{BASE_URL}/api/admin/pages/about", json=VALID).status_code == 401


def test_member_is_not_admin(member):
    assert member.get(f"{BASE_URL}/api/auth/me").json().get("is_admin") is False
