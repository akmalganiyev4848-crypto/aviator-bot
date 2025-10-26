import telebot
import random
import json
import os

# 🔐 Token
TOKEN = "7253804878:AAGPZL3t3ugKYgeWDKB8_vvGG2KJvM_-AaA"
bot = telebot.TeleBot(TOKEN)

ACCESS_KEY = "230220004848"
USERS_FILE = "verified_users.json"

# ✅ Fayl mavjud bo‘lmasa — yaratamiz
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump([], f)

# ✅ Foydalanuvchilarni yuklash/saqlash
def load_verified_users():
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_verified_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

# 🎯 /start komandasi
@bot.message_handler(commands=['start'])
def start(message):
    text = (
        "👋 Salom!\n\n"
        "Botdan foydalanish uchun quyidagi amallarni bajaring:\n"
        "1️⃣ Ro‘yxatdan o‘ting 👉 https://lb-aff.com/L?tag=d_4114394m_22611c_site&site=4114394&ad=22611&r=registration\n"
        "2️⃣ Promo kod joyiga <b>AKIBET777</b> yozing.\n"
        "3️⃣ APK yuklab oling 👉 https://lb-aff.com/L?tag=d_4114394m_66803c_apk1&site=4114394&ad=66803\n"
        "4️⃣ To‘liq ro‘yxatdan o‘tgandan so‘ng ADMIN: @akibet1 ga yozing.\n"
        "✅ Admin sizga botning aktivatsiya kodini beradi."
    )
    bot.send_message(message.chat.id, text, parse_mode="HTML")

# 🔹 Aviator statistikaga mos KF yaratish
def generate_kf():
    rand = random.random()  # 0.0–1.0
    if rand < 0.7:  # 70% ehtimol bilan 1.0–3.0
        kf = round(random.uniform(1.00, 3.00), 2)
    elif rand < 0.9:  # 20% ehtimol bilan 3.0–5.0
        kf = round(random.uniform(3.01, 5.00), 2)
    else:  # 10% ehtimol bilan 5.01–10.0
        kf = round(random.uniform(5.01, 10.00), 2)
    return kf

# 🧩 Aktivatsiya kod tekshiruvi va KF funksiyasi
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.chat.id
    verified_users = load_verified_users()
    text = message.text.strip()

    # 🔑 Aktivatsiya kodi
    if text == ACCESS_KEY:
        if user_id not in verified_users:
            verified_users.append(user_id)
            save_verified_users(verified_users)
            bot.send_message(user_id, "✅ Bot aktivatsiya qilindi!\nEndi siz KF olish tugmasidan foydalanishingiz mumkin.")
        else:
            bot.send_message(user_id, "⚡ Siz allaqachon aktivatsiya qilingansiz!")
        return

    # 🔓 Aktiv foydalanuvchi uchun KF yuborish
    if user_id in verified_users:
        if text.lower() in ["kf", "🎯 kf olish"]:
            kf = generate_kf()
            bot.send_message(user_id, f"🎲 Sizga tavsiya etilgan KF: <b>{kf}</b>", parse_mode="HTML")
        else:
            bot.send_message(user_id, "🎯 KF olish uchun 'KF' deb yozing yoki tugmadan foydalaning.")
    else:
        # ❌ Aktiv bo‘lmagan foydalanuvchi
        bot.send_message(user_id, "⚠️ Siz hali botni aktiv qilmagansiz!\nIltimos, admin orqali aktivatsiya kodini oling.")

# 🔄 Botni ishga tushiramiz
bot.polling(none_stop=True)
