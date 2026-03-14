import os

def clean(key: str, required: bool = False) -> str:
    val = os.getenv(key, "")
    if val:
        val = val.strip()
    if required and not val:
        raise ValueError(f"{key} missing")
    return val

TELEGRAM_BOT_TOKEN = clean("TELEGRAM_BOT_TOKEN", required=True)
OPENROUTER_API_KEY = clean("OPENROUTER_API_KEY", required=True)
SUPABASE_URL = clean("SUPABASE_URL", required=True)
SUPABASE_KEY = clean("SUPABASE_KEY", required=True)

MODEL = "google/gemma-2-9b-it:free"
SYSTEM_PROMPT = "You are Mybuddy, a friendly Telegram AI assistant. Be concise and helpful."
