import os


def clean_env(key: str, required: bool = False) -> str:
    """
    Get environment variable, strip whitespace, and validate.
    
    Args:
        key: Environment variable name
        required: If True, raise error when missing
    
    Returns:
        Cleaned string value
    """
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
# Best free uncensored-capable model on OpenRouter
MODEL = "qwen/qwen3-next-80b-a3b-instruct:free"

# Alternative models (uncomment to switch):
# MODEL = "venice/uncensored:free"  # Fully uncensored
# MODEL = "mistralai/mistral-small-3.1-24b:free"  # Balanced
# MODEL = "stepfun/step-3.5-flash:free"  # Maximum intelligence

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
