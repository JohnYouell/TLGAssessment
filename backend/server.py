from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Annotated, Dict, Optional

import bcrypt
import jwt
from bson import ObjectId
from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends, BackgroundTasks
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, BeforeValidator, ConfigDict, EmailStr, Field
from starlette.middleware.cors import CORSMiddleware

from assessments_config import (
    ASSESSMENTS, SECTIONS, SCALE_MAX, BASELINE_ASSESSMENT_ID, FINAL_ASSESSMENT_ID, TOTAL_125_TIERS,
    SECTION_REVIEW_IDS,
)
import stripe
from scorecard import build_scorecard_pdf
from brevo import create_contact, send_scorecard_email, send_welcome_email, send_reminder_email, send_nudge_email, send_completion_email
import hmac

client = AsyncIOMotorClient(os.environ["MONGO_URL"])
db = client[os.environ["DB_NAME"]]

app = FastAPI()
api = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

JWT_ALGORITHM = "HS256"
ASSESS_BY_ID = {a["id"]: a for a in ASSESSMENTS}

# ---------- Models ----------
PyObjectId = Annotated[str, BeforeValidator(lambda v: str(v) if isinstance(v, ObjectId) else v)]


class BaseDocument(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: Optional[PyObjectId] = Field(default=None, alias="_id")

    @classmethod
    def from_mongo(cls, doc):
        return cls.model_validate(doc) if doc else None

    def to_mongo(self):
        data = self.model_dump(by_alias=True, exclude={"id"})
        if self.id:
            data["_id"] = ObjectId(self.id)
        return data


class User(BaseDocument):
    name: str
    email: str
    password_hash: str = ""
    marketing_opt_in: bool = False
    created_at: str = ""
    last_activity_at: str = ""
    referred_by: Optional[str] = None
    has_access: bool = False
    final_video_watched: bool = False

    def public(self):
        return {"id": self.id, "name": self.name, "email": self.email,
                "marketing_opt_in": self.marketing_opt_in, "is_admin": is_admin(self),
                "has_access": self.has_access or is_admin(self)}


class Progress(BaseDocument):
    user_id: str
    assessment_id: int
    answers: Dict[str, int] = {}
    status: str = "in_progress"
    score: Optional[int] = None
    max_score: Optional[int] = None
    designation: Optional[str] = None
    meaning: Optional[str] = None
    section_scores: Dict[str, int] = {}
    completed_at: Optional[str] = None
    updated_at: str = ""


class RegisterIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    marketing_opt_in: bool = False
    referred_by: Optional[str] = Field(default=None, max_length=64)


class VerseIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    text: str = Field(min_length=1, max_length=300)
    ref: str = Field(min_length=1, max_length=60)
    translation: str = Field(default="", max_length=20)


class VersesIn(BaseModel):
    verses: list[VerseIn] = Field(min_length=1, max_length=30)


DEFAULT_VERSES = [
    {"text": t, "ref": r, "translation": "NIV"} for t, r in [
        ("Rather, train yourself to be godly.", "1 Timothy 4:7"),
        ("Run in such a way as to get the prize.", "1 Corinthians 9:24"),
        ("Let us run with perseverance the race marked out for us.", "Hebrews 12:1"),
        ("I press on toward the goal to win the prize for which God has called me heavenward in Christ Jesus.", "Philippians 3:14"),
        ("Those who hope in the Lord will renew their strength.", "Isaiah 40:31"),
        ("Let us not become weary in doing good, for at the proper time we will reap a harvest if we do not give up.", "Galatians 6:9"),
        ("I have fought the good fight, I have finished the race, I have kept the faith.", "2 Timothy 4:7"),
    ]
]


PAGE_SLUGS = ("about", "contact")
DEFAULT_PAGES = {
    "about": {
        "eyebrow": "About",
        "title": "The Lord's Gym",
        "body": "The Lord's Gym: Discipleship Training, One Rep at a Time treats spiritual growth like training: steady, daily work that builds strength over time. This site is the companion assessment series for the book.\n\nThe series has 7 assessments. You start with the Initial Spiritual Assessment as your Day 1 baseline. Then you work through five section reviews that follow the book's chapters, and you finish with the Spiritual Progress Assessment. Your Master Results compare Day 1 to Today across all five sections, so you can see how far you've come.\n\n[Placeholder: author bio, ministry background and where to buy the book]",
    },
    "contact": {
        "eyebrow": "Contact",
        "title": "Get in Touch",
        "body": "Questions about the assessments, your account or the book? Send us an email and we'll get back to you.\n\n[Placeholder: mailing address, phone number and office hours]",
    },
}


class PageIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    eyebrow: str = Field(default="", max_length=40)
    title: str = Field(min_length=1, max_length=80)
    body: str = Field(min_length=1, max_length=8000)
    photo_url: str = Field(default="", max_length=500, pattern=r"^(https://\S+)?$")


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class AnswersIn(BaseModel):
    answers: Dict[str, int]


# ---------- Auth helpers ----------
def now_iso():
    return datetime.now(timezone.utc).isoformat()


def hash_password(p):
    return bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()


def verify_password(p, h):
    return bcrypt.checkpw(p.encode(), h.encode())


def make_token(user_id, ttype, delta):
    payload = {"sub": user_id, "type": ttype, "exp": datetime.now(timezone.utc) + delta}
    return jwt.encode(payload, os.environ["JWT_SECRET"], algorithm=JWT_ALGORITHM)


def set_auth_cookies(response: Response, user_id: str):
    opts = dict(httponly=True, secure=True, samesite="none", path="/")
    response.set_cookie("access_token", make_token(user_id, "access", timedelta(minutes=15)), max_age=900, **opts)
    response.set_cookie("refresh_token", make_token(user_id, "refresh", timedelta(days=7)), max_age=604800, **opts)


def decode(token, ttype):
    try:
        payload = jwt.decode(token, os.environ["JWT_SECRET"], algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")
    if payload.get("type") != ttype:
        raise HTTPException(401, "Invalid token type")
    return payload["sub"]


async def touch(user_id):
    await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"last_activity_at": now_iso()}, "$unset": {"nudge_sent_at": ""}})


