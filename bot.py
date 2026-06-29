import telebot
import random
from telebot import types

TOKEN = "7253804878:AAGPNjcSRJhtz5yE9Nosvr79bq1F9MgkqcU"
SECRET_CODE = "23022000"  # Siz aytgan maxfiy kod
ADMIN_USERNAME = "@gv_aki"  # Sizning username'ingiz

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
    text = message.text.strip()

    if text == "🎁 Promo-kod bilan Bonus":
        bonus_text = (
            "🎁 **BOTNI FAOLLASHTIRISH VA BONUS OLISH QO'LLANMASI**\n\n"
            "1️⃣ Pastdagi tugma orqali Linebet saytida yangi akkaunt oching.\n"
            "2️⃣ Ro'yxatdan o'tishda **AKIBET777** promo-kodini kiriting.\n"
            f"3️⃣ Ro'yxatdan o'tganingizdan so'ng, akkaunt ID raqamingiz yoki skrinshotini adminga ({ADMIN_USERNAME}) yuboring.\n\n"
            "🔑 Admin tekshirib, sizga botni faollashtiruvchi **maxfiy kodni** beradi. O'sha kodni ushbu botga yozsangiz, signallar ochiladi!"
        )
        inline_markup = types.InlineKeyboardMarkup()
        # Sizning yangi referal havolangiz shu yerga qo'yildi
        link_btn = types.InlineKeyboardButton("🌐 Linebet saytiga o'tish", url="https://lb-aff.com/L?tag=d_4114394m_22611c_&site=4114394&ad=22611")
        admin_btn = types.InlineKeyboardButton("👤 Adminga yozish", url=f"https://t.me/{ADMIN_USERNAME.replace('@', '')}")
        inline_markup.add(link_btn)
        inline_markup.add(admin_btn)
        bot.send_message(user_id, bonus_text, reply_markup=inline_markup, parse_mode="Markdown")

    elif text == "🚀 Signal olish":
        # Ruxsat tekshirish
        if user_id not in allowed_users:
            alert_text = (
                "🛑 **Kirish taqiqlangan!**\n\n"
                f"Siz hali botni faollashtirmadingiz. Iltimos, **🎁 Promo-kod bilan Bonus** tugmasini bosing, shartlarni bajarib adminga ({ADMIN_USERNAME}) yozing va faollashtirish kodini oling."
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

    elif text == "📊 Aviator Statistika":
        stat_text = (
            "📊 **Aviator Global O'yinlar Statistikasi (Oxirgi 10,000 raund):**\n\n"
            "🔹 **1.00x - 1.60x (Eng ko'p chiqadigan):** 62.4% holatda\n"
            "🔹 **1.70x - 3.50x (O'rtacha ko'rsatkich):** 26.8% holatda\n"
            "🔹 **4.00x - 10.00x (Kam uchraydigan):** 8.3% holatda\n"
            "🔹 **10.00x dan yuqori (Ultra risk):** 2.5% holatda\n\n"
            "🤖 *Bizning botimiz ushbu matematik algoritmlarni hisoblab, sizga eng xavfsiz nuqtani ko'rsatib beradi.*"
        )
        bot.send_message(user_id, stat_text, parse_mode="Markdown")

    elif text == SECRET_CODE:
        # Foydalanuvchi to'g'ri kodni kiritganda
        if user_id in allowed_users:
            bot.send_message(user_id, "ℹ️ Botingiz allaqachon faollashtirilgan!", reply_markup=main_menu())
        else:
            save_user(user_id)
            bot.send_message(
                user_id, 
                "🎉 **Tabriklaymiz! Maxfiy kod qabul qilindi va botingiz muvaffaqiyatli faollashtirildi!**\n\nEndi **🚀 Signal olish** tugmasini bosib cheksiz signallardan foydalanishingiz mumkin!", 
                reply_markup=main_menu()
            )
    else:
        # Kod noto'g'ri bo'lsa yoki boshqa matn yozilsa
        if user_id not in allowed_users:
            bot.send_message(user_id, f"❌ **Noto'g'ri kod yoki tushunarsiz buyruq!**\n\nBotni faollashtirish kodini olish uchun adminga murojaat qiling: {ADMIN_USERNAME}")
        
