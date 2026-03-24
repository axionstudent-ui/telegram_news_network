import os
import asyncio
from telethon import TelegramClient, events
from core.config import API_ID, API_HASH, BOT_TOKEN, SOURCE_CHANNELS, TARGET_CHANNEL
from db.database import is_duplicate_hash, get_recent_posts, save_post
from ai.processor import translate_text, is_duplicate_fuzzy, analyze_priority_and_country
from media.generator import create_image, create_video

print("Initializing Advanced Global News Automation Bot...")

client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Queue system for delay management to avoid spam bursts
post_queue = asyncio.Queue()

async def worker():
    """Background loop to process and post gracefully"""
    while True:
        task = await post_queue.get()
        try:
            target, media, vid, caption = task
            if media:
                await client.send_file(target, media, caption=caption)
                if vid and os.path.exists(vid):
                    await asyncio.sleep(2) # brief delay between media
                    await client.send_file(target, vid, caption=caption)
            else:
                await client.send_message(target, caption)
                
            await asyncio.sleep(5) # Rate limiting queue
        except Exception as e:
            print(f"Worker Error: {e}")
        finally:
            if media and os.path.exists(media): os.remove(media)
            if vid and os.path.exists(vid): os.remove(vid)
            post_queue.task_done()

# Add worker to event loop
client.loop.create_task(worker())

@client.on(events.NewMessage(chats=SOURCE_CHANNELS if SOURCE_CHANNELS else None))
async def handle_incoming(event):
    if not TARGET_CHANNEL: return

    text = event.text or ""
    if not text.strip() and not event.media: return

    # -> 3-Layer Duplicate Prevention
    # 1. Exact Hash
    is_dup_hash, text_hash = await is_duplicate_hash(text)
    if is_dup_hash:
        print("Blocked: Hash Duplicate")
        return

    # 2. Text Similarity (ratio > 0.85)
    recent_posts = await get_recent_posts(100)
    recent_texts = [p.get("text", "") for p in recent_posts]
    if is_duplicate_fuzzy(text, recent_texts):
        print("Blocked: Similarity > 0.85")
        return
        
    source_name = getattr(event.chat, 'title', 'Network API') if event.chat else 'Network API'
    
    # -> AI Enhancement
    priority, country = analyze_priority_and_country(text, source_name)
    ar_text, en_text = translate_text(text)

    caption = (
        f"{priority}\n\n"
        f"{country}\n\n"
        f"🇮🇶 بالعربية:\n{ar_text}\n\n"
        f"🇺🇸 English:\n{en_text}\n\n"
        f"📡 المصدر: {source_name}\n"
        f"━━━━━━━━━━━━━━\n"
        f"🌍 الأخبار العالمية | World News\n"
        f"🔗 t.me/{TARGET_CHANNEL.replace('@', '')}"
    )

    media_path = None
    vid_path = None
    processed_img = None

    if event.photo:
        media_path = await event.download_media("temp_dl.jpg")
        processed_img = create_image(media_path, source_name)
        vid_path = create_video(processed_img, ar_text)

    # Dispatch to Publisher queue
    await post_queue.put((TARGET_CHANNEL, processed_img, vid_path, caption))

    # -> Save to DB mapping
    await save_post(text, text_hash, source_name)

    # -> Clear memory files directly (No persistent local storage!)
    # We clean up inside the orchestrator right after enqueueing it?
    # Actually, we should clean it AFTER posting so we schedule cleanup loosely or inline.
    # For a robust stateless queue, we'd clean after await file sends inside the worker, 
    # but since local instance creates it, we can defer deletion.
    # I'll let worker handle cleanup or just delete them after a delay for safety.

client.run_until_disconnected()
