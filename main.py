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

from aiohttp import web

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

bot.loop.create_task(worker())
bot.loop.create_task(start_dummy_server())

async def process_message(msg, chat_entity=None):
    if not TARGET_CHANNEL: return

    chat = chat_entity
    
    # Accept ONLY messages from Broadcast Channels (Bypass DMs/Groups)
    if not getattr(chat, 'broadcast', False):
        return
        
    username = getattr(chat, 'username', '') or ''
    title = getattr(chat, 'title', '') or ''
    
    # Exclude our own target channel to prevent loopbacks
    target_clean = TARGET_CHANNEL.replace('@', '').lower().strip()
    if username and target_clean in username.lower():
        return

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
    print("Fetching the latest news item from all subscribed channels to jumpstart...")
    try:
        count = 0
        async for dialog in scraper.iter_dialogs():
            if count >= 40: break # Grab up to 40 latest news max for jumpstart
            if dialog.is_channel and not dialog.is_group:
                if getattr(dialog.entity, 'username', '').lower() == TARGET_CHANNEL.replace('@', '').lower():
                    continue
                try:
                    async for msg in scraper.iter_messages(dialog.entity, limit=1):
                        await process_message(msg, dialog.entity)
                        count += 1
                except Exception:
                    pass
    except Exception as e:
        print(f"Startup loop error: {e}")

# Run startup script before listening
if SESSION_STRING:
    bot.loop.run_until_complete(startup_test())
    bot.loop.run_until_complete(scraper.run_until_disconnected())
else:
    bot.loop.run_until_complete(startup_test())
    bot.run_until_disconnected()
