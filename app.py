import requests
from fastapi import FastAPI, Request
from telegram import Update
import os

# Load env vars directly
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"].strip()
HF_TOKEN = os.environ["HF_TOKEN"].strip()
SUPABASE_URL = os.environ["SUPABASE_URL"].strip()
SUPABASE_KEY = os.environ["SUPABASE_KEY"].strip()
HF_MODEL = os.environ.get("HF_MODEL", "microsoft/Phi-3-mini-4k-instruct").strip()
SYSTEM_PROMPT = "Be short and helpful."

app = FastAPI()
TG_API = "https://api.telegram.org/bot" + TELEGRAM_BOT_TOKEN
SUPABASE_TABLE = "chat_logs"

print(f"🚀 Starting with model: {HF_MODEL}")


def send_telegram(chat_id, text):
    try:
        r = requests.post(
            TG_API + "/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=15
        )
        if r.status_code != 200:
            print(f"❌ Telegram send failed: {r.status_code}")
    except Exception as e:
        print(f"❌ Telegram exception: {e}")


def get_ai_reply(prompt):
    url = "https://router.huggingface.co/" + HF_MODEL + "/v1/chat/completions"
    print(f"🤖 Calling HF: {url}")
    
    try:
        r = requests.post(
            url,
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
        
        print(f"📡 HF Response: {r.status_code} - {r.text[:200]}")
        
        if r.status_code == 200:
            data = r.json()
            if data.get("choices") and data["choices"][0].get("message"):
                return data["choices"][0]["message"]["content"].strip()
            print("⚠️ No choices in response")
            return "AI returned empty."
        
        # Specific error messages
        if r.status_code == 401:
            print("❌ HF 401: Invalid token")
            return "AI auth error."
        elif r.status_code == 404:
            print(f"❌ HF 404: Model not found: {HF_MODEL}")
            return "Model not available."
        elif r.status_code == 429:
            print("⚠️ HF 429: Rate limited")
            return "AI busy. Wait 30s."
        elif r.status_code == 503:
            print("⏳ HF 503: Model loading")
            return "AI loading. Try again."
        else:
            return f"AI error {r.status_code}."
            
    except requests.exceptions.Timeout:
        print("⏱️ HF timeout")
        return "AI request timed out."
    except Exception as e:
        print(f"❌ HF exception: {type(e).__name__}: {e}")
        return "AI unavailable."


@app.post("/webhook")
async def webhook(req: Request):
    try:
        data = await req.json()
        update = Update.de_json(data, None)
        if update and update.message and update.message.text:
            text = update.message.text.strip()
            chat_id = update.message.chat.id
            print(f"📥 Got: {text}")
            reply = get_ai_reply(text)
            print(f"📤 Reply: {reply[:50]}...")
            send_telegram(chat_id, reply)
        return {"ok": True}
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return {"ok": False}


@app.get("/")
def root():
    return {"status": "ok", "model": HF_MODEL}


@app.get("/health")
def health():
    return {"status": "healthy"}
