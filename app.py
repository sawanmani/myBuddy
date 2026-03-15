# --- CONFIGURATION ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
HF_TOKEN = os.environ.get("HF_TOKEN", "").strip()

# ✅ ALLOW MULTIPLE IDs: Put all allowed IDs in this list
ALLOWED_USER_IDS = [8494923985, 987654321] 

# ... (rest of your AI functions) ...

@app.post("/webhook")
async def webhook(req: Request):
    try:
        data = await req.json()
        update = Update.de_json(data, None)
        
        if update.message and update.message.text:
            chat_id = update.message.chat.id
            user_id = update.message.from_user.id
            
            # ✅ CHECK IF USER IS IN THE ALLOWED LIST
            if user_id in ALLOWED_USER_IDS:
                reply = get_ai_reply(update.message.text)
                requests.post(f"{TG_API}/sendMessage", json={"chat_id": chat_id, "text": reply})
            else:
                # Optional: log the attempt in your Render console
                print(f"🚫 Unauthorized access attempt by ID: {user_id}")
                # You can choose to send a message or stay silent
                # requests.post(f"{TG_API}/sendMessage", json={"chat_id": chat_id, "text": "Private Bot."})
        
        return {"ok": True}
    except Exception as e:
        print(f"Error: {e}")
        return {"ok": False}