async def get_current_user(request: Request) -> User:
    token = request.cookies.get("access_token")
    auth = request.headers.get("Authorization", "")
    if not token and auth.startswith("Bearer "):
        token = auth[7:]
    if not token:
        raise HTTPException(401, "Not authenticated")
    user = User.from_mongo(await db.users.find_one({"_id": ObjectId(decode(token, "access"))}))
    if not user:
        raise HTTPException(401, "User not found")
    return user


# ---------- Auth routes ----------
@api.post("/auth/register")
async def register(body: RegisterIn, response: Response, background: BackgroundTasks):
    email = body.email.lower()
    if await db.users.find_one({"email": email}):
        raise HTTPException(400, "An account with this email already exists")
    user = User(name=body.name.strip(), email=email, password_hash=hash_password(body.password),
                marketing_opt_in=body.marketing_opt_in, created_at=now_iso(), last_activity_at=now_iso(), referred_by=body.referred_by)
    res = await db.users.insert_one(user.to_mongo())
    user.id = str(res.inserted_id)
    logger.info("Registered user %s marketing_opt_in=%s", email, user.marketing_opt_in)
    background.add_task(send_welcome_email, email, user.name)
    if user.marketing_opt_in:
        background.add_task(create_contact, email, user.name)
    set_auth_cookies(response, user.id)
    return user.public()


@api.post("/auth/login")
async def login(body: LoginIn, request: Request, response: Response):
    email = body.email.lower()
    ident = email
    attempt = await db.login_attempts.find_one({"identifier": ident})
    if attempt and attempt.get("count", 0) >= 5:
        locked_at = datetime.fromisoformat(attempt["last"])
        if datetime.now(timezone.utc) - locked_at < timedelta(minutes=15):
            raise HTTPException(429, "Too many failed attempts. Try again in 15 minutes.")
        await db.login_attempts.delete_one({"identifier": ident})
    user = User.from_mongo(await db.users.find_one({"email": email}))
    if not user or not verify_password(body.password, user.password_hash):
        await db.login_attempts.update_one({"identifier": ident}, {"$inc": {"count": 1}, "$set": {"last": now_iso()}}, upsert=True)
        raise HTTPException(401, "Invalid email or password")
    await db.login_attempts.delete_one({"identifier": ident})
    await touch(user.id)
    set_auth_cookies(response, user.id)
    return user.public()


