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

# Model with strip() to remove any trailing spaces
HF_MODEL = os.getenv("HF_MODEL", "meta-llama/Llama-3.2-1B-Instruct").strip()

SYSTEM_PROMPT = "You are Mybuddy. Be short and helpful."
