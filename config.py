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

# Working free models:
HF_MODEL = "microsoft/Phi-3-mini-4k-instruct"
# Alternative: HF_MODEL = "google/gemma-2-9b-it"
# Alternative: HF_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"

SYSTEM_PROMPT = "You are Mybuddy, a friendly Telegram AI assistant. Keep replies short and helpful."