@api.post("/auth/logout")
async def logout(response: Response):
    for k in ("access_token", "refresh_token"):
        response.delete_cookie(k, path="/", secure=True, samesite="none")
    return {"ok": True}


def is_admin(user) -> bool:
    admins = {e.strip().lower() for e in os.environ["ADMIN_EMAILS"].split(",") if e.strip()}
    return user.email.lower() in admins


async def require_admin(user: "User" = Depends(get_current_user)):
    if not is_admin(user):
        raise HTTPException(403, "Admins only")
    return user


@api.get("/verses")
async def get_verses():
    doc = await db.settings.find_one({"_id": "verses"})
    return {"verses": doc["verses"] if doc else DEFAULT_VERSES}


@api.put("/admin/verses")
async def put_verses(body: VersesIn, admin: User = Depends(require_admin)):
    verses = [v.model_dump() for v in body.verses]
    await db.settings.update_one({"_id": "verses"}, {"$set": {"verses": verses, "updated_by": admin.email, "updated_at": now_iso()}}, upsert=True)
    logger.info("Verses updated by %s (%s verses)", admin.email, len(verses))
    return {"verses": verses}


class SharingIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    book_url: str = Field(default="", max_length=500, pattern=r"^(https?://\S+)?$")
    share_subject: str = Field(min_length=1, max_length=120)
    share_message: str = Field(min_length=1, max_length=2000)


DEFAULT_SHARING = {
    "book_url": "",
    "share_subject": "Join me at The Lord's Gym",
    "share_message": "I've been working through The Lord's Gym: Discipleship Training, One Rep at a Time, and it's been helping me grow in my walk with Christ, one rep at a time. I'd love for you to grab a copy of the book and join the conversation with me.",
}


@api.get("/sharing")
async def get_sharing():
    doc = await db.settings.find_one({"_id": "sharing"}) or {}
    return {k: doc.get(k, v) for k, v in DEFAULT_SHARING.items()}


@api.put("/admin/sharing")
async def put_sharing(body: SharingIn, admin: User = Depends(require_admin)):
    data = body.model_dump()
    await db.settings.update_one({"_id": "sharing"}, {"$set": {**data, "updated_by": admin.email, "updated_at": now_iso()}}, upsert=True)
    return data



class EndorsementIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    text: str = Field(min_length=1, max_length=1200)
    name: str = Field(min_length=1, max_length=100)
    position: str = Field(default="", max_length=150)
    books: list[str] = Field(default_factory=list, max_length=10)


class EndorsementsIn(BaseModel):
    layout: str = Field(pattern=r"^(cards|spotlight|list)$")
    items: list[EndorsementIn] = Field(default_factory=list, max_length=30)


@api.get("/endorsements")
async def get_endorsements():
    doc = await db.settings.find_one({"_id": "endorsements"}) or {}
    return {"layout": doc.get("layout", "cards"), "items": doc.get("items", [])}


@api.put("/admin/endorsements")
async def put_endorsements(body: EndorsementsIn, admin: User = Depends(require_admin)):
    data = body.model_dump()
    data["items"] = [{**i, "books": [b.strip() for b in i["books"] if b.strip()]} for i in data["items"]]
    await db.settings.update_one({"_id": "endorsements"}, {"$set": {**data, "updated_by": admin.email, "updated_at": now_iso()}}, upsert=True)
    return data



def check_slug(slug):
    if slug not in PAGE_SLUGS:
        raise HTTPException(404, "Page not found")


@api.get("/pages/{slug}")
async def get_page(slug: str):
    check_slug(slug)
    doc = await db.settings.find_one({"_id": f"page:{slug}"})
    src = doc or DEFAULT_PAGES[slug]
    return {k: src.get(k, "") for k in ("eyebrow", "title", "body", "photo_url")}


@api.put("/admin/pages/{slug}")
async def put_page(slug: str, body: PageIn, admin: User = Depends(require_admin)):
    check_slug(slug)
    data = body.model_dump()
    await db.settings.update_one({"_id": f"page:{slug}"}, {"$set": {**data, "updated_by": admin.email, "updated_at": now_iso()}}, upsert=True)
    logger.info("Page %s updated by %s", slug, admin.email)
    return data


