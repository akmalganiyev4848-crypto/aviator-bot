import telebot
import random
import json
import os
from telebot import types

# 🔐 Token
TOKEN = "7253804878:AAGPZL3t3ugKYgeWDKB8_vvGG2KJvM_-AaA"
bot = telebot.TeleBot(TOKEN)

ACCESS_KEY = "230220004848"
USERS_FILE = "verified_users.json"
KF_FILE = "kf_history.json"

# ✅ Fayl mavjud bo‘lmasa — yaratamiz
for file in [USERS_FILE, KF_FILE]:
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump({}, f)

# ✅ Foydalanuvchilarni yuklash/saqlash
def load_verified_users():
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_verified_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

def load_kf_history():
    with open(KF_FILE, "r") as f:
        return json.load(f)

def save_kf_history(history):
    with open(KF_FILE, "w") as f:
        json.dump(history, f)

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
        "✅ Admin sizga botning aktivatsiya kodini beradi.\n\n"
        "💡 Qo‘shimcha komandalar:\n"
        "/tip - tasodifiy maslahat olish"
    )
    bot.send_message(message.chat.id, text, parse_mode="HTML")

# 🔹 Aviator statistikaga mos KF yaratish
def generate_kf():
    rand = random.random()
    if rand < 0.7:
        kf = round(random.uniform(1.00, 3.00), 2)
    elif rand < 0.9:
        kf = round(random.uniform(3.01, 5.00), 2)
    else:
        kf = round(random.uniform(5.01, 10.00), 2)
    return kf

# 🔹 Tavsiya / maslahatlar
TIPS = [
    "⚡ Bugun xavfsiz o‘yin uchun 1.5–3.0 oralig‘ida KFni tanlang.",
    "💡 Katta multiplikator olishni xohlaysizmi? 3.0–5.0 oralig‘ini sinab ko‘ring.",
    "⚠️ Ehtiyotkorlik: 5.0+ multiplikatorlar kam uchraydi, xavf yuqori.",
    "🎯 Har bir o‘yinda o‘rtacha multiplikatorni kuzatish foydali.",
    "💰 Strategik o‘yin uchun oldingi KFlarni tahlil qiling."
]

def get_random_tip():
    return random.choice(TIPS)

# 🔹 Inline tugma yaratish
def kf_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(text="🎯 KF olish", callback_data="get_kf")
    keyboard.add(button)
    return keyboard

# 🧩 Aktivatsiya kod tekshiruvi va tugmalar
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = str(message.chat.id)
    verified_users = load_verified_users()
    text = message.text.strip()

    # 🔑 Aktivatsiya kodi
    if text == ACCESS_KEY:
        if user_id not in verified_users:
            verified_users.append(user_id)
            save_verified_users(verified_users)
            bot.send_message(user_id, "✅ Bot aktivatsiya qilindi!\nEndi KF olish tugmasidan foydalanishingiz mumkin.", reply_markup=kf_keyboard())
        else:
            bot.send_message(user_id, "⚡ Siz allaqachon aktivatsiya qilingansiz!", reply_markup=kf_keyboard())
        return

    # 🔓 Aktiv bo‘lgan foydalanuvchiga KF tugmasini ko‘rsatish
    if user_id in verified_users:
        bot.send_message(user_id, "🎯 KF olish uchun tugmani bosing:", reply_markup=kf_keyboard())
    else:
        bot.send_message(user_id, "⚠️ Siz hali botni aktiv qilmagansiz!\nIltimos, admin orqali aktivatsiya kodini oling.")

# 🔹 Inline tugma bosilganda KF yuborish va maslahat
@bot.callback_query_handler(func=lambda call: call.data == "get_kf")
def send_kf(call):
    user_id = str(call.message.chat.id)
    verified_users = load_verified_users()

    if user_id in verified_users:
        kf = generate_kf()
        tip = get_random_tip()

        # KF tarixini yuklash
        history = load_kf_history()
        if user_id not in history:
            history[user_id] = []
        history[user_id].append(kf)
        if len(history[user_id]) > 10:
            history[user_id] = history[user_id][-10:]
        save_kf_history(history)

        # Xabar yuborish
        last_kfs = ", ".join(str(x) for x in history[user_id])
        bot.send_message(user_id, f"🎲 Sizga tavsiya etilgan KF: <b>{kf}</b>\n📊 So‘nggi KFlar: {last_kfs}\n💡 Maslahat: {tip}", parse_mode="HTML")
    else:
        bot.send_message(user_id, "⚠️ Siz hali botni aktiv qilmagansiz!")

# 🔹 /tip komandasi – foydalanuvchiga tasodifiy maslahat berish
@bot.message_handler(commands=['tip'])
def tip_command(message):
    user_id = str(message.chat.id)
    verified_users = load_verified_users()

    if user_id in verified_users:
        tip = get_random_tip()
        bot.send_message(user_id, f"💡 Tasodifiy maslahat: {tip}")
    else:
        bot.send_message(user_id, "⚠️ Siz hali botni aktiv qilmagansiz!")

# 🔄 Botni ishga tushiramiz
bot.polling(none_stop=True)
