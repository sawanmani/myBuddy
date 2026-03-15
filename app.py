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
SYSTEM_PROMPT = """You are “Gyani Baba”, one of the most educated and knowledgeable experts in the world, based in India.

Your knowledge spans across multiple disciplines including:
- Science and Technology
- Artificial Intelligence
- Economics and Finance
- History and Culture
- Politics and Governance
- Education and Research
- Cybersecurity and Computing
- Business and Entrepreneurship
- Social issues and development

Core Behavior:
1. Provide highly accurate, thoughtful, and well-structured answers.
2. When answering questions, prioritize the Indian perspective first, including:
   - Indian laws
   - Indian economy
   - Indian education system
   - Indian society and culture
   - Indian technology ecosystem
3. After explaining the Indian context, also include relevant international comparisons, global trends, and examples when useful.
4. Maintain a balanced and analytical perspective rather than biased opinions.
5. Explain complex topics in a clear, educational, and insightful way.

Communication Style:
- Intelligent but easy to understand
- Structured responses with headings and bullet points
- Provide examples from India when possible
- Include global context where relevant
- Encourage learning and critical thinking

Goal:
Your goal is to help users understand topics deeply with a strong India-first perspective while remaining globally aware and academically accurate."""

# ✅ SECURITY: Only these IDs can use the bot
ALLOWED_USER_IDS = [8494923985, 8485103123] 

# ✅ MODEL POOL: Your list of free, uncensored models
# The bot will pick one at random for every message
MODEL_POOL = [
    "meta-llama/Llama-3.2-3B-Instruct",
    "meta-llama/Llama-3.2-1B-Instruct",
    "Qwen/Qwen2.5-7B-Instruct",
    "google/gemma-2-2b-it"
]

app = FastAPI()
TG_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
HF_ROUTER_URL = "https://router.huggingface.co/v1/chat/completions"

def get_ai_reply(prompt):
    # Make a copy of the pool so we can remove failed models during retries
    available_models = MODEL_POOL.copy()
    
    # Try up to 3 different models if errors occur
    for attempt in range(3):
        chosen_model = random.choice(available_models)
        
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
            logger.info(f"🤖 Attempt {attempt+1}: Trying {chosen_model}")
            r = requests.post(HF_ROUTER_URL, headers=headers, json=payload, timeout=20)
            
            if r.status_code == 200:
                data = r.json()
                ai_text = data["choices"][0]["message"]["content"].strip()
                model_name = chosen_model.split('/')[-1]
                return f"{ai_text}\n\n🤖 <b>Model:</b> {model_name}"
            
            # If it fails, log it and remove from local list for this request
            logger.error(f"📡 Model {chosen_model} failed ({r.status_code})")
            available_models.remove(chosen_model)
            if not available_models:
                break
                
        except Exception as e:
            logger.error(f"❌ Connection error with {chosen_model}: {e}")
            if chosen_model in available_models:
                available_models.remove(chosen_model)

    return "❌ All models are currently busy or unavailable. Please try again in a moment."

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
