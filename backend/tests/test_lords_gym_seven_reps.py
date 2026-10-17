# 7 Reps tests (chapter reviews removed): assessment list, lock states, videos keys, master results
# Requires seed: python /app/backend/tests/seed_rep7_users.py seed ; run with -n0
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api"
PW = "Test1234!"
FREE, PAID, ADMIN = "TEST_free7@example.com", "TEST_paid7@example.com", "john.youell@newlifeokc.org"


def login(email):
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": email, "password": PW})
    if r.status_code != 200:
        pytest.skip(f"login failed {email}: {r.status_code}")
    return s


def submit(s, aid):
    q = s.get(f"{API}/assessments/{aid}")
    assert q.status_code == 200, q.text
    ans = {x["id"]: 3 for x in q.json()["questions"]}
    r = s.post(f"{API}/assessments/{aid}/submit", json={"answers": ans})
    assert r.status_code == 200, r.text
    return r.json()


@pytest.fixture(scope="module")
def free():
    return login(FREE)


@pytest.fixture(scope="module")
def paid():
    return login(PAID)


@pytest.fixture(scope="module")
def admin():
    return login(ADMIN)


def items(s):
    d = s.get(f"{API}/assessments").json()
    return d, {a["id"]: a for a in d["assessments"]}


class TestSevenReps:
    def test_exactly_7_no_chapters(self, free):
        d, by = items(free)
        assert sorted(by) == list(range(1, 8))
        assert all(a["kind"] != "chapter" for a in d["assessments"])
        assert {by[1]["kind"], by[7]["kind"]} == {"initial", "final"}
        assert all(by[i]["kind"] == "section" for i in range(2, 7))

    def test_chapter_ids_404(self, free):
        for aid in (101, 117):
            assert free.get(f"{API}/assessments/{aid}").status_code == 404

    def test_free_locks(self, free):
        d, by = items(free)
        assert d["has_access"] is False
        assert by[1]["tier"] == "free" and by[1]["unlocked"] is True
        for i in range(2, 8):
            assert by[i]["tier"] == "paid" and by[i]["lock"] == "paywall"
        assert free.get(f"{API}/assessments/2").status_code == 402

    def test_paid_sections_all_unlocked(self, paid):
        d, by = items(paid)
        assert d["has_access"] is True
        for i in range(1, 7):
            assert by[i]["unlocked"] is True and by[i]["lock"] is None, i
        assert by[7]["lock"] == "sequence"
        assert paid.get(f"{API}/assessments/7").status_code == 403

    def test_admin_sections_unlocked(self, admin):
        _, by = items(admin)
        for i in range(2, 7):
            assert by[i]["unlocked"] is True
        assert by[7]["lock"] == "sequence"

    def test_video_keys(self, admin, free):
        v = admin.get(f"{API}/videos").json()["videos"]
        assert set(v) == {"registration_thanks", "initial_congrats", "pastor_final"} | {f"section_{i}" for i in range(2, 7)}
        fv = free.get(f"{API}/videos").json()
        assert fv["has_access"] is False and all(fv["videos"][f"section_{i}"]["url"] == "" for i in range(2, 7))

    def test_admin_videos_save_ignores_chapter(self, admin):
        r = admin.put(f"{API}/admin/videos", json={"videos": {"section_2": {"title": "TEST_S2", "url": ""}, "chapter_1": {"title": "x", "url": ""}}})
        assert r.status_code == 200
        v = admin.get(f"{API}/videos").json()["videos"]
        assert v["section_2"]["title"] == "TEST_S2" and "chapter_1" not in v
        admin.put(f"{API}/admin/videos", json={"videos": {"section_2": {"title": "", "url": ""}}})

    def test_non_admin_cannot_save_videos(self, paid):
        assert paid.put(f"{API}/admin/videos", json={"videos": {}}).status_code == 403


class TestPaidJourney:
    def test_out_of_order_section_submit(self, paid):
        r = submit(paid, 4)
        assert r["kind"] == "section" and r["max_score"] == 75

    def test_complete_all_and_final(self, paid):
        submit(paid, 1)
        for i in (2, 3, 5, 6):
            submit(paid, i)
        _, by = items(paid)
        assert by[7]["unlocked"] is True
        assert paid.post(f"{API}/assessments/7/video-watched").status_code == 200
        r = submit(paid, 7)
        assert r["kind"] == "final"

    def test_master_results(self, paid):
        r = paid.get(f"{API}/master-results")
        assert r.status_code == 200
        d = r.json()
        assert "chapters" not in d
        assert set(d) == {"rows", "total", "reviews"}
        assert len(d["reviews"]) == 5 and len(d["rows"]) == 5

    def test_scorecard_pdf(self, paid):
        r = paid.get(f"{API}/master-results/scorecard")
        assert r.status_code == 200 and r.content[:4] == b"%PDF"