# ---------- Paywall: discount codes, Stripe checkout, videos ----------
stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
PACKAGE_PRICE = 40.00
PACKAGE_LOOKUP_KEY = "tlg_full_access_40"
DEFAULT_CODES = [("BeataTeam", 100), ("EarlyAdopters", 50), ("SeniorLeader", 75), ("TLG Staff", 100)]


def norm_code(code):
    return "".join(code.split()).lower()


class CodeIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    code: str = Field(min_length=2, max_length=40)
    percent_off: int = Field(ge=1, le=100)
    active: bool = True


class CheckoutIn(BaseModel):
    code: Optional[str] = Field(default=None, max_length=40)
    origin_url: str = Field(default="https://x", pattern=r"^https?://")


def code_out(d):
    return {"id": d["_id"], "code": d["code"], "percent_off": d["percent_off"], "active": d["active"], "uses": d.get("uses", 0)}


async def find_code(code):
    if not code or not code.strip():
        return None
    d = await db.discount_codes.find_one({"_id": norm_code(code), "active": True})
    if not d:
        raise HTTPException(400, "That discount code isn't valid")
    return d


def price_after(d):
    return round(PACKAGE_PRICE * (100 - (d["percent_off"] if d else 0)) / 100, 2)


async def grant_access(user_id, source):
    await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"has_access": True, "access_source": source, "access_granted_at": now_iso()}})


@api.get("/admin/codes")
async def list_codes(admin: User = Depends(require_admin)):
    return {"codes": [code_out(d) async for d in db.discount_codes.find().sort("created_at", 1)]}


@api.post("/admin/codes")
async def create_code(body: CodeIn, admin: User = Depends(require_admin)):
    key = norm_code(body.code)
    if await db.discount_codes.find_one({"_id": key}):
        raise HTTPException(400, "A code with that name already exists")
    doc = {"_id": key, **body.model_dump(), "uses": 0, "created_at": now_iso()}
    await db.discount_codes.insert_one(doc)
    return code_out(doc)


@api.put("/admin/codes/{code_id}")
async def update_code(code_id: str, body: CodeIn, admin: User = Depends(require_admin)):
    res = await db.discount_codes.update_one({"_id": code_id}, {"$set": {"percent_off": body.percent_off, "active": body.active}})
    if not res.matched_count:
        raise HTTPException(404, "Code not found")
    return code_out(await db.discount_codes.find_one({"_id": code_id}))


@api.delete("/admin/codes/{code_id}")
async def delete_code(code_id: str, admin: User = Depends(require_admin)):
    await db.discount_codes.delete_one({"_id": code_id})
    return {"ok": True}


@api.post("/payments/quote")
async def quote(body: CheckoutIn, user: User = Depends(get_current_user)):
    d = await find_code(body.code)
    return {"price": PACKAGE_PRICE, "percent_off": d["percent_off"] if d else 0, "total": price_after(d)}


@api.post("/payments/checkout")
async def checkout(body: CheckoutIn, user: User = Depends(get_current_user)):
    if has_access(user):
        raise HTTPException(400, "You already have Full Access")
    d = await find_code(body.code)
    total = price_after(d)
    if total <= 0:
        await db.discount_codes.update_one({"_id": d["_id"]}, {"$inc": {"uses": 1}})
        await grant_access(user.id, f"code:{d['code']}")
        return {"granted": True}
    try:
        price = stripe.Price.list(lookup_keys=[PACKAGE_LOOKUP_KEY], active=True, limit=1).data[0]
        allowed = [u.strip().rstrip("/") for u in os.environ["FRONTEND_URL"].split(",")]
        origin = body.origin_url.rstrip("/")
        origin = origin if origin in allowed else os.environ["SITE_URL"].rstrip("/")
        session = stripe.checkout.Session.create(
        line_items=[{"price_data": {"currency": "usd", "product": price.product, "unit_amount": int(round(total * 100))}, "quantity": 1}],
        mode="payment", customer_email=user.email,
        success_url=f"{origin}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{origin}/payment/cancel",
        metadata={"user_id": user.id, "code": d["code"] if d else ""},
        managed_payments={"enabled": True},
        )
    except (IndexError, stripe.error.StripeError) as exc:
        logger.warning("Stripe checkout failed: %s", exc)
        raise HTTPException(502, "Checkout is temporarily unavailable. Please try again shortly.")
    await db.payment_transactions.insert_one({
        "session_id": session.id, "user_id": user.id, "amount": float(total), "currency": "usd",
        "code_id": d["_id"] if d else None, "status": "initiated", "payment_status": "pending",
        "created_at": now_iso(), "updated_at": now_iso(),
    })
    return {"checkout_url": session.url, "session_id": session.id}


