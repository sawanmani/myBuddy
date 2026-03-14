import os
def clean(key, required=False):
    val = os.getenv(key, "")
    if val: val = val.strip()
    if required and not val: raise ValueError(f"{key} missing!")
    return val

TELEGRAM_BOT_TOKEN = clean("TELEGRAM_BOT_TOKEN", required=True)
OPENROUTER_API_KEY = clean("OPENROUTER_API_KEY", required=True)
SUPABASE_URL = clean("SUPABASE_URL", required=True)
SUPABASE_KEY = clean("SUPABASE_KEY", required=True)
MODEL = "qwen/qwen2.5-7b-instruct"
SYSTEM_PROMPT = "You are a helpful Telegram AI assistant named Sawan Buddy."