import os
import asyncio
import re
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from core.config import API_ID, API_HASH, BOT_TOKEN, SESSION_STRING, SOURCE_CHANNELS, TARGET_CHANNEL
from db.database import is_duplicate_hash, get_recent_posts, save_post
from sources.external import fetch_rss_news
from ai.processor import translate_text, is_duplicate_fuzzy, analyze_priority_and_country, clean_source_text
from aiohttp import web

print("Initializing Zero-Lag News Automation Bot...")

# 1. Publisher Bot
bot = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# 2. Scraper Client
if SESSION_STRING:
    print("Scraper starting...")
    scraper = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH).start()
else:
    scraper = bot

post_queue = asyncio.Queue()
local_dedup_cache = set()

async def health_check(request):
    return web.Response(text="Zero-Lag Bot Active")

async def start_dummy_server():
    app = web.Application()
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get('PORT', 8080))
    await web.TCPSite(runner, '0.0.0.0', port).start()
    print(f"Healthcheck on port {port}")

async def worker():
    """Ultra-fast publisher"""
    while True:
        task = await post_queue.get()
        try:
            target, media, caption = task
            if media:
                await bot.send_file(target, media, caption=caption)
            else:
                await bot.send_message(target, caption)
            await asyncio.sleep(1) # Peak speed
        except Exception as e:
            print(f"Worker Error: {e}")
        finally:
            if media and os.path.exists(media):
                try: os.remove(media)
                except: pass
            post_queue.task_done()

async def rss_polling_loop():
    """Ultra-fast 30s RSS checker"""
    print("RSS Loop Active (30s)...")
    while True:
        try:
            news_items = await fetch_rss_news()
            for item in news_items:
                class Dummy: pass
                m, c = Dummy(), Dummy()
                m.text, m.photo, m.media = item['text'], None, None
                c.title, c.broadcast, c.username = item['source_name'], True, ""
                await process_message(m, c)
        except Exception as e:
            print(f"RSS Error: {e}")
        await asyncio.sleep(30)

bot.loop.create_task(worker())
bot.loop.create_task(start_dummy_server())
bot.loop.create_task(rss_polling_loop())

NEWS_KEYWORDS = ["news", "tv", "channel", "press", "agency", "media", "world", "global", "breaking", 
                 "اخبار", "الجزيرة", "العربية", "بي بي سي", "عاجل", "وكالة", "بث", "ستلايت", "قناة"]

async def process_message(msg, chat_entity=None):
    if not TARGET_CHANNEL: return
    chat = chat_entity
    if not getattr(chat, 'broadcast', False): return
    username = (getattr(chat, 'username', '') or '').lower()
    title = (getattr(chat, 'title', '') or '').lower()
    
    # Official Only
    if not any(kw in username or kw in title for kw in NEWS_KEYWORDS): return
    if username and TARGET_CHANNEL.replace('@', '').lower() in username: return

    raw_text = msg.text or ""
    if not raw_text.strip() and not msg.media: return
    text = clean_source_text(raw_text)
    if not text: return

    # Triple Deduplication (Memory -> Hash -> Fuzzy)
    is_dup_hash, text_hash = await is_duplicate_hash(text)
    if text_hash in local_dedup_cache or is_dup_hash: return
    
    local_dedup_cache.add(text_hash)
    if len(local_dedup_cache) > 1000: local_dedup_cache.clear()

    recent_posts = await get_recent_posts(100)
    if is_duplicate_fuzzy(text, [p.get("text", "") for p in recent_posts]): return
        
    source_name = getattr(chat, 'title', 'Network')
    priority, country = analyze_priority_and_country(text, source_name)
    ar_text, en_text = translate_text(text)

    caption = (
        f"{priority}\n\n"
        f"{country}\n\n"
        f"🇮🇶 {ar_text}\n\n"
        f"🇺🇸 {en_text}\n\n"
        f"📡 المصدر: {source_name}\n"
        f"━━━━━━━━━━━━━━\n"
        f"🌍 الأخبار العالمية | World News\n"
        f"🔗 t.me/{TARGET_CHANNEL.replace('@', '')}"
    )

    media_path = None
    if msg.photo: media_path = await msg.download_media("temp_dl.jpg")

    await post_queue.put((TARGET_CHANNEL, media_path, caption))
    await save_post(text, text_hash, source_name)

@scraper.on(events.NewMessage())
async def handle_incoming(event):
    chat = await event.get_chat()
    await process_message(event.message, chat)

async def startup_test():
    print("Zero-Lag Jumpstart...")
    try:
        count, seen = 0, set()
        for ch in SOURCE_CHANNELS:
            if count >= 30: break
            try:
                entity = await scraper.get_entity(ch)
                seen.add(getattr(entity, 'id', None))
                async for m in scraper.iter_messages(entity, limit=1):
                    await process_message(m, entity)
                    count += 1
            except: continue
        async for d in scraper.iter_dialogs():
            if count >= 40: break
            if d.is_channel and not d.is_group and d.id not in seen:
                if getattr(d.entity, 'username', '').lower() == TARGET_CHANNEL.replace('@', '').lower(): continue
                try:
                    async for m in scraper.iter_messages(d.entity, limit=1):
                        await process_message(m, d.entity)
                        count += 1
                except: pass
    except Exception as e: print(f"Jumpstart Error: {e}")

if SESSION_STRING:
    bot.loop.run_until_complete(startup_test())
    bot.loop.run_until_complete(scraper.run_until_disconnected())
else:
    bot.loop.run_until_complete(startup_test())
    bot.run_until_disconnected()
