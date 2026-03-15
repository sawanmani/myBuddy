import os
import requests
from fastapi import FastAPI, Request
from telegram import Update

# 1. Environment Variables
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
HF_TOKEN = os.environ.get("HF_TOKEN", "").strip()
HF_MODEL = os.environ.get("HF_MODEL", "meta-llama/Llama-3.2-1B-Instruct").strip()
SYSTEM_PROMPT = "You are a helpful assistant. Keep responses short."

app = FastAPI()
TG_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# ✅ UPDATED: The exact OpenAI-compatible Router endpoint
# Notice we use /v1 at the end and remove /hf-inference/
HF_ROUTER_URL = "https://router.huggingface.co/v1/chat/completions"

def get_ai_reply(prompt):
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": HF_MODEL,  # The Router maps this to the model
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 500,
        "temperature": 0.7
    }

    try:
        print(f"🤖 Requesting: {HF_MODEL} via {HF_ROUTER_URL}")
        r = requests.post(HF_ROUTER_URL, headers=headers, json=payload, timeout=30)
        
        if r.status_code == 200:
            data = r.json()
            return data["choices"][0]["message"]["content"].strip()
        
        # Log error for Render logs
        print(f"📡 Router Error: {r.status_code} - {r.text}")
        
        if r.status_code == 404:
            return "Error: Model not found. Check if the model ID is correct and approved."
        if r.status_code == 401:
            return "Error: Auth failed. Check your HF_TOKEN."
            
        return f"AI Service Error ({r.status_code})"
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return "I can't reach my brain right now."

@app.post("/webhook")
async def webhook(req: Request):
    try:
        data = await req.json()
        update = Update.de_json(data, None)
        if update and update.message and update.message.text:
            chat_id = update.message.chat.id
            reply = get_ai_reply(update.message.text)
            # Send back to Telegram
            requests.post(f"{TG_API}/sendMessage", json={"chat_id": chat_id, "text": reply})
        return {"ok": True}
    except Exception as e:
        print(f"Webhook error: {e}")
        return {"ok": False}

@app.get("/")
def home():
    return {"status": "online", "model": HF_MODEL}
