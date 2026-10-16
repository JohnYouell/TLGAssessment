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
)
from scorecard import build_scorecard_pdf
from brevo import create_contact, send_scorecard_email

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

    def public(self):
        return {"id": self.id, "name": self.name, "email": self.email, "marketing_opt_in": self.marketing_opt_in}


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
                marketing_opt_in=body.marketing_opt_in, created_at=now_iso())
    res = await db.users.insert_one(user.to_mongo())
    user.id = str(res.inserted_id)
    logger.info("Registered user %s marketing_opt_in=%s", email, user.marketing_opt_in)
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
    set_auth_cookies(response, user.id)
    return user.public()


@api.post("/auth/logout")
async def logout(response: Response):
    for k in ("access_token", "refresh_token"):
        response.delete_cookie(k, path="/", secure=True, samesite="none")
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


def is_unlocked(aid, prog):
    return aid == 1 or (aid - 1 in prog and prog[aid - 1].status == "completed")


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
        "assessment_id": a["id"], "title": a["title"], "subtitle": a["subtitle"],
        "score": p.score, "max_score": p.max_score, "designation": p.designation,
        "meaning": p.meaning, "completed_at": p.completed_at, "sections": sections,
    }


@api.get("/assessments")
async def list_assessments(user: User = Depends(get_current_user)):
    prog = await user_progress(user.id)
    items = []
    for a in ASSESSMENTS:
        p = prog.get(a["id"])
        items.append({
            "id": a["id"], "title": a["title"], "subtitle": a["subtitle"], "description": a["description"],
            "question_count": len(a["questions"]),
            "answered_count": len(p.answers) if p else 0,
            "status": p.status if p else "not_started",
            "unlocked": is_unlocked(a["id"], prog),
            "score": p.score if p else None, "max_score": p.max_score if p else None,
            "designation": p.designation if p else None,
        })
    return {"assessments": items, "master_unlocked": all(i["status"] == "completed" for i in items)}


@api.get("/assessments/{aid}")
async def get_one(aid: int, user: User = Depends(get_current_user)):
    a = get_assessment(aid)
    prog = await user_progress(user.id)
    if not is_unlocked(aid, prog):
        raise HTTPException(403, "Complete the previous assessment first")
    p = prog.get(aid)
    return {
        "id": a["id"], "title": a["title"], "subtitle": a["subtitle"], "description": a["description"],
        "questions": [{"id": q["id"], "text": q["text"], "section": q["section"]} for q in a["questions"]],
        "sections": SECTIONS if a["has_sections"] else [],
        "answers": p.answers if p else {}, "status": p.status if p else "not_started",
    }


@api.put("/assessments/{aid}/progress")
async def save_progress(aid: int, body: AnswersIn, user: User = Depends(get_current_user)):
    a = get_assessment(aid)
    prog = await user_progress(user.id)
    if not is_unlocked(aid, prog):
        raise HTTPException(403, "Complete the previous assessment first")
    if aid in prog and prog[aid].status == "completed":
        raise HTTPException(400, "Assessment already completed")
    answers = clean_answers(a, body.answers)
    await db.progress.update_one(
        {"user_id": user.id, "assessment_id": aid},
        {"$set": {"answers": answers, "status": "in_progress", "updated_at": now_iso()}},
        upsert=True,
    )
    return {"ok": True, "answered_count": len(answers)}


@api.post("/assessments/{aid}/submit")
async def submit(aid: int, body: AnswersIn, user: User = Depends(get_current_user)):
    a = get_assessment(aid)
    prog = await user_progress(user.id)
    if not is_unlocked(aid, prog):
        raise HTTPException(403, "Complete the previous assessment first")
    if aid in prog and prog[aid].status == "completed":
        raise HTTPException(400, "Assessment already completed")
    answers = clean_answers(a, body.answers)
    if len(answers) != len(a["questions"]):
        raise HTTPException(400, "Please answer every question before submitting")
    score = sum(answers.values())
    max_score = len(a["questions"]) * SCALE_MAX
    band = tier(a["total_tiers"], score)
    section_scores: Dict[str, int] = {}
    for q in a["questions"]:
        if q["section"]:
            key = str(q["section"])
            section_scores[key] = section_scores.get(key, 0) + answers[q["id"]]
    p = Progress(user_id=user.id, assessment_id=aid, answers=answers, status="completed", score=score,
                 max_score=max_score, designation=band["label"], meaning=band["meaning"],
                 section_scores=section_scores, completed_at=now_iso(), updated_at=now_iso())
    await db.progress.update_one({"user_id": user.id, "assessment_id": aid}, {"$set": p.to_mongo()}, upsert=True)
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
    if not all(a["id"] in prog and prog[a["id"]].status == "completed" for a in ASSESSMENTS):
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
    return {"rows": rows, "total": total}


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
    for a in ASSESSMENTS:
        await db.assessments.replace_one({"_id": a["id"]}, {"_id": a["id"], **{k: v for k, v in a.items() if k != "id"}}, upsert=True)


@app.on_event("shutdown")
async def shutdown():
    client.close()
