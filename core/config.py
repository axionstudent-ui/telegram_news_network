import os

API_ID = os.environ.get("API_ID", "31030384")
API_HASH = os.environ.get("API_HASH", "35b04ff5fb54744d4439f3d1c41e4230")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8602549699:AAEOrF-CnILqUSLlOi-6DHf9amrVaAYjsu8")
SESSION_STRING = os.environ.get("SESSION_STRING", "")
DB_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
TRANSLATION_API_KEY = os.environ.get("TRANSLATION_API_KEY", "")

# 6 Specific Regional Channels + Others
SOURCE_CHANNELS = [
    "SabrenNewss",
    "almawqef_tv",
    "Alomhoar",
    "iran_military_capabilities",
    "TANFITHY",
    "mayadeenchannel"
]
TARGET_CHANNEL = os.environ.get("TARGET_CHANNEL", "@WorldNewsLi")
