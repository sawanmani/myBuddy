import requests
from fastapi import FastAPI, Request
from telegram import Update
import os
import json

from config import (
    TELEGRAM_BOT_TOKEN,
    OPENROUTER_API_KEY,
    SUPABASE_URL,
    SUPABASE_KEY,
    MODEL,
    SYSTEM_PROMPT
)

app = FastAPI()
SUPABASE_TABLE = "chat_logs"
TG_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


# ---------- Telegram API Helper ----------
def tg_post(method: str, data: dict):
    """Make POST request to Telegram API"""
    url = f"{TG_API}/{method}"
    try:
        r = requests.post(url, json=data, timeout=15)
        return r.json()
    except Exception as e:
        print(f"❌ Telegram API error: {e}")
        return None


def send_message(chat_id: int, text: str):
    """Send text message to Telegram"""
    return tg_post("sendMessage", {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    })


# ---------- AI Call: OpenRouter with Qwen3 ----------
def ask_openrouter(prompt: str) -> str:
    """Call OpenRouter API using Qwen3 model"""
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": os.getenv("RENDER_EXTERNAL_URL", "https://huggingface.co"),
            "X-Title": "Mybuddy",
        }
        
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 500,
            "temperature": 0.7,
        }
        rint(f"🤖 Calling OpenRouter model: {MODEL}")
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if r.status_code != 200:
            print(f"⚠️ OpenRouter {r.status_code}: {r.text[:300]}")
            return "Sorry, the AI service is busy. Please try again in a moment."
        
        data = r.json()
        
        if "choices" not in data or not data["choices"]:
            print(f"⚠️ No choices in response: {data}")
            return "AI service returned an empty response."
        
        return data["choices"][0]["message"]["content"].strip()
        
    except requests.exceptions.Timeout:
        print("❌ OpenRouter timeout")
        return "The AI is taking too long. Please try again."
    except requests.exceptions.RequestException as e:
        print(f"❌ OpenRouter request error: {e}")
        return "Network error connecting to AI service."
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")
        return "AI is temporarily unavailable."


# ---------- Supabase Memory ----------
def save_memory(user_text: str, bot_reply: str):
    """Save conversation to Supabase"""
    try:
        url = f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }
        data = {"user_message": user_text, "bot_reply": bot_reply}
        requests.post(url, headers=headers, json=data, timeout=10)
    except Exception as e:
        print(f"⚠️ Supabase error (non-critical): {e}")


# ---------- Message Handler ----------
def handle_message(update: Update):
    """Process incoming Telegram messages"""
    if not update.message or not update.message.text:
        return
    
    user_text = update.message.text.strip()
    chat_id = update.message.chat.id
    
    print(f"📥 [{chat_id}] {user_text}")
    
    # Get AI response
    ai_reply = ask_openrouter(user_text)
    
    # Send reply to user
    result = send_message(chat_id, ai_reply)
    
    if result and result.get("ok"):
        print(f"✅ Replied to {chat_id}")
    else:
        print(f"⚠️ Failed to send reply: {result}")
    
    # Save to memory (fire-and-forget)
    save_memory(user_text, ai_reply)


# ---------- FastAPI Endpoints ----------
@app.get("/")
def root():
    """Health check root endpoint"""
    return {
        "status": "✅ Sawan Buddy is running!",
        "model": MODEL,
        "webhook": "/webhook",
        "docs": "/docs"
    }


@app.post("/webhook")
async def webhook(req: Request):
    """Telegram webhook endpoint"""
    try:
        data = await req.json()
        update = Update.de_json(data, None)
        
        if update and update.message and update.message.text:
            handle_message(update)
        
        return {"ok": True}
    
    except json.JSONDecodeError:
        print("⚠️ Invalid JSON in webhook")
        return {"ok": False, "error": "invalid_json"}
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return {"ok": False, "error": str(e)}


@app.get("/health")
def health_check():
    """Detailed health check with connectivity tests"""
    results = {"status": "healthy", "services": {}}
    
    # Test Telegram API
    try:
        r = requests.get(f"{TG_API}/getMe", timeout=10)
        results["services"]["telegram"] = "OK" if r.status_code == 200 else f"ERROR {r.status_code}"
    except Exception as e:
        results["services"]["telegram"] = f"BLOCKED: {type(e).__name__}"
    
    # Test OpenRouter API
    try:
        r = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
            timeout=10
        )
        results["services"]["openrouter"] = "OK" if r.status_code == 200 else f"ERROR {r.status_code}"
    except Exception as e:
        results["services"]["openrouter"] = f"BLOCKED: {type(e).__name__}"
    
    # Test Supabase
    try:
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}?limit=1",
            headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"},
            timeout=10
        )
        results["services"]["supabase"] = "OK" if r.status_code in [200, 206] else f"ERROR {r.status_code}"
    except Exception as e:
        results["services"]["supabase"] = f"BLOCKED: {type(e).__name__}"
    
    return results


@app.get("/debug")
def debug_info():
    """Debug endpoint for troubleshooting"""
    return {
        "env_vars": {
            "TELEGRAM_BOT_TOKEN": "✓ set" if TELEGRAM_BOT_TOKEN else "✗ missing",
            "OPENROUTER_API_KEY": "✓ set" if OPENROUTER_API_KEY else "✗ missing",
            "SUPABASE_URL": "✓ set" if SUPABASE_URL else "✗ missing",
            "SUPABASE_KEY": "✓ set" if SUPABASE_KEY else "✗ missing",
        },
        "config": {
            "MODEL": MODEL,
            "SYSTEM_PROMPT_LENGTH": len(SYSTEM_PROMPT),
        },
        "render_url": os.getenv("RENDER_EXTERNAL_URL", "not set"),
    }