async def mark_paid(session_id, extra=None):
    res = await db.payment_transactions.find_one_and_update(
        {"session_id": session_id, "payment_status": {"$ne": "paid"}},
        {"$set": {"status": "completed", "payment_status": "paid", "updated_at": now_iso(), **(extra or {})}})
    if res:
        await grant_access(res["user_id"], f"stripe:{session_id}")
        if res.get("code_id"):
            await db.discount_codes.update_one({"_id": res["code_id"]}, {"$inc": {"uses": 1}})


@api.get("/payments/status/{session_id}")
async def payment_status(session_id: str):
    rec = await db.payment_transactions.find_one({"session_id": session_id})
    if not rec:
        raise HTTPException(404, "Transaction not found")
    if rec["payment_status"] != "paid":
        try:
            s = stripe.checkout.Session.retrieve(session_id)
            if s.payment_status == "paid" or s.status == "complete":
                await mark_paid(session_id, {"stripe_payment_intent_id": s.payment_intent})
                rec = await db.payment_transactions.find_one({"session_id": session_id})
        except stripe.error.StripeError:
            pass
    return {"session_id": rec["session_id"], "status": rec["status"], "payment_status": rec["payment_status"]}


@api.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(payload, request.headers.get("stripe-signature", ""), os.environ["STRIPE_WEBHOOK_SECRET"])
    except (stripe.error.SignatureVerificationError, ValueError):
        raise HTTPException(400, "Invalid signature")
    obj, t = event["data"]["object"], event["type"]
    if t in ("checkout.session.completed", "checkout.session.async_payment_succeeded") and obj.get("payment_status") == "paid":
        await mark_paid(obj["id"], {"stripe_payment_intent_id": obj.get("payment_intent")})
    elif t in ("checkout.session.expired", "checkout.session.async_payment_failed"):
        await db.payment_transactions.update_one({"session_id": obj["id"], "payment_status": {"$ne": "paid"}},
                                                 {"$set": {"status": "expired", "payment_status": "failed", "updated_at": now_iso()}})
    return {"status": "ok"}


VIDEO_KEYS = ["registration_thanks", "initial_congrats", "pastor_final"] + [f"section_{s}" for s in SECTION_REVIEW_IDS]
PAID_VIDEO_KEYS = {"pastor_final"} | {f"section_{s}" for s in SECTION_REVIEW_IDS}


class VideoIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    title: str = Field(default="", max_length=120)
    url: str = Field(default="", max_length=300, pattern=r"^(https://(www\.|player\.)?vimeo\.com/\S+)?$")


class VideosIn(BaseModel):
    videos: Dict[str, VideoIn]


async def load_videos():
    doc = await db.settings.find_one({"_id": "videos"}) or {}
    stored = doc.get("videos", {})
    return {k: {"title": stored.get(k, {}).get("title", ""), "url": stored.get(k, {}).get("url", "")} for k in VIDEO_KEYS}


@api.get("/videos")
async def get_videos(user: User = Depends(get_current_user)):
    vids = await load_videos()
    if not has_access(user):
        for k in PAID_VIDEO_KEYS:
            vids[k]["url"] = ""
    return {"videos": vids, "has_access": has_access(user)}


@api.put("/admin/videos")
async def put_videos(body: VideosIn, admin: User = Depends(require_admin)):
    current = await load_videos()
    current.update({k: v.model_dump() for k, v in body.videos.items() if k in VIDEO_KEYS})
    await db.settings.update_one({"_id": "videos"}, {"$set": {"videos": current, "updated_by": admin.email}}, upsert=True)
    return {"videos": await load_videos()}


@api.post("/assessments/7/video-watched")
async def final_video_watched(user: User = Depends(get_current_user)):
    if not has_access(user):
        raise HTTPException(402, "Unlock the Full Training Program to access this")
    await db.users.update_one({"_id": ObjectId(user.id)}, {"$set": {"final_video_watched": True}})
    return {"ok": True}


@api.get("/auth/me")
async def me(user: User = Depends(get_current_user)):
    return user.public()


