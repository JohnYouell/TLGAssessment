# Seed/cleanup for Account + Invites UI tests: python seed_account_ui.py seed|cleanup
import sys
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
from pymongo import MongoClient


def _env(key):
    for line in open("/app/backend/.env"):
        if line.startswith(key + "="):
            return line.split("=", 1)[1].strip().strip('"')


db = MongoClient(_env("MONGO_URL"))[_env("DB_NAME")]
PREFIX = "test_accui_"


def user(email, pw="test1234", **extra):
    now = datetime.now(timezone.utc).isoformat()
    doc = {"name": "TEST AccUI", "email": email, "password_hash": bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode() if pw else "",
           "marketing_opt_in": False, "created_at": now, "last_activity_at": now, "has_access": False,
           "final_video_watched": False, "token_version": 0, **extra}
    return str(db.users.insert_one(doc).inserted_id)


def cleanup():
    ids = [str(u["_id"]) for u in db.users.find({"email": {"$regex": f"^{PREFIX}|^test_inv_"}})]
    db.share_events.delete_many({"user_id": {"$in": ids}})
    db.progress.delete_many({"user_id": {"$in": ids}})
    db.login_attempts.delete_many({"identifier": {"$regex": f"^{PREFIX}|^test_inv_"}})
    return db.users.delete_many({"email": {"$regex": f"^{PREFIX}|^test_inv_"}}).deleted_count


if __name__ != "__main__":
    pass
elif sys.argv[1] == "seed":
    cleanup()
    uid = user(f"{PREFIX}main@example.com")
    user(f"{PREFIX}friend@example.com", referred_by=uid)
    gid = user(f"{PREFIX}google@example.com", pw="", google_id="g1")
    user("test_inv_admin@example.com")
    tok = jwt.encode({"sub": gid, "type": "access", "v": 0, "exp": datetime.now(timezone.utc) + timedelta(minutes=14)},
                     _env("JWT_SECRET"), algorithm="HS256")
    print("MAIN_ID", uid)
    print("GOOGLE_TOKEN", tok)
else:
    print("deleted users", cleanup())
