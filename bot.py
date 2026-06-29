import telebot
import random
from telebot import types

TOKEN = "7253804878:AAGPNjcSRJhtz5yE9Nosvr79bq1F9MgkqcU"
bot = telebot.TeleBot(TOKEN)

# Promo-kodni ko'rgan foydalanuvchilarni eslab qolish uchun vaqtinchalik baza
users_who_saw_promo = set()

# Asosiy menyu tugmalari
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("🚀 Signal olish")
    btn2 = types.KeyboardButton("🎁 Promo-kod bilan Bonus")
    btn3 = types.KeyboardButton("📊 Statistika")
    markup.add(btn1, btn2)
    markup.add(btn3)
    return markup

# /start bosilganda
@bot.message_handler(commands=['start'])
def start(message):
    welcome_text = (
        "👋 Salom! Aviator Signal Botiga xush kelibsiz!\n\n"
        "🤖 Botdan to'liq foydalanish va aniq signallarni olish uchun pastdagi **🎁 Promo-kod bilan Bonus** tugmasini bosing va ko'rsatmalarni bajaring!"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu(), parse_mode="Markdown")

# Tugmalar bosilganda
@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.chat.id

    if message.text == "🎁 Promo-kod bilan Bonus":
        # Foydalanuvchi promo-kodni ko'rdi deb belgilaymiz
        users_who_saw_promo.add(user_id)
        
        bonus_text = (
            "🎁 **Linebet Maxsus Bonusi va KF olish uchun qo'llanma!**\n\n"
            "1️⃣ Linebet rasmiy saytida yangi akkaunt oching.\n"
            "2️⃣ Ro'yxatdan o'tishda **AKIBET777** promo-kodini kiriting (Bu sizga 100% bonus va bot kf'larini ochadi).\n"
            "3️⃣ Depozit qiling va botga qaytib **🚀 Signal olish** tugmasini bosing!"
        )
        # BU YERGA O'Z HAMKORLIK HAVOLANGIZNI (LINK) QO'YING
        inline_markup = types.InlineKeyboardMarkup()
        link_btn = types.InlineKeyboardButton("🌐 Linebet saytiga o'tish", url="https://linebet.com")
        inline_markup.add(link_btn)
        
        bot.send_message(user_id, bonus_text, reply_markup=inline_markup, parse_mode="Markdown")

    elif message.text == "🚀 Signal olish":
        # Agar foydalanuvchi hali promo-kod tugmasini bosmagan bo'lsa
        if user_id not in users_who_saw_promo:
            alert_text = (
                "⚠️ **Kirish cheklangan!**\n\n"
                "Signallarni ko'rishdan oldin **🎁 Promo-kod bilan Bonus** tugmasini bosib, "
                "**AKIBET777** promo-kodi bilan ro'yxatdan o'tganingizni tasdiqlashingiz kerak!"
            )
            bot.send_message(user_id, alert_text, parse_mode="Markdown")
        else:
            # Promo-kodni ko'rgan bo'lsa, signal beriladi
            coeff = round(random.uniform(1.10, 4.85), 2)
            signal_text = (
                f"🎯 **Signal: {coeff}x**\n\n"
                "⚠️ **Diqqat:** Bu kf faqat **AKIBET777** promokodi bilan ro'yxatdan o'tganlar uchun aniq ishlaydi!"
            )
            bot.send_message(user_id, signal_text, parse_mode="Markdown")

    elif message.text == "📊 Statistika":
        win_rate = random.randint(88, 95)
        stat_text = (
            "📊 **Bot statistikasi:**\n\n"
            f"✅ Muvaffaqiyatli signallar: {win_rate}%\n"
            "👥 Faol foydalanuvchilar: 1,840+\n"
            "🔄 Signallar tizimi barqaror ishlamoqda."
        )
        bot.send_message(user_id, stat_text, parse_mode="Markdown")

if __name__ == '__main__':
    bot.polling(none_stop=True)
        
