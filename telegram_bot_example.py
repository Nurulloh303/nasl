"""Minimal Telegram bot example for sending users to backend telegram-auth endpoint."""

import os
import requests
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv

# .env faylini yuklaymiz
load_dotenv()

BASE_URL = os.getenv("BACKEND_HOST", "http://127.0.0.1:8000").rstrip("/")
BACKEND_URL = f"{BASE_URL}/api/v1/auth/telegram-auth/"
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_TELEGRAM_ID = os.getenv("ADMIN_TELEGRAM_ID", "6895505562, 2132747990")

async def send_payment_info(bot_instance_or_message):
    text = (
        "💳 <b>Hisobni to'ldirish uchun to'lov ma'lumotlari:</b>\n\n"
        "Karta raqam: <code>4916 9903 5071 4777</code>\n"
        "Karta egasi: JORAYEV A\n\n"
        "<i>To'lovni amalga oshirgach, chekni (skrinshotni) quyidagi adminga yuboring, admin sizning hisobingizni to'ldirib beradi:</i>\n"
        "👉 @onlyforwardarx"
    )
    await bot_instance_or_message.reply_text(text, parse_mode="HTML")

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
        
        # Tugma yaratish (har doim chiqadi)
        keyboard = [[InlineKeyboardButton("💳 To'lov qilish", callback_data="pay_now")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        msg = f"👋 Assalomu alaykum, {user.first_name}!\n\n"
        msg += f"Siz muvaffaqiyatli ro'yxatdan o'tdingiz.\n\n"
        msg += f"🌐 <b>Saytga kirish uchun ma'lumotlaringiz:</b>\n"
        msg += f"Login: <code>{data['user']['username']}</code>\n"
        
        # Agar yangi ro'yxatdan o'tgan bo'lsa, parolni ham chiqaramiz
        if "initial_password" in data:
            msg += f"Parol: <code>{data['initial_password']}</code>\n"
            msg += f"\n<i>⚠️ Xavfsizlik uchun saytga kirganingizdan so'ng parolni o'zgartirib olishingizni tavsiya qilamiz.</i>\n\n"
        else:
            msg += f"Parol: <i>(Siz avvalroq ro'yxatdan o'tgansiz)</i>\n\n"

        msg += f"💰 Balansingiz: <b>{data['user']['credits']} token</b>.\n\n"
        msg += "Hisobingizni to'ldirish uchun quyidagi tugmani bosing:"

        await update.message.reply_text(
            msg,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
        
        # Agar saytdan "to'lov qilish" orqali "?start=pay" link kelgan bo'lsa
        args = context.args
        if args and args[0] == "pay":
            await send_payment_info(update.message)
            
    except requests.exceptions.ConnectionError:
        await update.message.reply_text("❌ Backendga ulanib bo'lmadi. Server o'chiq yoki IP noto'g'ri.")
    except requests.exceptions.HTTPError as e:
        await update.message.reply_text(f"❌ Backend xato qaytardi (HTTP {e.response.status_code}).")
    except Exception as e:
        await update.message.reply_text(f"❌ Kutilmagan xatolik: {str(e)}")
        print(f"DEBUG ERROR: {e}")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "pay_now":
        await send_payment_info(query.message)

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
        raise RuntimeError("BOT_TOKEN environment variable o'rnatilmagan")
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("promo", promo))
    app.add_handler(CallbackQueryHandler(button_callback))  # Inline buttonga handler
    
    print("Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()