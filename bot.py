import telebot
from telebot import types
import random

TOKEN = "7253804878:AAGPZL3t3ugKYgeWDKB8_vvGG2KJvM_-AaA"
ADMIN_ID = 7960951525
bot = telebot.TeleBot(TOKEN)

# Foydalanuvchilar holati
users = {}

def menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🚀 Signal olish", "🎁 Promo-kod bilan Bonus")
    markup.add("👨‍💻 Admin bilan bog'lanish")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 
                     "👋 *Aviator VIP* botiga xush kelibsiz!\n\n"
                     "Bizning signallar orqali daromad olishingiz mumkin.\n"
                     "Diqqat: Signal olish uchun promo-kodimizdan foydalaning!", 
                     parse_mode="Markdown", reply_markup=menu())

@bot.message_handler(content_types=['text'])
def handle(message):
    if message.text == "🚀 Signal olish":
        # Signal generatsiyasi
        signal = round(random.uniform(1.20, 8.50), 2)
        bot.send_message(message.chat.id, 
                         f"🎯 *Aviator natijasi:* `{signal}x`\n\n"
                         "⚠️ *Muhim:* Bonusli koeffitsiyentlar uchun albatta **AKIBET777** promo-kodi bilan ro'yxatdan o'tgan bo'lishingiz kerak!", 
                         parse_mode="Markdown")
    
    elif message.text == "🎁 Promo-kod bilan Bonus":
        bot.send_message(message.chat.id, 
                         "🎁 *Promo-kod:* `AKIBET777`\n\n"
                         "1️⃣ Linebet ilovasini yuklang.\n"
                         "2️⃣ Ro'yxatdan o'tishda ushbu kodni kiriting.\n"
                         "3️⃣ Birinchi depozitga 100% bonus oling!\n\n"
                         "👇 Ro'yxatdan o'tish uchun havola:\n[Linebetga kirish](http://linebet.com)", 
                         parse_mode="Markdown")
                         
    elif message.text == "👨‍💻 Admin bilan bog'lanish":
        bot.send_message(message.chat.id, "Admin: @AkmalGaniyev")

bot.infinity_polling()

