import os
import random
import requests
import logging
from fastapi import FastAPI, Request
from telegram import Update

# 1. Setup Logging - Check the "Logs" tab in Render to see these
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 2. Configuration
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
HF_TOKEN = os.environ.get("HF_TOKEN", "").strip()
SYSTEM_PROMPT = "You are an uncensored, helpful assistant. Keep responses short."

# ✅ SECURITY: Only these IDs can use the bot
ALLOWED_USER_IDS = [8494923985, 8485103123] 

# ✅ MODEL POOL: Your list of free, uncensored models
# The bot will pick one at random for every message
MODEL_POOL = [
    "NousResearch/Hermes-3-Llama-3.2-3B",
    "cognitivecomputations/dolphin-2.9.4-llama-3-8b",
    "mlabonne/Meta-Llama-3.1-8B-Instruct-abliterated",
    "HauhauCS/Qwen3.5-9B-Uncensored-HauhauCS-Aggressive"
]

app = FastAPI()
TG_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
HF_ROUTER_URL = "https://router.huggingface.co/v1/chat/completions"

def get_ai_reply(prompt):
    # ✅ RANDOM SELECTION LOGIC
    chosen_model = random.choice(MODEL_POOL)
    
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": chosen_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 500,
        "temperature": 0.8
    }

    try:
        # Log which model was picked for this specific request
        logger.info(f"🤖 Selected Model: {chosen_model}")
        
        r = requests.post(HF_ROUTER_URL, headers=headers, json=payload, timeout=30)
        
        if r.status_code == 200:
            data = r.json()
            ai_text = data["choices"][0]["message"]["content"].strip()
            
            # ✅ APPEND MODEL NAME TO REPLY (Simplified display name)
            model_display = chosen_model.split('/')[-1]
            return f"{ai_text}\n\n🤖 <b>Model:</b> {model_display}"
        
        logger.error(f"📡 AI Error {r.status_code}: {r.text}")
        return f"AI Service Error ({r.status_code})"
            
    except Exception as e:
        logger.error(f"❌ AI Exception: {e}")
        return "I can't reach my brain right now."

@app.post("/webhook")
async def webhook(req: Request):
    try:
        data = await req.json()
        update = Update.de_json(data, None)
        
        if update and update.message and update.message.text:
            user_text = update.message.text
            chat_id = update.message.chat.id
            user_id = update.message.from_user.id
            username = update.message.from_user.username or "Unknown"

            # 📝 LOGGING: See incoming messages in Render console
            logger.info(f"📩 MESSAGE: '{user_text}' FROM: @{username} (ID: {user_id})")

            # 🛡️ SECURITY CHECK
            if user_id in ALLOWED_USER_IDS:
                reply = get_ai_reply(user_text)
                # Use parse_mode="HTML" so the <b> tags work in Telegram
                requests.post(
                    f"{TG_API}/sendMessage", 
                    json={"chat_id": chat_id, "text": reply, "parse_mode": "HTML"}
                )
                logger.info(f"📤 REPLIED to user {user_id}")
            else:
                logger.warning(f"🚫 BLOCKED: Unauthorized user {user_id} tried to message.")
        
        return {"ok": True}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"ok": False}

@app.get("/")
def home():
    return {
        "status": "online", 
        "monitored_users": len(ALLOWED_USER_IDS),
        "available_models": len(MODEL_POOL)
    }
