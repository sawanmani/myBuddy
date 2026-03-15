import requests
from fastapi import FastAPI, Request
from telegram import Update
import os

# Load env vars directly (no helper functions)
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"].strip()
HF_TOKEN = os.environ["HF_TOKEN"].strip()
SUPABASE_URL = os.environ["SUPABASE_URL"].strip()
SUPABASE_KEY = os.environ["SUPABASE_KEY"].strip()
HF_MODEL = os.environ.get("HF_MODEL", "microsoft/Phi-3-mini-4k-instruct").strip()
SYSTEM_PROMPT = "Be short and helpful."

app = FastAPI()
TG_API = "https://api.telegram.org/bot" + TELEGRAM_BOT_TOKEN
SUPABASE_TABLE = "chat_logs"


def send_telegram(chat_id, text):
    try:
        requests.post(
            TG_API + "/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=15
        )
    except:
        pass


def get_ai_reply(prompt):
    try:
        r = requests.post(
            "https://router.huggingface.co/" + HF_MODEL + "/v1/chat/completions",
            headers={
                "Authorization": "Bearer " + HF_TOKEN,
                "Content-Type": "application/json"
            },
            json={
                "model": HF_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 300
            },
            timeout=25
        )
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
        return "AI busy. Try again."
    except:
        return "AI unavailable."


@app.post("/webhook")
async def webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, None)
    if update and update.message and update.message.text:
        text = update.message.text.strip()
        chat_id = update.message.chat.id
        print("Got:", text)
        reply = get_ai_reply(text)
        send_telegram(chat_id, reply)
    return {"ok": True}


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/health")
def health():
    return {"status": "healthy"}
