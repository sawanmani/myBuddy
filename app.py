import requests
from fastapi import FastAPI, Request
from telegram import Update
import os

# Load env vars
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
HF_TOKEN = os.environ.get("HF_TOKEN", "").strip()
HF_MODEL = os.environ.get("HF_MODEL", "meta-llama/Llama-3.2-1B-Instruct").strip()
SYSTEM_PROMPT = "You are a helpful assistant. Keep responses concise."

app = FastAPI()
TG_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# FIX: Standard Hugging Face Inference API URL
# Pattern: https://api-inference.huggingface.co/models/<MODEL_ID>
HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}/v1/chat/completions"

print(f"🚀 Starting with model: {HF_MODEL}")

def send_telegram(chat_id, text):
    try:
        r = requests.post(
            f"{TG_API}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=15
        )
        return r.status_code == 200
    except Exception as e:
        print(f"❌ Telegram exception: {e}")
        return False

def get_ai_reply(prompt):
    print(f"🤖 Calling HF API: {HF_API_URL}")
    
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
        "max_tokens": 500
    }

    try:
        r = requests.post(HF_API_URL, headers=headers, json=payload, timeout=30)
        
        if r.status_code == 200:
            data = r.json()
            return data["choices"][0]["message"]["content"].strip()
        
        # Handle specific HF statuses
        error_map = {
            401: "AI Auth Error: Check your HF_TOKEN.",
            404: f"Model '{HF_MODEL}' not found. Check the model ID.",
            429: "AI is rate-limited. Please try again in a minute.",
            503: "AI is currently loading/booting up. Try again in 30s."
        }
        
        error_msg = error_map.get(r.status_code, f"AI Error ({r.status_code})")
        print(f"📡 HF Response Error: {r.status_code} - {r.text}")
        return error_msg
            
    except Exception as e:
        print(f"❌ HF exception: {e}")
        return "Sorry, I'm having trouble thinking right now."

@app.post("/webhook")
async def webhook(req: Request):
    try:
        data = await req.json()
        update = Update.de_json(data, None)
        
        if update and update.message and update.message.text:
            user_text = update.message.text
            chat_id = update.message.chat.id
            
            # Get AI response
            reply = get_ai_reply(user_text)
            send_telegram(chat_id, reply)
            
        return {"ok": True}
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return {"ok": False}

@app.get("/")
def root():
    return {"status": "online", "model": HF_MODEL}

@app.get("/health")
def health():
    return {"status": "healthy"}
