# Paywall tests: tier/lock states, discount codes, Stripe checkout, admin codes/videos, final gate, master results
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api"
FREE = ("test_free@example.com", "Test1234!")
PAID = ("test_paid@example.com", "Test1234!")
ADMIN = ("john.youell@newlifeokc.org", "AdminTest123")


def login(creds):
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": creds[0], "password": creds[1]})
    if r.status_code != 200:
        pytest.skip(f"login failed {creds[0]}: {r.status_code} {r.text}")
    return s


def answers_for(s, aid):
    r = s.get(f"{API}/assessments/{aid}")
    assert r.status_code == 200, r.text
    return {q["id"]: 3 for q in r.json()["questions"]}


def submit(s, aid):
    r = s.post(f"{API}/assessments/{aid}/submit", json={"answers": answers_for(s, aid)})
    assert r.status_code in (200, 400), r.text
    return r


@pytest.fixture(scope="module")
def free():
    return login(FREE)


@pytest.fixture(scope="module")
def paid():
    return login(PAID)


@pytest.fixture(scope="module")
def admin():
    return login(ADMIN)


# --- Free tier lock states
class TestFreeTier:
    def test_list_24_items(self, free):
        d = free.get(f"{API}/assessments").json()
        items = d["assessments"]
        assert len(items) == 24
        assert d["has_access"] is False
        by = {a["id"]: a for a in items}
        assert by[1]["tier"] == "free" and by[1]["unlocked"]
        for i in range(2, 8):
            assert by[i]["tier"] == "paid" and by[i]["lock"] == "paywall"
        for i in range(101, 118):
            assert by[i]["tier"] == "free"

    def test_paid_402(self, free):
        assert free.get(f"{API}/assessments/2").status_code == 402
        assert free.get(f"{API}/assessments/7").status_code == 402
        assert free.get(f"{API}/master-results").status_code == 402

    def test_chapter_sequence(self, free):
        assert free.get(f"{API}/assessments/101").status_code == 403
        submit(free, 1)
        assert free.get(f"{API}/assessments/101").status_code == 200
        assert free.get(f"{API}/assessments/102").status_code == 403
        r = submit(free, 101)
        assert r.status_code == 200 and r.json()["kind"] == "chapter"
        assert len(r.json().get("sections", [])) == 0
        assert free.get(f"{API}/assessments/102").status_code == 200
        assert free.get(f"{API}/assessments/103").status_code == 403

    def test_chapter_3_questions(self, free):
        q = free.get(f"{API}/assessments/102").json()["questions"]
        assert [x["id"] for x in q] == ["c2q1", "c2q2", "c2q3"]


# --- Quotes and checkout
class TestPayments:
    def test_quotes(self, free):
        r = free.post(f"{API}/payments/quote", json={"code": "earlyadopters"})
        assert r.status_code == 200 and r.json()["total"] == 20.0
        r = free.post(f"{API}/payments/quote", json={"code": "Senior Leader"})
        assert r.status_code == 200 and r.json()["total"] == 10.0
        r = free.post(f"{API}/payments/quote", json={"code": " tlg staff "})
        assert r.json()["total"] == 0.0
        r = free.post(f"{API}/payments/quote", json={})
        assert r.json()["total"] == 40.0
        assert free.post(f"{API}/payments/quote", json={"code": "BOGUS"}).status_code == 400

    def test_quote_unauth(self):
        assert requests.post(f"{API}/payments/quote", json={}).status_code == 401

    def test_checkout_stripe(self, free):
        r = free.post(f"{API}/payments/checkout", json={"code": "EarlyAdopters", "origin_url": BASE_URL})
        assert r.status_code == 200, r.text
        d = r.json()
        assert "checkout.stripe.com" in d["checkout_url"]
        st = free.get(f"{API}/payments/status/{d['session_id']}")
        assert st.status_code == 200 and st.json()["payment_status"] == "pending"

    def test_checkout_full_price(self, free):
        r = free.post(f"{API}/payments/checkout", json={"origin_url": BASE_URL})
        assert r.status_code == 200, r.text
        assert "checkout.stripe.com" in r.json()["checkout_url"]

    def test_status_404(self, free):
        assert free.get(f"{API}/payments/status/cs_test_nope").status_code == 404


