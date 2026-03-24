from motor.motor_asyncio import AsyncIOMotorClient
import hashlib
from core.config import DB_URL

# Connect to MongoDB
client = AsyncIOMotorClient(DB_URL)
db = client.telegram_news
posts_col = db.posts

async def is_duplicate_hash(text):
    """Layer 1: Exact Hash Match"""
    if not text:
        return False, ""
    text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
    exists = await posts_col.find_one({"hash": text_hash})
    return bool(exists), text_hash

async def get_recent_posts(limit=100):
    """Get recent items for fuzzy semantic checks"""
    cursor = posts_col.find().sort("_id", -1).limit(limit)
    return await cursor.to_list(length=limit)

async def save_post(text, text_hash, source):
    """Save post state into DB to prevent recurring duplicates"""
    await posts_col.insert_one({
        "text": text,
        "hash": text_hash,
        "source": source
    })
