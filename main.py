import telebot
from telebot import types
from datetime import datetime
import os

TOKEN = os.getenv("TOKEN")
ADMIN_USERNAME = "akibet1"
ACCESS_KEY = "230220004848"

bot = telebot.TeleBot(TOKEN)
verified_users = set()

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    link_button = types.InlineKeyboardButton(
        "🔗 Sayt orqali ro‘yxatdan o‘tish",
        url="https://lb-aff.com/L?tag=d_4114394m_22611c_&site=4114394&ad=22611&r=registration"
    )
    check_button = types.InlineKeyboardButton("✅ Tekshirish", callback_data="check")
    markup.add(link_button)
    markup.add(check_button)
    text = (
        "👋 Salom!\n\n"
        "Aviator signallarini olish uchun quyidagi havola orqali ro‘yxatdan o‘ting:\n"
        "👉 [Ro‘yxatdan o‘tish havolasi](https://lb-aff.com/L?tag=d_4114394m_22611c_&site=4114394&ad=22611&r=registration)\n\n"
        "Promo kod: *AKIBET777*\n\n"
        "Ro‘yxatdan o‘tgach, pastdagi '✅ Tekshirish' tugmasini bosing."
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data == "check":
        bot.answer_callback_query(call.id, "Tekshirish jarayonida...")
        bot.send_message(call.message.chat.id,
                         "🔑 Ro‘yxatdan o‘tgan bo‘lsangiz, endi **kalit so‘zni** yuboring.\n\n"
                         f"Admin: @{ADMIN_USERNAME}")

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.chat.id
    username = message.from_user.username

    if username == ADMIN_USERNAME:
        if message.text.startswith("signal:"):
            signal_text = message.text.replace("signal:", "").strip()
            if not signal_text:
                bot.send_message(user_id, "⚠️ Signal matni bo‘sh bo‘lishi mumkin emas.")
                return
            current_time = datetime.now().strftime("%H:%M")
            formatted_signal = f"📡 *Yangi signal ({current_time}):* {signal_text}"
            if verified_users:
                for uid in verified_users:
                    bot.send_message(uid, formatted_signal, parse_mode="Markdown")
                bot.send_message(user_id, f"✅ Signal {len(verified_users)} ta foydalanuvchiga yuborildi.")
            else:
                bot.send_message(user_id, "⚠️ Hozircha signal olishga ro‘yxatdan o‘tgan foydalanuvchi yo‘q.")
        return

    if message.text == ACCESS_KEY:
        verified_users.add(user_id)
        bot.send_message(user_id, "✅ Kalit to‘g‘ri! Siz signal olish uchun ro‘yxatdan o‘tgan foydalanuvchilar orasidasiz.")
    else:
        if user_id not in verified_users:
            bot.send_message(user_id, f"❌ Kalit noto‘g‘ri, qaytadan urinib ko‘ring yoki admin bilan bog‘laning: @{ADMIN_USERNAME}")

print("Bot ishlayapti...")
bot.polling()
