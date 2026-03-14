import os

def env(key: str, required: bool = False) -> str:
    val = os.getenv(key, "")
    if val:
        val = val.strip()
    if required and not val:
        raise ValueError(f"{key} is required")
    return val

TELEGRAM_BOT_TOKEN = env("TELEGRAM_BOT_TOKEN", required=True)
HF_TOKEN = env("HF_TOKEN", required=True)
SUPABASE_URL = env("SUPABASE_URL", required=True)
SUPABASE_KEY = env("SUPABASE_KEY", required=True)

HF_MODEL = "Qwen/Qwen2.5-7B-Instruct"
SYSTEM_PROMPT = "You are Mybuddy, a friendly and concise Telegram AI assistant."