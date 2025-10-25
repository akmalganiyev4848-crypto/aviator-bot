import telebot
from telebot import types
import os

TOKEN = os.environ.get("7253804878:AAGPZL3t3ugKYgeWDKB8_vvGG2KJvM_-AaA")
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    link_button = types.InlineKeyboardButton(
        "🔗 Sayt havolasi",
        url="https://lb-aff.com/L?tag=d_4114394m_22611c_site&site=4114394&ad=22611&r=registration"
    )
    check_button = types.InlineKeyboardButton("✅ Tekshirish", callback_data="check")
    markup.add(link_button)
    markup.add(check_button)

    text = (
        "👋 <b>Salom!</b>\n\n"
        "Aviator signallarini olish uchun avval ro‘yxatdan o‘ting:\n"
        "👉 <a href='https://lb-aff.com/L?tag=d_4114394m_22611c_site&site=4114394&ad=22611&r=registration'>Sayt havolasi</a>\n"
        "Promo kod: <b>AKIBET777</b>\n\n"
        "Ro‘yxatdan o‘tgach, pastdagi <b>✅ Tekshirish</b> tugmasini bosing."
    )

    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data == "check":
        bot.answer_callback_query(call.id, "Tekshirish jarayonida...")
        bot.send_message(
            call.message.chat.id,
            "✅ Rahmat! Sizning akkauntingiz tekshirilmoqda.\nTasdiqlangach, sizga signal beriladi."
        )

print("Bot ishga tushdi...")
bot.polling(non_stop=True)
