import os

API_ID = os.environ.get("API_ID", "31030384")
API_HASH = os.environ.get("API_HASH", "35b04ff5fb54744d4439f3d1c41e4230")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8602549699:AAEOrF-CnILqUSLlOi-6DHf9amrVaAYjsu8")
SESSION_STRING = os.environ.get("SESSION_STRING", "")
DB_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
TRANSLATION_API_KEY = os.environ.get("TRANSLATION_API_KEY", "")

# Comprehensive News Sources (Arab World & Middle East)
SOURCE_CHANNELS = [
    # Global/International (Arabic Branches)
    "AJA_News", "aljazeerachannel", "bbcarabic", "CNNArabic", 
    "AlArabiya", "alhadath", "SkyNewsArabia_sn", "rtarabic", 
    "France24_ar", "ReutersArabic", "TRTArabi", "Sputnik_Arabic",
    "UNArabic", "cnbcarabia", "ajplusarabi", "dw_arabic",
    
    # Iraq
    "SabrenNewss", "almawqef_tv", "Alomhoar", "AlghadeerTv", 
    "Alghadir_News", "Baghdad_Today", "EarthNews_Iq", "AlSumariaNews",
    "AlShortaNews", "INANewIQ", "SharqiyaNews", "NRT_Arabic",
    
    # Palestine
    "QudsN", "Samanews", "SafaPs", "GazaNowN", "ShehabAgency", 
    "AlAqsaTVChannel", "Newpalestine", "PNN",
    
    # Lebanon
    "mayadeenchannel", "AlManar_News", "MTVNewsLebanon", "AlJadeedNews",
    "LbcGroup", "VdlNews", "LebanonFiles",
    
    # Gulf (KSA, UAE, Kuwait, Qatar, Bahrain, Oman)
    "AlArabiya_KSA", "AlMarsd", "SabqNews", "SaudiNews50",
    "SharjahTV", "AbuDhabiTV", "AlEtihadNews", "AlWatanNews",
    "EremNews", "GulfNews_Arabic", "KunaArabic", "OmanNewsAgency",
    
    # Egypt & North Africa
    "Cairo24", "AlMasry_AlYoum", "Youm7", "ExtraNewsTv",
    "AlWatanEgypt", "ShoroukNews", "RTNorthAfrica", "H24Info",
    "AwanMag", "AlMaghrebia", "MosaiqueFM",
    
    # Syria & Iran & Regional
    "SyriaSANA", "ShamFM", "AlWatanSyria", "iran_military_capabilities", 
    "ParsTodayArabic", "AlAlamArabic", "AlQudsAlArabi", "AnadoluAr",
    "MasirahNews", "AnsarollahMC"
]
TARGET_CHANNEL = os.environ.get("TARGET_CHANNEL", "@WorldNewsLi")
