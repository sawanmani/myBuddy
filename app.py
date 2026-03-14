import requests
from fastapi import FastAPI, Request
from telegram import Update
import os

from config import (
    TELEGRAM_BOT_TOKEN,
    HF_TOKEN,
    HF_MODEL,
    SYSTEM_PROMPT,
    SUPABASE_URL,
    SUPABASE_KEY
)

app = FastAPI()
SUPABASE_TABLE = "chat_logs"
TG_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def tg_post(method: str,  dict):
    url = f"{TG_API}/{method}"
    try:
        r = requests.post(url, json=data, timeout=15)
        return r.json()
    except:
        return None


def send_message(chat_id: int, text: str):
    return tg_post("sendMessage", {"chat_id": chat_id, "text": text, "parse_mode": "HTML"})


def ask_huggingface(prompt: str) -> str:
    try:
        url = f"https://router.huggingface.co/{HF_MODEL}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {HF_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": HF_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 500,
            "temperature": 0.7
        }
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        if r.status_code == 200:
            data = r.json()
            if data.get("choices") and data["choices"][0].get("message"):
                return data["choices"][0]["message"]["content"].strip()
        if r.status_code == 401:
            return "AI auth error."
        elif r.status_code == 404:
            return "Model not found."
        elif r.status_code == 429:
            return "AI is busy. Wait 30s."
        elif r.status_code == 503:
            return "AI loading. Try again."
        print(f"HF Error {r.status_code}: {r.text[:200]}")
        return "AI unavailable."
    except Exception as e:
        print(f"HF Exception: {e}")
        return "AI temporarily unavailable."


def save_memory(user_text: str, bot_reply: str):
    try:
        url = f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}"
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json", "Prefer": "return=minimal"}
        requests.post(url, headers=headers, json={"user_message": user_text, "bot_reply": bot_reply}, timeout=10)
    except:
        pass


def handle_message(update: Update):
    if not update.message or not update.message.text:
        return
    user_text = update.message.text.strip()
    chat_id = update.message.chat.id
    print(f"Message: {user_text}")
    ai_reply = ask_huggingface(user_text)
    send_message(chat_id, ai_reply)
    save_memory(user_text, ai_reply)


@app.get("/")
def root():
    return {"status": "running", "model": HF_MODEL}


@app.post("/webhook")
async def webhook(req: Request):
    try:
        data = await req.json()
        update = Update.de_json(data, None)
        if update and update.message and update.message.text:
            handle_message(update)
        return {"ok": True}
    except:
        return {"ok": False}


@app.get("/health")
def health():
    return {"status": "healthy"}
