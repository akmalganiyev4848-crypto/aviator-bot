import telebot
from telebot import types

# ⚠️ MANA SHU YERDAGI QO'SHTIRNOQ ICHIGA O'ZINGNING TOKENINGNI YOZ:
TOKEN = "7123456789:ABCdefGhIJKlmNoPQRstUVwXyZ"

# PythonAnywhere tekin akkaunti uchun Proxy sozlamasi:
from telebot import apihelper
apihelper.proxy = {'http': 'http://proxy.server:3128'}

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# SIZNING MA'LUMOTLARINGIZ
PROMO_KOD = "AKIBET777"
SAYT_LINK = "https://lb-aff.com/L?tag=d_4114394m_22611c_site&site=4114394&ad=22611&r=registration"
APK_LINK = "https://lb-aff.com/L?tag=d_4114394m_66803c_apk1&site=4114394&ad=66803"

# Tasdiqlangan foydalanuvchilar ro'yxati
tasdiqlangan_foydalanuvchilar = set()

# Ro'yxatdan o'tish tugmalari
def royxatdan_otish_tugmalari():
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton(text="🌐 Sayt orqali ro'yxatdan o'tish", url=SAYT_LINK)
    btn2 = types.InlineKeyboardButton(text="📱 APK yuklab olish (Android)", url=APK_LINK)
    markup.add(btn1)
    markup.add(btn2)
    return markup

@bot.message_handler(commands=['start'])
def start_komandasi(message):
    user_id = message.from_user.id
    
    # Agar foydalanuvchi allaqachon tasdiqlangan bo'lsa
    if user_id in tasdiqlangan_foydalanuvchilar:
        bot.send_message(message.chat.id, f"🚀 Xush kelibsiz, <b>{message.from_user.first_name}</b>! Bot siz uchun faol.")
        return

    # Shartlarni ko'rsatish
    matn = (
        f"Salom, <b>{message.from_user.first_name}</b>! 👋\n\n"
        f"⚠️ Botdan to'liq foydalanish va signallarni ko'rish uchun quyidagi shartlarni bajaring:\n\n"
        f"1️⃣ Pastdagi tugmalar orqali sayt yoki APK ilovadan ro'yxatdan o'ting.\n"
        f"2️⃣ Ro'yxatdan o'tishda <b>{PROMO_KOD}</b> promokodini kiriting (bu majburiy!).\n\n"
        f"Ro'yxatdan o'tib bo'lgach, faollashtirish uchun botga promokodingizni yozib yuboring 👇:"
    )
    bot.send_message(message.chat.id, matn, reply_markup=royxatdan_otish_tugmalari())

@bot.message_handler(func=lambda message: True)
def xabarlarni_filtrlash(message):
    user_id = message.from_user.id
    kiritilgan_kod = message.text.strip().upper()

    # Agar foydalanuvchi hali tasdiqlanmagan bo'lsa va promokod yuborgan bo'lsa
    if user_id not in tasdiqlangan_foydalanuvchilar:
        if kiritilgan_kod == PROMO_KOD:
            tasdiqlangan_foydalanuvchilar.add(user_id)
            bot.send_message(
                message.chat.id, 
                f"✅ <b>Muvaffaqiyatli faollashtirildi!</b>\nPromokod to'g'ri. Bot siz uchun ochildi! 🚀"
            )
        else:
            bot.send_message(
                message.chat.id, 
                f"❌ Noto'g'ri promokod kiritildi!\nQaytadan urinib ko'ring yoki to'g'ri havoladan o'ting:",
                reply_markup=royxatdan_otish_tugmalari()
            )
        return

    # SIZNING ASOSIY BOT FUNKSIYALARINGIZ
    if message.text == "Signal 🚀":
        bot.send_message(message.chat.id, "🎯 Keyingi Aviator koeffitsiyenti: 1.95x\nTikishga tayyorlaning!")
    else:
        bot.send_message(message.chat.id, "Bot faol! Kerakli buyruqni tanlang.")

if __name__ == "__main__":
    print("Bot muvaffaqiyatli ishga tushdi...")
    bot.infinity_polling()
    
