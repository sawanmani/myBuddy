import os
import requests
from fastapi import FastAPI, Request
from telegram import Update

# 1. Load env vars
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
HF_TOKEN = os.environ.get("HF_TOKEN", "").strip()
HF_MODEL = os.environ.get("HF_MODEL", "meta-llama/Llama-3.2-1B-Instruct").strip()
SYSTEM_PROMPT = "Be short and helpful."

app = FastAPI()
TG_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# 2. ✅ FIXED: The modern 2026 Router URL
# We use the generic chat completions endpoint and specify the model in the payload
HF_ROUTER_URL = "https://router.huggingface.co/hf-inference/v1/chat/completions"

def get_ai_reply(prompt):
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # 3. The Router needs the model name inside the JSON body
    payload = {
        "model": HF_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 300,
        "stream": False
    }

    try:
        print(f"🤖 Calling HF Router for: {HF_MODEL}")
        r = requests.post(HF_ROUTER_URL, headers=headers, json=payload, timeout=30)
        
        if r.status_code == 200:
            data = r.json()
            return data["choices"][0]["message"]["content"].strip()
        
        # Specific error handling for the new router
        print(f"📡 Router Error {r.status_code}: {r.text}")
        if r.status_code == 401: return "Auth Error: Check HF_TOKEN."
        if r.status_code == 404: return "Model not found on Router."
        if r.status_code == 429: return "Rate limited. Wait a moment."
        if r.status_code == 503: return "Model is loading. Try again in 30s."
        
        return f"AI Error: {r.status_code}"
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return "Connection to AI failed."

@app.post("/webhook")
async def webhook(req: Request):
    try:
        data = await req.json()
        update = Update.de_json(data, None)
        
        if update and update.message and update.message.text:
            chat_id = update.message.chat.id
            user_text = update.message.text
            
            # Get AI response and send back to Telegram
            reply = get_ai_reply(user_text)
            requests.post(f"{TG_API}/sendMessage", 
                         json={"chat_id": chat_id, "text": reply})
            
        return {"ok": True}
    except Exception as e:
        print(f"Webhook Error: {e}")
        return {"ok": False}

@app.get("/")
def home():
    return {"status": "online", "model": HF_MODEL}