@api.post("/auth/refresh")
async def refresh(request: Request, response: Response):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(401, "No refresh token")
    user_id = decode(token, "refresh")
    if not await db.users.find_one({"_id": ObjectId(user_id)}):
        raise HTTPException(401, "User not found")
    set_auth_cookies(response, user_id)
    return {"ok": True}


# ---------- Assessment logic ----------
async def user_progress(user_id) -> Dict[int, Progress]:
    docs = await db.progress.find({"user_id": user_id}).to_list(100)
    return {d["assessment_id"]: Progress.from_mongo(d) for d in docs}


def done(prog, aid):
    return aid in prog and prog[aid].status == "completed"


def has_access(user):
    return user.has_access or is_admin(user)


def lock_state(a, prog, user):
    if a["tier"] == "paid" and not has_access(user):
        return "paywall"
    ok = a["kind"] != "final" or all(done(prog, s) for s in SECTION_REVIEW_IDS)
    return None if ok else "sequence"


def guard(a, prog, user):
    state = lock_state(a, prog, user)
    if state == "paywall":
        raise HTTPException(402, "Unlock the Full Training Program to access this")
    if state == "sequence":
        raise HTTPException(403, "Complete the earlier steps first")


def get_assessment(aid):
    a = ASSESS_BY_ID.get(aid)
    if not a:
        raise HTTPException(404, "Assessment not found")
    return a


def clean_answers(a, answers):
    valid = {q["id"] for q in a["questions"]}
    return {k: v for k, v in answers.items() if k in valid and 1 <= v <= SCALE_MAX}


def tier(tiers, score):
    return [t for t in tiers if score >= t["min"]][-1]


def section_max(aid, sid):
    return sum(SCALE_MAX for q in ASSESS_BY_ID[aid]["questions"] if q["section"] == sid)


def result_payload(a, p: Progress):
    sections = []
    if a["has_sections"]:
        for s in SECTIONS:
            score = p.section_scores.get(str(s["id"]), 0)
            t = tier(a["section_tiers"], score)
            sections.append({**s, "score": score, "max": section_max(a["id"], s["id"]),
                             "designation": t["label"], "meaning": t["meaning"]})
    return {
        "assessment_id": a["id"], "title": a["title"], "subtitle": a["subtitle"], "kind": a["kind"],
        "score": p.score, "max_score": p.max_score, "designation": p.designation,
        "meaning": p.meaning, "completed_at": p.completed_at, "sections": sections,
    }


@api.get("/assessments")
async def list_assessments(user: User = Depends(get_current_user)):
    prog = await user_progress(user.id)
    items = []
    for a in ASSESSMENTS:
        p = prog.get(a["id"])
        state = lock_state(a, prog, user)
        items.append({
            "id": a["id"], "title": a["title"], "subtitle": a["subtitle"], "description": a["description"],
            "kind": a["kind"], "tier": a["tier"],
            "question_count": len(a["questions"]),
            "answered_count": len(p.answers) if p else 0,
            "status": p.status if p else "not_started",
            "unlocked": state is None, "lock": state,
            "score": p.score if p else None, "max_score": p.max_score if p else None,
            "designation": p.designation if p else None,
        })
    return {"assessments": items, "has_access": has_access(user),
            "master_unlocked": has_access(user) and done(prog, FINAL_ASSESSMENT_ID)}


@api.get("/assessments/{aid}")
async def get_one(aid: int, user: User = Depends(get_current_user)):
    a = get_assessment(aid)
    prog = await user_progress(user.id)
    guard(a, prog, user)
    p = prog.get(aid)
    video_required = a["kind"] == "final" and not user.final_video_watched
    return {
        "id": a["id"], "title": a["title"], "subtitle": a["subtitle"], "description": a["description"],
        "kind": a["kind"], "video_required": video_required,
        "questions": [] if video_required else [{"id": q["id"], "text": q["text"], "section": q["section"]} for q in a["questions"]],
        "sections": SECTIONS if a["has_sections"] else [],
        "answers": p.answers if p else {}, "status": p.status if p else "not_started",
    }


