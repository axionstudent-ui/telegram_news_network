import os

API_ID = os.environ.get("API_ID", "31030384")
API_HASH = os.environ.get("API_HASH", "35b04ff5fb54744d4439f3d1c41e4230")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8602549699:AAEOrF-CnILqUSLlOi-6DHf9amrVaAYjsu8")
SESSION_STRING = os.environ.get("SESSION_STRING", "")
DB_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
TRANSLATION_API_KEY = os.environ.get("TRANSLATION_API_KEY", "")

# 6 Specific Regional Channels + Major Global News Networks
SOURCE_CHANNELS = [
    # Regional
    "SabrenNewss",
    "almawqef_tv",
    "Alomhoar",
    "iran_military_capabilities",
    "TANFITHY",
    "mayadeenchannel",
    
    # Global Official Networks (Aljazeera, CNN, BBC, etc)
    "AJA_News",           # الجزيرة عاجل
    "aljazeerachannel",   # الجزيرة الاخبارية
    "bbcarabic",          # بي بي سي نيوز 
    "CNNArabic",          # سي ان ان عربية
    "AlArabiya",          # العربية
    "alhadath",           # الحدث
    "SkyNewsArabia_sn",   # سكاي نيوز عربية
    "rtarabic",           # روسيا اليوم
    "TRTArabi",           # تي ار تي
    "cnbcarabia",         # سي إن بي سي عربية
    "ReutersArabic",      # رويترز عربي
    "France24_ar",        # فرانس ٢٤
    "UNArabic",           # الأمم المتحدة
    "Sputnik_Arabic"      # سبوتنيك عربي
]
TARGET_CHANNEL = os.environ.get("TARGET_CHANNEL", "@WorldNewsLi")
