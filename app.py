import os
import requests
import logging # Added for application logs
from fastapi import FastAPI, Request
from telegram import Update

# 1. Setup Logging - This will show up in your Render "Logs" tab
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 2. Configuration
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
HF_TOKEN = os.environ.get("HF_TOKEN", "").strip()
HF_MODEL = os.environ.get("HF_MODEL", "meta-llama/Llama-3.2-1B-Instruct").strip()
SYSTEM_PROMPT = "You are a helpful assistant. Keep responses short."

# ✅ Add your IDs here. Example: [8494923985, 123456789]
ALLOWED_USER_IDS = [8494923985,8485103123] 

app = FastAPI()
TG_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
HF_ROUTER_URL = "https://router.huggingface.co/v1/chat/completions"

def get_ai_reply(prompt):
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

    try:
        r = requests.post(HF_ROUTER_URL, headers=headers, json=payload, timeout=30)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
        
        logger.error(f"📡 AI Error {r.status_code}: {r.text}")
        return f"AI Error ({r.status_code})"
    except Exception as e:
        logger.error(f"❌ AI Exception: {e}")
        return "Connection failed."

@app.post("/webhook")
async def webhook(req: Request):
    try:
        data = await req.json()
        update = Update.de_json(data, None)
        
        if update and update.message and update.message.text:
            user_text = update.message.text
            chat_id = update.message.chat.id
            user_id = update.message.from_user.id # This is the sender's unique ID
            username = update.message.from_user.username or "NoUsername"

            # 📝 LOGGING: This will show in Render
            logger.info(f"📩 MESSAGE: '{user_text}' FROM: {username} (ID: {user_id})")

            # 🛡️ SECURITY CHECK: Only reply if the ID is in our list
            if user_id in ALLOWED_USER_IDS:
                reply = get_ai_reply(user_text)
                requests.post(f"{TG_API}/sendMessage", json={"chat_id": chat_id, "text": reply})
                logger.info(f"📤 REPLIED to {user_id}")
            else:
                logger.warning(f"🚫 BLOCKED: Unauthorized user {user_id} tried to use the bot.")
                # Optional: Send a one-time "Access Denied" message
                # requests.post(f"{TG_API}/sendMessage", json={"chat_id": chat_id, "text": "Private Bot."})

        return {"ok": True}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"ok": False}

@app.get("/")
def home():
    return {"status": "online", "allowed_count": len(ALLOWED_USER_IDS)}
