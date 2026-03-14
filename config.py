# config.py - clean version
import os

def env(key: str, required: bool = False) -> str:
    val = os.getenv(key, "")
    return val.strip() if val else ("", raise ValueError(f"{key} missing"))[required]

TELEGRAM_BOT_TOKEN = env("TELEGRAM_BOT_TOKEN", True)
HF_TOKEN = env("HF_TOKEN", True)
SUPABASE_URL = env("SUPABASE_URL", True)
SUPABASE_KEY = env("SUPABASE_KEY", True)

# Model from env or default (also stripped)
HF_MODEL = os.getenv("HF_MODEL", "meta-llama/Llama-3.2-1B-Instruct").strip()
SYSTEM_PROMPT = "You are Mybuddy. Be short and helpful."
