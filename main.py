import os
import asyncio
import re
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from core.config import API_ID, API_HASH, BOT_TOKEN, SESSION_STRING, SOURCE_CHANNELS, TARGET_CHANNEL
from db.database import is_duplicate_hash, get_recent_posts, save_post
from sources.external import fetch_rss_news
from ai.processor import translate_text, is_duplicate_fuzzy, analyze_priority_and_country, clean_source_text
from media.generator import create_image, create_video
from aiohttp import web

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

async def health_check(request):
    return web.Response(text="Bot is healthy and scraping")

async def start_dummy_server():
    app = web.Application()
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get('PORT', 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Healthcheck server listening on port {port}")

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

async def rss_polling_loop():
    """Polls external RSS feeds every 30 seconds for breaking news."""
    print("Starting RSS Polling Loop (Interval: 30s)...")
    while True:
        try:
            news_items = await fetch_rss_news()
            for item in news_items:
                # Wrap each RSS item into a dummy object for process_message
                class DummyMsg:
                    def __init__(self, text):
                        self.text = text
                        self.photo = None
                        self.media = None
                
                class DummyChat:
                    def __init__(self, title):
                        self.title = title
                        self.broadcast = True
                        self.username = ""
                
                await process_message(DummyMsg(item['text']), DummyChat(item['source_name']))
        except Exception as e:
            print(f"RSS Loop Error: {e}")
        await asyncio.sleep(30)

bot.loop.create_task(worker())
bot.loop.create_task(start_dummy_server())
bot.loop.create_task(rss_polling_loop())

NEWS_KEYWORDS = ["news", "tv", "channel", "press", "agency", "media", "world", "global", "breaking", 
                 "اخبار", "الجزيرة", "العربية", "بي بي سي", "عاجل", "وكالة", "بث", "ستلايت", "قناة"]

async def process_message(msg, chat_entity=None):
    if not TARGET_CHANNEL: return

    chat = chat_entity
    
    # Check for official broadcast only
    if not getattr(chat, 'broadcast', False):
        return
        
    username = (getattr(chat, 'username', '') or '').lower()
    title = (getattr(chat, 'title', '') or '').lower()
    
    # Privacy check: Ignore personal channels by looking for news keywords in title/username
    is_official = any(kw in username or kw in title for kw in NEWS_KEYWORDS)
    if not is_official:
        return

    # Exclude our own target channel
    target_clean = TARGET_CHANNEL.replace('@', '').lower().strip()
    if username and target_clean in username:
        return

    raw_text = msg.text or ""
    if not raw_text.strip() and not msg.media: return

    # -> CLEANING (No links, no personal info)
    text = clean_source_text(raw_text)
    if not text: return

    # -> 3-Layer Duplicate Prevention
    is_dup_hash, text_hash = await is_duplicate_hash(text)
    if is_dup_hash: return

    recent_posts = await get_recent_posts(100)
    recent_texts = [p.get("text", "") for p in recent_posts]
    if is_duplicate_fuzzy(text, recent_texts): return
        
    source_name = getattr(chat, 'title', 'World Source')
    
    # -> AI Enhancement
    priority, country = analyze_priority_and_country(text, source_name)
    ar_text, en_text = translate_text(text)

    # FINAL CAPTION (Only target channel link allowed)
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

    media_path, vid_path, processed_img = None, None, None

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
    print("Fetching the latest news item from curated whitelist and subscribed channels...")
    try:
        seen_entities = set()
        count = 0
        
        # 1. Fetch from curated whitelist first (High Priority)
        for ch in SOURCE_CHANNELS:
            if count >= 50: break
            try:
                entity = await scraper.get_entity(ch)
                seen_entities.add(getattr(entity, 'id', None))
                async for msg in scraper.iter_messages(entity, limit=1):
                    await process_message(msg, entity)
                    count += 1
            except Exception: continue
            
        # 2. Fallback to other subscribed channels
        async for dialog in scraper.iter_dialogs():
            if count >= 60: break
            if dialog.is_channel and not dialog.is_group:
                if dialog.id in seen_entities: continue
                if getattr(dialog.entity, 'username', '').lower() == TARGET_CHANNEL.replace('@', '').lower():
                    continue
                try:
                    async for msg in scraper.iter_messages(dialog.entity, limit=1):
                        await process_message(msg, dialog.entity)
                        count += 1
                except Exception: pass
    except Exception as e: print(f"Startup loop error: {e}")

# Run startup script before listening
if SESSION_STRING:
    bot.loop.run_until_complete(startup_test())
    bot.loop.run_until_complete(scraper.run_until_disconnected())
else:
    bot.loop.run_until_complete(startup_test())
