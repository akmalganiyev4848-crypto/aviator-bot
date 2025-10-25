import telebot
from telebot import types
from datetime import datetime
import os

TOKEN = os.getenv(7253804878:AAGPZL3t3ugKYgeWDKB8_vvGG2KJvM_-AaA)
ADMIN_USERNAME = "akibet1"
ACCESS_KEY = "230220004848"

bot = telebot.TeleBot(TOKEN)
verified_users = set()  # Kalit kiritgan foydalanuvchilar ro‘yxati

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    link_button = types.InlineKeyboardButton(
        "🔗 Sayt orqali ro‘yxatdan o‘tish", 
        url="https://lb-aff.com/L?tag=d_4114394m_22611c_site&site=4114394&ad=22611&r=registration"
    )
    check_button = types.InlineKeyboardButton("✅ Tekshirish", callback_data="check")
    markup.add(link_button)
    markup.add(check_button)

    text = (
        "👋 <b>Salom!</b>\n\n"
        "Aviator signallarini olish uchun quyidagi havola orqali ro‘yxatdan o‘ting:\n"
        "👉 <a href='https://lb-aff.com/L?tag=d_4114394m_22611c_site&site=4114394&ad=22611&r=registration'>Sayt havolasi</a>\n\n"
        "Promo kod: <b>AKIBET777</b>\n\n"
        "Ro‘yxatdan o‘tgach, pastdagi <b>✅ Tekshirish</b> tugmasini bosing."
    )

    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data == "check":
        bot.answer_callback_query(call.id, "Tekshirish jarayonida...")
        bot.send_message(call.message.chat.id,
                         "🔑 Ro‘yxatdan o‘tgan bo‘lsangiz, endi <b>kalit so‘zni</b> yuboring.\n\n"
                         f"Admin: @{ADMIN_USERNAME}",
                         parse_mode="HTML")


@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.chat.id
    username = message.from_user.username

    # 1️⃣ Admin signal yuborayotgan bo‘lsa
    if username == ADMIN_USERNAME:
        if message.text.startswith("signal:"):
            signal_text = message.text.replace("signal:", "").strip()
            if not signal_text:
                bot.send_message(user_id, "⚠️ Signal matni bo‘sh bo‘lishi mumkin emas.")
                return

            current_time = datetime.now().strftime("%H:%M")
            formatted_signal = f"📡 <b>Yangi signal ({current_time}):</b>\n{signal_text}"

            if verified_users:
                for uid in verified_users:
                    bot.send_message(uid, formatted_signal, parse_mode="HTML")
                bot.send_message(user_id, f"✅ Signal {len(verified_users)} ta foydalanuvchiga yuborildi.")
            else:
                bot.send_message(user_id, "⚠️ Hozircha signal olishga ro‘yxatdan o‘tgan foydalanuvchi yo‘q.")
        return

    # 2️⃣ Oddiy foydalanuvchi kalit kiritayotgan bo‘lsa
    if message.text == ACCESS_KEY:
        verified_users.add(user_id)
        bot.send_message(user_id, "✅ Kalit to‘g‘ri! Siz signal olish uchun ro‘yxatdan o‘tdingiz.")
    else:
        if user_id not in verified_users:
            bot.send_message(user_id, f"❌ Kalit noto‘g‘ri!\nAdmin bilan bog‘laning: @{ADMIN_USERNAME}")


print("Bot ishlayapti...")
bot.polling(none_stop=True)
