from deep_translator import GoogleTranslator
from thefuzz import fuzz

def translate_text(text):
    if not text: return "", ""
    try:
        trunc = text[:800]
        ar_trans = GoogleTranslator(source='auto', target='ar').translate(trunc)
        en_trans = GoogleTranslator(source='auto', target='en').translate(trunc)
        return ar_trans, en_trans
    except Exception as e:
        print(f"Translate Err: {e}")
        return text, text

def is_duplicate_fuzzy(new_text, recent_texts):
    """Layer 2 & 3: High threshold similarity + NLP heuristic fallback"""
    if not new_text or not recent_texts: return False
    for old_text in recent_texts:
        if not old_text: continue
        score = fuzz.ratio(new_text, old_text)
        if score > 85:
            return True
    return False

def analyze_priority_and_country(text, source):
    """Scoring and categorization"""
    text_lower = text.lower()
    
    # Analyze Priority
    priority = "📰 Normal News"
    if "عاجل" in text or "urgent" in text_lower or "breaking" in text_lower:
        priority = "🚨 Breaking"
    elif "مهم" in text or "important" in text_lower:
        priority = "⭐ Important"
        
    # Analyze Country Flag (Fallback is World)
    country = "🌍 World"
    if "iraq" in text_lower or "عراق" in text: country = "🇮🇶 Iraq"
    elif "iran" in text_lower or "إيران" in text: country = "🇮🇷 Iran"
    elif "lebanon" in text_lower or "لبنان" in text: country = "🇱🇧 Lebanon"
    elif "syria" in text_lower or "سوريا" in text: country = "🇸🇾 Syria"
    elif "palestine" in text_lower or "فلسطين" in text: country = "🇵🇸 Palestine"
    elif "yemen" in text_lower or "يمن" in text: country = "🇾🇪 Yemen"
    elif "usa" in text_lower or "أمريكا" in text: country = "🇺🇸 USA"
    elif "russia" in text_lower or "روسيا" in text: country = "🇷🇺 Russia"
    
    return priority, country