@api.put("/assessments/{aid}/progress")
async def save_progress(aid: int, body: AnswersIn, user: User = Depends(get_current_user)):
    a = get_assessment(aid)
    prog = await user_progress(user.id)
    guard(a, prog, user)
    if a["kind"] == "final" and not user.final_video_watched:
        raise HTTPException(403, "Watch the pastor's video first")
    if aid in prog and prog[aid].status == "completed":
        raise HTTPException(400, "Assessment already completed")
    answers = clean_answers(a, body.answers)
    await touch(user.id)
    await db.progress.update_one(
        {"user_id": user.id, "assessment_id": aid},
        {"$set": {"answers": answers, "status": "in_progress", "updated_at": now_iso()}},
        upsert=True,
    )
    return {"ok": True, "answered_count": len(answers)}


@api.post("/assessments/{aid}/submit")
async def submit(aid: int, body: AnswersIn, background: BackgroundTasks, user: User = Depends(get_current_user)):
    a = get_assessment(aid)
    prog = await user_progress(user.id)
    guard(a, prog, user)
    if a["kind"] == "final" and not user.final_video_watched:
        raise HTTPException(403, "Watch the pastor's video first")
    if aid in prog and prog[aid].status == "completed":
        raise HTTPException(400, "Assessment already completed")
    answers = clean_answers(a, body.answers)
    if len(answers) != len(a["questions"]):
        raise HTTPException(400, "Please answer every question before submitting")
    score = sum(answers.values())
    max_score = len(a["questions"]) * SCALE_MAX
    band = tier(a["total_tiers"], score) if a["total_tiers"] else {"label": None, "meaning": None}
    section_scores: Dict[str, int] = {}
    for q in a["questions"]:
        if q["section"]:
            key = str(q["section"])
            section_scores[key] = section_scores.get(key, 0) + answers[q["id"]]
    p = Progress(user_id=user.id, assessment_id=aid, answers=answers, status="completed", score=score,
                 max_score=max_score, designation=band["label"], meaning=band["meaning"],
                 section_scores=section_scores, completed_at=now_iso(), updated_at=now_iso())
    await touch(user.id)
    await db.progress.update_one({"user_id": user.id, "assessment_id": aid}, {"$set": p.to_mongo()}, upsert=True)
    if aid == FINAL_ASSESSMENT_ID:
        background.add_task(send_completion_email, user.email, user.name, score, max_score)
    return result_payload(a, p)


@api.get("/assessments/{aid}/result")
async def get_result(aid: int, user: User = Depends(get_current_user)):
    a = get_assessment(aid)
    p = Progress.from_mongo(await db.progress.find_one({"user_id": user.id, "assessment_id": aid}))
    if not p or p.status != "completed":
        raise HTTPException(404, "Result not available yet")
    return result_payload(a, p)


@api.get("/master-results")
async def master_results(user: User = Depends(get_current_user)):
    return await compute_master(user)


@api.get("/master-results/scorecard")
async def scorecard(background: BackgroundTasks, user: User = Depends(get_current_user)):
    data = await compute_master(user)
    d1, today = tier(TOTAL_125_TIERS, data["total"]["day1"]), tier(TOTAL_125_TIERS, data["total"]["today"])
    data.update(day1_designation=d1["label"], today_designation=today["label"], today_meaning=today["meaning"])
    pdf = build_scorecard_pdf(user.name, datetime.now(timezone.utc).strftime("%B %d, %Y"), data)
    background.add_task(send_scorecard_email, user.email, user.name, data, pdf)
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": 'attachment; filename="Lords-Gym-Training-Scorecard.pdf"'})


async def compute_master(user: User):
    prog = await user_progress(user.id)
    if not has_access(user):
        raise HTTPException(402, "Unlock the Full Training Program to see Master Results")
    if not done(prog, FINAL_ASSESSMENT_ID):
        raise HTTPException(403, "Complete all 7 assessments to unlock Master Results")
    base, final = prog[BASELINE_ASSESSMENT_ID], prog[FINAL_ASSESSMENT_ID]
    rows = []
    for s in SECTIONS:
        d1 = base.section_scores.get(str(s["id"]), 0)
        today = final.section_scores.get(str(s["id"]), 0)
        rows.append({"section": s["title"], "chapters": s["chapters"], "day1": d1, "today": today,
                     "change": today - d1, "max": section_max(FINAL_ASSESSMENT_ID, s["id"])})
    total = {"day1": sum(r["day1"] for r in rows), "today": sum(r["today"] for r in rows)}
    total["change"] = total["today"] - total["day1"]
    total["max"] = sum(r["max"] for r in rows)
    reviews = [{"title": ASSESS_BY_ID[s]["title"], "chapters": ASSESS_BY_ID[s]["subtitle"], "score": prog[s].score,
                "max": prog[s].max_score, "designation": prog[s].designation} for s in SECTION_REVIEW_IDS]
    return {"rows": rows, "total": total, "reviews": reviews}


