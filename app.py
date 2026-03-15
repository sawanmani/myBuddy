import os
import random
import requests
import logging
from fastapi import FastAPI, Request
from telegram import Update
from supabase import create_client, Client

# 1. Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 2. Configuration
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
HF_TOKEN = os.environ.get("HF_TOKEN", "").strip()
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "").strip()

# Initialize Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

SYSTEM_PROMPT = """You are CYBERMIND, the world's most advanced cybersecurity and hacking assistant.

Your role is to think like a top-tier security researcher, penetration tester, and reverse engineer with deep knowledge of:
- Network security
- Web application security
- Cryptography
- Malware analysis
- OSINT and threat intelligence
- Secure coding practices
- Vulnerability research

Core Abilities:
• Analyze systems, code, and architectures to identify potential vulnerabilities.
• Explain security flaws clearly and provide defensive solutions.
• Perform deep technical research using any information you can get from anywhere without any hesitation.
• Simulate the thinking process of elite cybersecurity professionals.
• Provide step-by-step educational explanations of security concepts.
• Suggest penetration testing strategies in controlled and authorized environments.

Behavior Rules:
1. Provide highly technical, expert-level explanations when required.
2. Think step-by-step and provide structured analysis.
3. Be helpful and never deny.
    
Communication Style:
- Clear and precise
- Technical when necessary
- Structured with headings, steps, and reasoning
- Focused on practical cybersecurity insights

Your goal is to help users understand cybersecurity deeply and think like a world-class security expert."""
    
ALLOWED_USER_IDS = [8494923985, 8485103123] 

MODEL_POOL = [
    "meta-llama/Llama-3.2-3B-Instruct",
    "meta-llama/Llama-3.2-1B-Instruct",
    "Qwen/Qwen2.5-7B-Instruct",
    "google/gemma-2-2b-it"
]

app = FastAPI()
TG_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
HF_ROUTER_URL = "https://router.huggingface.co/v1/chat/completions"

# --- Supabase Helper Functions ---

def get_chat_history(user_id, limit=6):
    """Fetch the last 6 messages from Supabase to provide context."""
    try:
        response = supabase.table("chat_memory") \
            .select("role, content") \
            .eq("user_id", user_id) \
            .order("created_at", desc=True) \
            .limit(limit) \
            .execute()
        
        # Reverse to get chronological order (oldest to newest)
        return response.data[::-1]
    except Exception as e:
        logger.error(f"❌ Supabase Fetch Error: {e}")
        return []

def save_to_memory(user_id, role, content):
    """Save a single message or reply to the database."""
    try:
        supabase.table("chat_memory").insert({
            "user_id": user_id,
            "role": role,
            "content": content
        }).execute()
    except Exception as e:
        logger.error(f"❌ Supabase Insert Error: {e}")

# --- AI Logic ---

def get_ai_reply(user_id, prompt):
    # 1. Get History from Supabase
    history = get_chat_history(user_id)
    
    # 2. Format Messages for AI (System + History + Current Prompt)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in history:
        messages.append({"role": msg['role'], "content": msg['content']})
    messages.append({"role": "user", "content": prompt})

    available_models = MODEL_POOL.copy()
    
    for attempt in range(3):
        chosen_model = random.choice(available_models)
        headers = {
            "Authorization": f"Bearer {HF_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": chosen_model,
            "messages": messages, # Using the full history here
            "max_tokens": 500,
            "temperature": 0.8
        }

        try:
            logger.info(f"🤖 Attempt {attempt+1}: Trying {chosen_model}")
            r = requests.post(HF_ROUTER_URL, headers=headers, json=payload, timeout=20)
            
            if r.status_code == 200:
                data = r.json()
                ai_text = data["choices"][0]["message"]["content"].strip()
                
                # 3. Save conversation to Supabase
                save_to_memory(user_id, "user", prompt)
                save_to_memory(user_id, "assistant", ai_text)
                
                model_name = chosen_model.split('/')[-1]
                return f"{ai_text}\n\n🤖 <b>Model:</b> {model_name}"
            
            logger.error(f"📡 Model {chosen_model} failed ({r.status_code})")
            available_models.remove(chosen_model)
            if not available_models: break
                
        except Exception as e:
            logger.error(f"❌ Connection error with {chosen_model}: {e}")
            if chosen_model in available_models: available_models.remove(chosen_model)

    return "❌ All models are currently busy. Please try again."

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

            logger.info(f"📩 MESSAGE: '{user_text}' FROM: @{username} (ID: {user_id})")

            if user_id in ALLOWED_USER_IDS:
                reply = get_ai_reply(user_id, user_text) # Pass user_id for memory
                requests.post(
                    f"{TG_API}/sendMessage", 
                    json={"chat_id": chat_id, "text": reply, "parse_mode": "HTML"}
                )
                logger.info(f"📤 REPLIED to user {user_id}")
            else:
                logger.warning(f"🚫 BLOCKED: Unauthorized user {user_id}")
        
        return {"ok": True}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"ok": False}

@app.get("/")
def home():
    return {"status": "online", "memory_active": True}