# --- Admin discount codes
class TestAdminCodes:
    def test_list(self, admin):
        codes = admin.get(f"{API}/admin/codes").json()["codes"]
        names = {c["code"] for c in codes}
        assert {"BeataTeam", "EarlyAdopters", "SeniorLeader", "TLG Staff"} <= names

    def test_crud(self, admin, free):
        r = admin.post(f"{API}/admin/codes", json={"code": "TEST Code1", "percent_off": 20})
        assert r.status_code == 200, r.text
        cid = r.json()["id"]
        assert cid == "testcode1"
        assert admin.post(f"{API}/admin/codes", json={"code": "testcode1", "percent_off": 20}).status_code == 400
        assert free.post(f"{API}/payments/quote", json={"code": "test code1"}).json()["total"] == 32.0
        r = admin.put(f"{API}/admin/codes/{cid}", json={"code": "TEST Code1", "percent_off": 30, "active": True})
        assert r.json()["percent_off"] == 30
        assert free.post(f"{API}/payments/quote", json={"code": "TESTCODE1"}).json()["total"] == 28.0
        admin.put(f"{API}/admin/codes/{cid}", json={"code": "TEST Code1", "percent_off": 30, "active": False})
        assert free.post(f"{API}/payments/quote", json={"code": "TESTCODE1"}).status_code == 400
        assert admin.delete(f"{API}/admin/codes/{cid}").status_code == 200
        assert cid not in {c["id"] for c in admin.get(f"{API}/admin/codes").json()["codes"]}
        assert admin.put(f"{API}/admin/codes/{cid}", json={"code": "x1", "percent_off": 30}).status_code == 404

    def test_validation(self, admin):
        assert admin.post(f"{API}/admin/codes", json={"code": "TESTbad", "percent_off": 0}).status_code == 422
        assert admin.post(f"{API}/admin/codes", json={"code": "TESTbad", "percent_off": 101}).status_code == 422

    def test_non_admin_403(self, free):
        assert free.get(f"{API}/admin/codes").status_code == 403
        assert free.post(f"{API}/admin/codes", json={"code": "TESTx", "percent_off": 10}).status_code == 403
        assert free.put(f"{API}/admin/codes/beatateam", json={"code": "x1", "percent_off": 10}).status_code == 403
        assert free.delete(f"{API}/admin/codes/beatateam").status_code == 403


# --- Admin videos
class TestVideos:
    def test_save_and_visibility(self, admin, free):
        cur = admin.get(f"{API}/videos").json()["videos"]
        cur["chapter_1"] = {"title": "TEST Chapter 1 headline", "url": "https://vimeo.com/76979871"}
        cur["registration_thanks"] = {"title": "Welcome", "url": "https://vimeo.com/76979871"}
        r = admin.put(f"{API}/admin/videos", json={"videos": cur})
        assert r.status_code == 200 and r.json()["videos"]["chapter_1"]["url"] == "https://vimeo.com/76979871"
        fv = free.get(f"{API}/videos").json()["videos"]
        assert fv["chapter_1"]["url"] == "" and fv["chapter_1"]["title"] == "TEST Chapter 1 headline"
        assert fv["registration_thanks"]["url"] == "https://vimeo.com/76979871"

    def test_bad_url(self, admin):
        r = admin.put(f"{API}/admin/videos", json={"videos": {"chapter_2": {"title": "", "url": "https://youtube.com/watch?v=1"}}})
        assert r.status_code == 422

    def test_non_admin(self, free):
        assert free.put(f"{API}/admin/videos", json={"videos": {}}).status_code == 403


# --- Paid user: grant via 100% code and full journey
class TestPaidJourney:
    def test_grant(self, paid):
        assert paid.get(f"{API}/auth/me").json()["has_access"] is False
        r = paid.post(f"{API}/payments/checkout", json={"code": "TLG Staff", "origin_url": BASE_URL})
        assert r.status_code == 200 and r.json() == {"granted": True}
        assert paid.get(f"{API}/auth/me").json()["has_access"] is True
        assert paid.get(f"{API}/videos").json()["videos"]["chapter_1"]["url"] == "https://vimeo.com/76979871"
        assert paid.post(f"{API}/payments/checkout", json={"code": "TLG Staff"}).status_code == 400

    def test_section_locks(self, paid):
        submit(paid, 1)
        for n in range(1, 4):
            assert paid.get(f"{API}/assessments/2").status_code == 403
            submit(paid, 100 + n)
        assert paid.get(f"{API}/assessments/2").status_code == 200
        for n in range(4, 18):
            submit(paid, 100 + n)
        assert paid.get(f"{API}/assessments/7").status_code == 403
        for s in range(2, 7):
            submit(paid, s)

    def test_final_gate(self, paid):
        d = paid.get(f"{API}/assessments/7").json()
        assert d["video_required"] is True and d["questions"] == []
        assert paid.post(f"{API}/assessments/7/submit", json={"answers": {}}).status_code == 403
        assert paid.post(f"{API}/assessments/7/video-watched").status_code == 200
        d = paid.get(f"{API}/assessments/7").json()
        assert len(d["questions"]) == 25

    def test_master(self, paid):
        assert paid.get(f"{API}/master-results").status_code == 403
        r = submit(paid, 7)
        assert r.status_code == 200
        m = paid.get(f"{API}/master-results").json()
        assert len(m["rows"]) == 5 and len(m["reviews"]) == 5 and len(m["chapters"]) == 17
        assert all(c["score"] == 9 for c in m["chapters"])
