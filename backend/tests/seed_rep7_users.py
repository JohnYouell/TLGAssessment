# Seed / cleanup TEST users for 7-Reps (chapter-removal) tests. Usage: python seed_rep7_users.py seed|clean
import os
import sys
from datetime import datetime, timezone
import bcrypt
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")
db = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
USERS = [("TEST_free7@example.com", "TEST Free", False), ("TEST_paid7@example.com", "TEST Paid", True),
         ("john.youell@newlifeokc.org", "TEST Admin", False)]
PW = "Test1234!"


def clean():
    for email, _, _ in USERS:
        u = db.users.find_one({"email": email.lower()})
        if u:
            db.progress.delete_many({"user_id": str(u["_id"])})
            db.users.delete_one({"_id": u["_id"]})
        db.login_attempts.delete_many({"identifier": email.lower()})


def seed():
    clean()
    now = datetime.now(timezone.utc).isoformat()
    for email, name, access in USERS:
        db.users.insert_one({"name": name, "email": email.lower(), "password_hash": bcrypt.hashpw(PW.encode(), bcrypt.gensalt()).decode(),
                             "marketing_opt_in": False, "created_at": now, "last_activity_at": now, "has_access": access,
                             "final_video_watched": False, "day2_reminder_sent_at": now})


if __name__ == "__main__":
    {"seed": seed, "clean": clean}[sys.argv[1]]()
    print("ok", sys.argv[1])
