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


def ask_openrouter(prompt: str) -> str:
    models = [
        "google/gemma-2-9b-it:free",
        "mistralai/mistral-7b-instruct:free",
        "meta-llama/llama-3.2-3b-instruct:free",
        "venice/uncensored:free",
    ]
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": os.getenv("RENDER_EXTERNAL_URL", "https://huggingface.co").strip(),
        "X-Title": "Mybuddy",
    }
    
    for model in models:
        try:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 500,
                "temperature": 0.7,
            }
            r = requests.post(url, headers=headers, json=payload, timeout=25)
            if r.status_code == 200:
                data = r.json()
                if data.get("choices"):
                    return data["choices"][0]["message"]["content"].strip()
        except:
            continue
    return "AI is busy. Please try again."


def save_memory(user_text: str, bot_reply: str):
    try:
        url = f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }
        requests.post(url, headers=headers, json={"user_message": user_text, "bot_reply": bot_reply}, timeout=10)
    except:
        pass


def handle_message(update: Update):
    if not update.message or not update.message.text:
        return
    user_text = update.message.text.strip()
    chat_id = update.message.chat.id
    print(f"Message: {user_text}")
    ai_reply = ask_openrouter(user_text)
    send_message(chat_id, ai_reply)
    save_memory(user_text, ai_reply)


@app.get("/")
def root():
    return {"status": "running", "model": MODEL}


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
    return {"status": "healthy"}
