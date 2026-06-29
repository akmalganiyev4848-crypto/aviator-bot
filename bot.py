import telebot
import random
from telebot import types

TOKEN = "7253804878:AAGPNjcSRJhtz5yE9Nosvr79bq1F9MgkqcU"
ADMIN_ID = 7960951525  # Sizning to'g'ri Telegram ID raqamingiz shu yerga qo'yildi!

bot = telebot.TeleBot(TOKEN)

# Ruxsat berilgan foydalanuvchilar ro'yxati (Baza)
try:
    with open("allowed_users.txt", "r") as f:
        allowed_users = set(int(line.strip()) for line in f if line.strip())
except FileNotFoundError:
    allowed_users = set()

def save_user(user_id):
    allowed_users.add(user_id)
    with open("allowed_users.txt", "a") as f:
        f.write(f"{user_id}\n")

# Asosiy menyu
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("🚀 Signal olish")
    btn2 = types.KeyboardButton("🎁 Promo-kod bilan Bonus")
    btn3 = types.KeyboardButton("📊 Aviator Statistika")
    markup.add(btn1, btn2)
    markup.add(btn3)
    return markup

# /start buyrug'i
@bot.message_handler(commands=['start'])
def start(message):
    welcome_text = (
        "👋 **Aviator Ultra Pro Signal Botiga xush kelibsiz!**\n\n"
        "🎯 Bu bot sun'iy intellekt va Aviatorning matematik algoritmlari asosida ishlaydi.\n\n"
        "🔒 **Bot hozir yopiq holatda.** Signallarni faollashtirish uchun pastdagi **🎁 Promo-kod bilan Bonus** tugmasini bosing va faollashtirish kodini olish shartlarini bajaring!"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu(), parse_mode="Markdown")

# Matnli xabarlarni qayta ishlash
@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.chat.id
    username = f"@{message.from_user.username}" if message.from_user.username else "Yashirin profil"

    if message.text == "🎁 Promo-kod bilan Bonus":
        bonus_text = (
            "🎁 **BOTNI FAOLLASHTIRISH VA BONUS OLISH QO'LLANMASI**\n\n"
            "1️⃣ Linebet rasmiy saytida yangi akkaunt oching.\n"
            "2️⃣ Ro'yxatdan o'tishda **AKIBET777** promo-kodini kiriting.\n"
            "3️⃣ Akkauntingiz ID raqamini yoki ro'yxatdan o'tganingiz haqidagi skrinshotni shu yerga xabar qilib yuboring.\n\n"
            "⏳ Siz yuborgan ma'lumotni admin tekshirib, 5-10 daqiqa ichida botingizni faollashtirib beradi!"
        )
        inline_markup = types.InlineKeyboardMarkup()
        link_btn = types.InlineKeyboardButton("🌐 Linebet rasmiy sayti", url="https://linebet.com")
        inline_markup.add(link_btn)
        bot.send_message(user_id, bonus_text, reply_markup=inline_markup, parse_mode="Markdown")

    elif message.text == "🚀 Signal olish":
        # Ruxsat tekshirish
        if user_id not in allowed_users:
            alert_text = (
                "🛑 **Kirish taqiqlangan!**\n\n"
                "Siz hali admin tomonidan tasdiqlanmadingiz. Iltimos, **🎁 Promo-kod bilan Bonus** tugmasini bosib, ko'rsatmalarni bajaring va ID raqamingizni yuborib kuting."
            )
            bot.send_message(user_id, alert_text, parse_mode="Markdown")
        else:
            # Aviator real matematik statistikasi bo'yicha kf chiqarish
            rand = random.random()
            if rand < 0.60:    # 60% holatda eng ko'p chiqadigan past kf
                coeff = round(random.uniform(1.10, 1.65), 2)
            elif rand < 0.90:  # 30% holatda o'rtacha kf
                coeff = round(random.uniform(1.70, 3.45), 2)
            else:              # 10% holatda kam chiqadigan yuqori kf
                coeff = round(random.uniform(4.00, 12.50), 2)

            signal_text = (
                "🎯 **ULTRA PRO SIGNAL** 🎯\n\n"
                f"🚀 Kutilayotgan koeffitsiyent: **{coeff}x**\n"
                "📉 Tavsiya: Pulingizni belgilangan koeffitsiyentga yetmasdan yechib olishga ulguring!\n\n"
                "👉 Ishonchlilik darajasi: 93% (Faqat Linebet rasmiy saytida va AKIBET777 promo-kodi bilan)."
            )
            bot.send_message(user_id, signal_text, parse_mode="Markdown")

    elif message.text == "📊 Aviator Statistika":
        stat_text = (
            "📊 **Aviator Global O'yinlar Statistikasi (Oxirgi 10,000 raund):**\n\n"
            "🔹 **1.00x - 1.60x (Eng ko'p chiqadigan):** 62.4% holatda\n"
            "🔹 **1.70x - 3.50x (O'rtacha ko'rsatkich):** 26.8% holatda\n"
            "🔹 **4.00x - 10.00x (Kam uchraydigan):** 8.3% holatda\n"
            "🔹 **10.00x dan yuqori (Ultra risk):** 2.5% holatda\n\n"
            "🤖 *Bizning botimiz ushbu matematik algoritmlarni hisoblab, sizga eng xavfsiz nuqtani ko'rsatib beradi.*"
        )
        bot.send_message(user_id, stat_text, parse_mode="Markdown")

    else:
        # Foydalanuvchi ID yoki skrinshot yuborganida adminga xabar ketadi
        if user_id != ADMIN_ID:
            bot.send_message(ADMIN_ID, f"🔔 **Yangi ariza!**\n\nFoydalanuvchi: {username}\nID: `{user_id}`\nXabari: {message.text}\n\nUshbu foydalanuvchiga ruxsat berish uchun pastdagi buyruqni bosing:\n/allow_{user_id}", parse_mode="Markdown")
            bot.send_message(user_id, "✅ Ma'lumotlaringiz adminga yuborildi. Tasdiqlanishini kuting...")

# Admin foydalanuvchiga ruxsat berganida (/allow_ID buyrug'i)
@bot.message_handler(commands=['allow'])
@bot.message_handler(func=lambda message: message.text.startswith('/allow_'))
def admin_allow_user(message):
    if message.chat.id == ADMIN_ID:
        try:
            target_user_id = int(message.text.split('_')[1])
            save_user(target_user_id)
            
            bot.send_message(ADMIN_ID, f"✅ Foydalanuvchi (ID: {target_user_id}) muvaffaqiyatli tasdiqlandi!")
            bot.send_message(target_user_id, "🎉 **Tabriklaymiz! Admin sizning so'rovingizni tasdiqladi.**\n\nEndi bot to'liq faollashdi. **🚀 Signal olish** tugmasini bosib signallardan cheksiz foydalanishingiz mumkin!", reply_markup=main_menu())
        except Exception as e:
            bot.send_message(ADMIN_ID, "❌ Buyruq xato bajarildi yoki ID topilmadi.")

if __name__ == '__main__':
    bot.polling(none_stop=True)
            
