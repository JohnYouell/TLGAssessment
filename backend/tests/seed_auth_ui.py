# Seed/cleanup helper for auth UI tests: python seed_auth_ui.py seed|cleanup
import sys, hashlib, secrets
from datetime import datetime, timezone, timedelta
import bcrypt
from pymongo import MongoClient


def _env(key):
    for line in open("/app/backend/.env"):
        if line.startswith(key + "="):
            return line.split("=", 1)[1].strip().strip('"')


db = MongoClient(_env("MONGO_URL"))[_env("DB_NAME")]
EMAIL = "test_authui_reset@example.com"

if sys.argv[1] == "seed":
    db.users.delete_many({"email": EMAIL})
    now = datetime.now(timezone.utc).isoformat()
    uid = str(db.users.insert_one({"name": "TEST UI", "email": EMAIL, "password_hash": bcrypt.hashpw(b"oldpass1", bcrypt.gensalt()).decode(),
                                   "marketing_opt_in": False, "created_at": now, "last_activity_at": now, "has_access": False,
                                   "final_video_watched": False, "token_version": 0}).inserted_id)
    out = []
    for delta in (timedelta(hours=1), timedelta(minutes=-5)):
        raw = secrets.token_urlsafe(32)
        db.password_reset_tokens.insert_one({"token_hash": hashlib.sha256(raw.encode()).hexdigest(), "user_id": uid, "email": EMAIL,
                                             "used": False, "created_at": now, "expires_at": datetime.now(timezone.utc) + delta})
        out.append(raw)
    print("VALID", out[0]); print("EXPIRED", out[1])
else:
    ids = [str(u["_id"]) for u in db.users.find({"email": {"$regex": "^test_auth"}})]
    db.progress.delete_many({"user_id": {"$in": ids}})
    db.password_reset_tokens.delete_many({"email": {"$regex": "^test_auth"}})
    db.login_attempts.delete_many({"identifier": {"$regex": "^test_auth"}})
    print("deleted users", db.users.delete_many({"email": {"$regex": "^test_auth"}}).deleted_count)
