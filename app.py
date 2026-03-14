import requests
from fastapi import FastAPI, Request
from telegram import Update
import os

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


# ---------- Simple Telegram API Calls ----------
def tg_post(method: str, data: dict):
    url = f"{TG_API}/{method}"
    try:
        r = requests.post(url, json=data, timeout=15)
        return r.json()
    except Exception as e:
        print(f"Telegram error: {e}")
        return None


def send_message(chat_id: int, text: str):
    return tg_post("sendMessage", {"chat_id": chat_id, "text": text, "parse_mode": "HTML"})


# ---------- AI Call (OpenRouter Only) ----------
def ask_openrouter(prompt):
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://huggingface.co",
            "X-Title": "Sawan Buddy",
        }
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        }
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print("OpenRouter ERROR:", e)
        return "Sorry, I'm having trouble right now. Please try again."


# ---------- Supabase Memory ----------
def save_memory(user_text, bot_reply):
    try:
        url = f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }
        requests.post(url, headers=headers, json={"user_message": user_text, "bot_reply": bot_reply}, timeout=10)
    except Exception as e:
        print("Supabase error:", e)


# ---------- Message Handler ----------
def handle_message(update: Update):
    if not update.message or not update.message.text:
        return
    user_text = update.message.text
    chat_id = update.message.chat.id
    print(f"📥 {chat_id}: {user_text}")
    
    ai_reply = ask_openrouter(user_text)
    result = send_message(chat_id, ai_reply)
    
    if result and result.get("ok"):
        print(f"✅ Replied to {chat_id}")
    save_memory(user_text, ai_reply)


# ---------- Endpoints ----------
@app.get("/")
def root():
    return {"status": "✅ Sawan Buddy running", "webhook": "/webhook"}

@app.post("/webhook")
async def webhook(req: Request):
    try:
        data = await req.json()
        update = Update.de_json(data, None)
        if update and update.message and update.message.text:
            handle_message(update)
        return {"ok": True}
    except Exception as e:
        print(f"Webhook error: {e}")
        return {"ok": False}

@app.get("/health")
def health():
    # Simple connectivity tests
    tests = {}
    for name, url in [("telegram", f"{TG_API}/getMe"), ("openrouter", "https://openrouter.ai/api/v1/models")]:
        try:
            r = requests.get(url, headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"} if "openrouter" in url else {}, timeout=10)
            tests[name] = f"OK ({r.status_code})"
        except Exception as e:
            tests[name] = f"BLOCKED: {type(e).__name__}"
    return {"status": "healthy", "connectivity": tests}