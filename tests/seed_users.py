import asyncio,os,bcrypt,sys
from datetime import datetime,timezone
from dotenv import load_dotenv; load_dotenv('/app/backend/.env')
from motor.motor_asyncio import AsyncIOMotorClient
EM=["john.youell@newlifeokc.org","test_member@example.com"]
async def m(mode):
    db=AsyncIOMotorClient(os.environ['MONGO_URL'])[os.environ['DB_NAME']]
    if mode=="seed":
        now=datetime.now(timezone.utc).isoformat()
        for e,n in zip(EM,["John Youell","Test Member"]):
            await db.users.update_one({"email":e},{"$set":{"name":n,"email":e,"password_hash":bcrypt.hashpw(b"AdminTest123",bcrypt.gensalt()).decode(),"marketing_opt_in":False,"created_at":now,"last_activity_at":now,"referred_by":None}},upsert=True)
    else:
        ids=[str(u["_id"]) async for u in db.users.find({"email":{"$in":EM}})]
        await db.progress.delete_many({"user_id":{"$in":ids}})
        await db.users.delete_many({"email":{"$in":EM}})
        await db.login_attempts.delete_many({})
        await db.settings.delete_one({"_id":"verses"})
    print(mode, await db.users.count_documents({"email":{"$in":EM}}))
asyncio.run(m(sys.argv[1]))
