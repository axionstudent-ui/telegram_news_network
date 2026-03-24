from telethon.sync import TelegramClient
from telethon.sessions import StringSession

API_ID = "31030384"
API_HASH = "35b04ff5fb54744d4439f3d1c41e4230"

print("--- Telethon String Session Generator ---")
print("This will log you into your Telegram account locally to generate a session string.")
print("This allows the bot to read external channels using your account, and post using the bot.")

with TelegramClient(StringSession(), API_ID, API_HASH) as client:
    session_string = client.session.save()
    print("\n" + "="*50)
    print("Your SESSION_STRING is:\n")
    print(session_string)
    print("\n" + "="*50)
    print("Copy the long string above and add it to Railway as a new Variable named: SESSION_STRING")