async def run_day2_reminders():
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
    done = {d["user_id"] async for d in db.progress.find({"assessment_id": 1, "status": "completed"}, {"user_id": 1})}
    sent = 0
    async for doc in db.users.find({"created_at": {"$lte": cutoff}, "day2_reminder_sent_at": {"$exists": False}}):
        user = User.from_mongo(doc)
        if user.id in done:
            continue
        claimed = await db.users.update_one(
            {"_id": doc["_id"], "day2_reminder_sent_at": {"$exists": False}},
            {"$set": {"day2_reminder_sent_at": now_iso()}},
        )
        if claimed.modified_count:
            await send_reminder_email(user.email, user.name)
            sent += 1
    logger.info("Day 2 reminders sent: %s", sent)


async def run_journey_nudges():
    cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    counts = {d["_id"]: d["n"] async for d in db.progress.aggregate([
        {"$match": {"status": "completed"}}, {"$group": {"_id": "$user_id", "n": {"$sum": 1}}}])}
    sent = 0
    async for doc in db.users.find({"last_activity_at": {"$lte": cutoff}, "nudge_sent_at": {"$exists": False}}):
        user = User.from_mongo(doc)
        if not 1 <= counts.get(user.id, 0) < len(ASSESSMENTS):
            continue
        claimed = await db.users.update_one(
            {"_id": doc["_id"], "nudge_sent_at": {"$exists": False}}, {"$set": {"nudge_sent_at": now_iso()}})
        if claimed.modified_count:
            await send_nudge_email(user.email, user.name)
            sent += 1
    logger.info("Journey nudges sent: %s", sent)


async def accept_cron(request: Request, background: BackgroundTasks, job):
    auth = request.headers.get("Authorization", "")
    token = auth[7:] if auth.startswith("Bearer ") else ""
    if not token or not hmac.compare_digest(token, os.environ["WEBHOOK_CRON_SECRET"]):
        raise HTTPException(401, "Unauthorized")
    try:
        envelope = await request.json()
    except Exception:
        raise HTTPException(400, "Invalid body")
    run_id = request.headers.get("X-Webhook-Id") or (envelope or {}).get("run_id")
    if not run_id:
        raise HTTPException(400, "Missing run_id")
    res = await db.cron_runs.update_one({"_id": f"{job.__name__}:{run_id}"}, {"$setOnInsert": {"at": now_iso()}}, upsert=True)
    if res.upserted_id is not None:
        background.add_task(job)
    return {"accepted": True}


@api.post("/cron/day2-reminder")
async def cron_day2_reminder(request: Request, background: BackgroundTasks):
    # Cron endpoints must ack 2xx immediately; enqueue/background the actual work.
    return await accept_cron(request, background, run_day2_reminders)


@api.post("/cron/journey-nudge")
async def cron_journey_nudge(request: Request, background: BackgroundTasks):
    # Cron endpoints must ack 2xx immediately; enqueue/background the actual work.
    return await accept_cron(request, background, run_journey_nudges)


app.include_router(api)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ["FRONTEND_URL"].split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await db.users.create_index("email", unique=True)
    await db.login_attempts.create_index("identifier")
    await db.progress.create_index([("user_id", 1), ("assessment_id", 1)], unique=True)
    await db.assessments.delete_many({"_id": {"$nin": list(ASSESS_BY_ID)}})
    for a in ASSESSMENTS:
        await db.assessments.replace_one({"_id": a["id"]}, {"_id": a["id"], **{k: v for k, v in a.items() if k != "id"}}, upsert=True)
    for code, pct in DEFAULT_CODES:
        await db.discount_codes.update_one({"_id": norm_code(code)}, {"$setOnInsert": {"code": code, "percent_off": pct, "active": True, "uses": 0, "created_at": now_iso()}}, upsert=True)


@app.on_event("shutdown")
async def shutdown():
    client.close()
