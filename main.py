import telebot
from telebot import types
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
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_verified_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

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

# 🔹 KF tugmasini inline tarzda yuborish
def send_inline_kf(user_id):
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("🎯 KF olish", callback_data="get_kf")
    markup.add(btn)
    bot.send_message(user_id, "KF olish uchun tugmani bosing:", reply_markup=markup)

# 🔹 Aviatorga mos KF yaratish
def generate_kf():
    ranges = [(1.00, 3.00), (3.01, 5.00), (5.01, 10.00)]
    probs = [0.7, 0.2, 0.1]
    chosen_range = random.choices(ranges, weights=probs, k=1)[0]
    return round(random.uniform(*chosen_range), 2)

# 🔹 KF yuborish (rasimsiz)
def send_kf_text(user_id, kf):
    bot.send_message(user_id, f"🎲 Sizga tavsiya etilgan KF: <b>{kf}</b>", parse_mode="HTML")

# 🧩 Aktivatsiya kod tekshiruvi
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
            bot.send_message(user_id, "✅ Bot aktivatsiya qilindi!")
            send_inline_kf(user_id)
        else:
            bot.send_message(user_id, "⚡ Siz allaqachon aktivatsiya qilingansiz!")
        return

    # 🔓 Aktiv foydalanuvchi uchun KF tugmasini yuborish
    if user_id in verified_users:
        send_inline_kf(user_id)
    else:
        bot.send_message(user_id, "⚠️ Siz hali botni aktiv qilmagansiz!\nIltimos, admin orqali aktivatsiya kodini oling.")
        start(message)

# 🔹 Callback: Inline tugmani bosganda KF yuborish
@bot.callback_query_handler(func=lambda call: True)
def callback_kf(call):
    user_id = call.message.chat.id
    verified_users = load_verified_users()
    if user_id in verified_users and call.data == "get_kf":
        kf = generate_kf()
        send_kf_text(user_id, kf)
    else:
        bot.answer_callback_query(call.id, "⚠️ Siz hali botni aktiv qilmagansiz!")

# 🔄 Botni ishga tushiramiz
bot.polling(none_stop=True)
