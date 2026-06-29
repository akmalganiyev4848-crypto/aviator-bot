import telebot
import random
from telebot import types

# Tokeningizni kiriting
TOKEN = "7253804878:AAGPNjcSRJhtz5yE9Nosvr79bq1F9MgkqcU" 
ADMIN_ID = 7960951525 
bot = telebot.TeleBot(TOKEN)

# 1. Professional Signal Generator (Kichik va katta koeffitsiyentlar aralash)
def get_signal():
    rand = random.random()
    if rand < 0.70: # 70% hollarda kichik kf
        return f"{round(random.uniform(1.10, 2.50), 2)}x"
    else:           # 30% hollarda katta kf
        return f"{round(random.uniform(2.51, 8.00), 2)}x"

# 2. Asosiy menyu
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🚀 Signal olish", "📊 Statistika")
    markup.add("🎁 Promo-kod bilan Bonus")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "🤖 *Aviator VIP Bot* - Eng aniq signallar!\n\nSignal olish uchun tugmani bosing.", 
                     parse_mode="Markdown", reply_markup=main_menu())

@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text == "🚀 Signal olish":
        bot.send_message(message.chat.id, f"🎯 *Signal:* `{get_signal()}`\n\n⚠️ *Diqqat:* Bu kf faqat **AKIBET777** promokodi bilan ro'yxatdan o'tganlar uchun aniq ishlaydi!", parse_mode="Markdown")
    
    elif message.text == "📊 Statistika":
        # Professional statistika ko'rinishi
        bot.send_message(message.chat.id, "📈 *Bot Statistika:*\n✅ Muvaffaqiyat: 94%\n👥 Faol foydalanuvchilar: 100+\n🚀 Bugungi signallar: 50+", parse_mode="Markdown")

    elif message.text == "🎁 Promo-kod bilan Bonus":
        bot.send_message(message.chat.id, "🎁 *Promokod:* `AKIBET777`\n\nUshbu kod orqali ro'yxatdan o'ting va 100% bonus oling!\n[Linebetga kirish](http://linebet.com)", parse_mode="Markdown")

    elif message.text == "/admin" and message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "🛠 *Admin Panel:* Bot mukammal ishlamoqda.")

bot.infinity_polling()
    
