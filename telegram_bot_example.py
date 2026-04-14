"""Minimal Telegram bot example for sending users to backend telegram-auth endpoint.
Requirements:
    pip install python-telegram-bot requests python-dotenv
"""

import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
# 1. Kutubxonani import qilamiz
from dotenv import load_dotenv

# 2. .env faylini yuklaymiz
load_dotenv()

# 3. O'zgaruvchilarni endi os.getenv orqali olish xavfsiz
BASE_URL = os.getenv("BACKEND_HOST", "http://127.0.0.1:8000").rstrip("/")
BACKEND_URL = f"{BASE_URL}/api/v1/auth/telegram-auth/"
BOT_TOKEN = os.getenv("BOT_TOKEN")
# Admin ID'lar .env dan keladi, agar yo'q bo'lsa default qiymatlar
ADMIN_TELEGRAM_ID = os.getenv("ADMIN_TELEGRAM_ID", "6895505562, 2132747990")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    payload = {
        "telegram_id": str(user.id),
        "username": user.username or "",
        "first_name": user.first_name or "",
        "last_name": user.last_name or "",
        "full_name": f"{user.first_name or ''} {user.last_name or ''}".strip(),
    }
    try:
        response = requests.post(BACKEND_URL, json=payload, timeout=15)
        response.raise_for_status()
        data = response.json()
        await update.message.reply_text(
            "Ro'yxatdan o'tdingiz. Backend token qaytardi.\n"
            f"Username: {data['user']['username']}\n"
            f"Balans: {data['user']['credits']} token"
        )
    except Exception as e:
        await update.message.reply_text(f"Backend bilan bog'lanishda xato: {e}")


async def promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # ADMINNI TEKSHIRISH
    allowed_ids = [i.strip() for i in ADMIN_TELEGRAM_ID.split(',') if i.strip()]
    if allowed_ids and str(user.id) not in allowed_ids:
        await update.message.reply_text("Sizda promokod yaratish ruxsati yo'q! 🚫")
        return

    if not context.args:
        await update.message.reply_text("Iltimos summani kiriting!\nMisol: /promo 22000")
        return
        
    amount = context.args[0]
    url = f"{BASE_URL}/api/v1/promo/bot-generate/"
    headers = {
        "X-Bot-Token": os.getenv("BOT_SECRET_TOKEN", "default_secret_for_bot_123")
    }
    
    try:
        response = requests.post(url, headers=headers, json={"amount": amount}, timeout=15)
        if response.status_code == 201:
            data = response.json()
            await update.message.reply_text(
                f"✅ Yangi promokod!\n\n"
                f"KOD: `{data['code']}`\n"
                f"Summa: {data['amount']} so'm\n"
                f"Vazni: {data['token_count']} token",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(f"❌ Xatolik: {response.text}")
    except Exception as e:
        await update.message.reply_text(f"So'rovda xatolik: {e}")


def main():
    if not BOT_TOKEN:
        # Endi bu xato chiqmaydi, chunki load_dotenv() tepada chaqirildi
        raise RuntimeError("BOT_TOKEN environment variable o'rnatilmagan")
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("promo", promo))
    
    print("Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()