import os
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from core.config import API_ID, API_HASH, BOT_TOKEN, SESSION_STRING, SOURCE_CHANNELS, TARGET_CHANNEL
from db.database import is_duplicate_hash, get_recent_posts, save_post
from ai.processor import translate_text, is_duplicate_fuzzy, analyze_priority_and_country
from media.generator import create_image, create_video

print("Initializing Advanced Global News Automation Bot...")

# 1. Publisher Bot (Posts to your channel)
bot = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# 2. Scraper Client (Reads from public channels using your Session)
if SESSION_STRING:
    print("Starting Scraper Client using User Session...")
    scraper = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH).start()
else:
    print("WARNING: SESSION_STRING not found. Bot will only be able to read channels where it is an admin!")
    scraper = bot

post_queue = asyncio.Queue()

async def worker():
    while True:
        task = await post_queue.get()
        try:
            target, media, vid, caption = task
            if media:
                await bot.send_file(target, media, caption=caption)
                if vid and os.path.exists(vid):
                    await asyncio.sleep(2)
                    await bot.send_file(target, vid, caption=caption)
            else:
                await bot.send_message(target, caption)
                
            await asyncio.sleep(5)
        except Exception as e:
            print(f"Worker Error: {e}")
        finally:
            if media and os.path.exists(media): os.remove(media)
            if vid and os.path.exists(vid): os.remove(vid)
            post_queue.task_done()

bot.loop.create_task(worker())

async def process_message(msg, chat_entity=None):
    if not TARGET_CHANNEL: return

    chat = chat_entity
    username = getattr(chat, 'username', '') or ''
    title = getattr(chat, 'title', '') or ''
    
    matched = False
    for ch in SOURCE_CHANNELS:
        c = ch.replace('@', '').lower().strip()
        if  c == username.lower() or c in title.lower():
            matched = True
            break
            
    if not matched: return

    text = msg.text or ""
    if not text.strip() and not msg.media: return

    # -> 3-Layer Duplicate Prevention
    is_dup_hash, text_hash = await is_duplicate_hash(text)
    if is_dup_hash: return

    recent_posts = await get_recent_posts(100)
    recent_texts = [p.get("text", "") for p in recent_posts]
    if is_duplicate_fuzzy(text, recent_texts): return
        
    source_name = title or 'Network API'
    
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

    if msg.photo:
        media_path = await msg.download_media("temp_dl.jpg")
        processed_img = create_image(media_path, source_name)
        vid_path = create_video(processed_img, ar_text)

    # Dispatch to Publisher queue
    await post_queue.put((TARGET_CHANNEL, processed_img, vid_path, caption))
    await save_post(text, text_hash, source_name)


@scraper.on(events.NewMessage())
async def handle_incoming(event):
    chat = await event.get_chat()
    await process_message(event.message, chat)

async def startup_test():
    print("Fetching the latest news item from all sources to jumpstart the channel...")
    try:
        for ch in SOURCE_CHANNELS:
            try:
                chat = await scraper.get_entity(ch)
                async for msg in scraper.iter_messages(chat, limit=1):
                    await process_message(msg, chat)
            except Exception as e:
                print(f"Startup fetch error for {ch}: {e}")
    except Exception as e:
        print(f"Startup loop error: {e}")

# Run startup script before listening
if SESSION_STRING:
    bot.loop.run_until_complete(startup_test())
    bot.loop.run_until_complete(scraper.run_until_disconnected())
else:
    bot.loop.run_until_complete(startup_test())
    bot.run_until_disconnected()
