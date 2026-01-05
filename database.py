from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
# If the URL contains a database name (e.g. ...mongodb.net/dbname), AsyncIOMotorClient uses it.
# We still allow an override via DATABASE_NAME env var.
DATABASE_NAME = os.getenv("DATABASE_NAME", "dr-kathe")

client = AsyncIOMotorClient(MONGODB_URL)
db = client[DATABASE_NAME]

async def get_database():
    return db
