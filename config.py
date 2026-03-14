import os


def clean_env(key: str, required: bool = False) -> str:
    """Get environment variable, strip whitespace, and validate."""
    value = os.getenv(key, "")
    if value:
        value = value.strip()
    if required and not value:
        raise ValueError(f"❌ Required environment variable '{key}' is missing or empty!")
    return value


# ========== Required Secrets ==========
TELEGRAM_BOT_TOKEN = clean_env("TELEGRAM_BOT_TOKEN", required=True)
OPENROUTER_API_KEY = clean_env("OPENROUTER_API_KEY", required=True)
SUPABASE_URL = clean_env("SUPABASE_URL", required=True)
SUPABASE_KEY = clean_env("SUPABASE_KEY", required=True)


# ========== AI Model Configuration ==========
# ✅ CORRECT Qwen3 model ID for OpenRouter free tier:
MODEL = os.getenv("OPENROUTER_MODEL", "qwen/qwen3-next-80b-a3b-instruct:free")

# 🔄 Alternative working models (uncomment one to switch):
# MODEL = os.getenv("OPENROUTER_MODEL", "google/gemma-2-9b-it:free")
# MODEL = os.getenv("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct:free")
# MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.2-3b-instruct:free")
# MODEL = os.getenv("OPENROUTER_MODEL", "venice/uncensored:free")  # Uncensored

# System prompt for the AI
SYSTEM_PROMPT = """You are Sawan Buddy, a friendly and helpful AI assistant for Telegram.

Guidelines:
- Be concise and natural (Telegram messages are short)
- Be engaging and warm in tone
- Answer questions directly
- If unsure, say so honestly
- Keep responses under 3-4 sentences when possible
- Use emojis sparingly 😊

You are helpful, harmless, and honest."""
