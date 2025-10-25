import telebot
from telebot import types
import random

TOKEN = "7253804878:AAGPZL3t3ugKYgeWDKB8_vvGG2KJvM_-AaA"
ADMIN_USERNAME = "akibet1"
ACCESS_KEY = "230220004848"  # Aktivatsiya kodi

bot = telebot.TeleBot(TOKEN)
verified_users = set()  # Aktiv foydalanuvchilar

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    link_button = types.InlineKeyboardButton("🔗 Ro‘yxatdan o‘tish", url="https://lb-aff.com/L?tag=d_4114394m_22611c_site&site=4114394&ad=22611&r=registration")
    apk_button = types.InlineKeyboardButton("📲 APK yuklab olish", url="https://lb-aff.com/L?tag=d_4114394m_66803c_apk1&site=4114394&ad=66803")
    markup.add(link_button)
    markup.add(apk_button)

    text = (
        "👋 Salom!\n\n"
        "Botdan foydalanish uchun quyidagi bosqichlarni bajaring:\n"
        "1️⃣ [Saytga kiring](https://lb-aff.com/L?tag=d_4114394m_22611c_site&site=4114394&ad=22611&r=registration)\n"
        "2️⃣ Ro‘yxatdan o‘tishda promo kod kiriting: **AKIBET777**\n"
        "3️⃣ APK versiyasini yuklab oling:\n"
        "👉 [APK yuklab olish havolasi](https://lb-aff.com/L?tag=d_4114394m_66803c_apk1&site=4114394&ad=66803)\n\n"
        "✅ To‘liq ro‘yxatdan o‘tgan bo‘lsangiz, ADMIN (@akibet1) ga yozing.\n"
        "U sizga botni **aktivatsiya kodi**ni beradi."
    )

    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)


@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.chat.id
    username = message.from_user.username

    # Admin signal yuborishi uchun
    if username == ADMIN_USERNAME:
        if message.text.startswith("signal:"):
            signal_text = message.text.replace("signal:", "").strip()
            if not signal_text:
                bot.send_message(user_id, "⚠️ Signal matni bo‘sh bo‘lmasligi kerak.")
                return
            for uid in verified_users:
                bot.send_message(uid, f"📡 *Signal:* {signal_text}", parse_mode="Markdown")
            bot.send_message(user_id, f"✅ Signal {len(verified_users)} foydalanuvchiga yuborildi.")
        return

    # Foydalanuvchi aktivatsiya kodi kiritgan bo‘lsa
    if message.text == ACCESS_KEY:
        verified_users.add(user_id)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kf_button = types.KeyboardButton("🎯 KF olish")
        markup.add(kf_button)
        bot.send_message(user_id, "✅ Aktivatsiya kodi to‘g‘ri!\nEndi sizga signal olish imkoniyati berildi.", reply_markup=markup)
        return

    # Foydalanuvchi KF so‘rasa
    if message.text == "🎯 KF olish":
        if user_id in verified_users:
            random_kf = round(random.uniform(1.00, 100.00), 2)
            bot.send_message(user_id, f"🎯 KF: *{random_kf}*", parse_mode="Markdown")
        else:
            bot.send_message(user_id, "❌ Siz hali aktivatsiya qilmagansiz. Avval admin bilan bog‘laning.")
        return

    # Aks holda
    bot.send_message(user_id, "❌ Noto‘g‘ri buyruq. Avval /start ni bosing.")


print("✅ Bot ishga tushdi...")
bot.polling(none_stop=True)
