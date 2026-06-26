import telebot
from telebot import types
from telebot import apihelper
import random
import time

# Sening haqiqiy tokening joyiga qo'yildi:
TOKEN = "7253804878:AAGPZL3t3ugKYgeWDKB8_vvGG2KJvM_-AaA"

# PythonAnywhere tekin akkaunti uchun Proxy sozlamasi:
apihelper.proxy = {'http': 'http://proxy.server:3128'}

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# ADMIN VA SOZLAMALAR (Sening Telegram ID'ng qo'yildi)
ADMIN_ID = 7960951525  
PROMO_KOD = "AKIBET777"
SAYT_LINK = "https://lb-aff.com/L?tag=d_4114394m_22611c_site&site=4114394&ad=22611&r=registration"
APK_LINK = "https://lb-aff.com/L?tag=d_4114394m_66803c_apk1&site=4114394&ad=66803"

# MA'LUMOTLAR BAZASI
tasdiqlanganlar = set()
kutilayotganlar = {}  # user_id: kiritilgan_linebet_id
kunlik_limit = {}  # user_id: qolgan_signallar

def asosiy_menyu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🚀 Signal olish"), types.KeyboardButton("📊 Statistika"))
    markup.add(types.KeyboardButton("ℹ️ Yordam"))
    return markup

def royxatdan_otish_tugmalari():
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton(text="🌐 Linebet Saytida ro'yxatdan o'tish", url=SAYT_LINK)
    btn2 = types.InlineKeyboardButton(text="📱 Linebet APK yuklab olish", url=APK_LINK)
    markup.add(btn1)
    markup.add(btn2)
    return markup

@bot.message_handler(commands=['start'])
def start_komandasi(message):
    user_id = message.from_user.id

    if user_id in tasdiqlanganlar or user_id == ADMIN_ID:
        bot.send_message(message.chat.id, "🚀 Aviator VIP botiga xush kelibsiz! Quyidagi menyudan foydalaning:", reply_markup=asosiy_menyu())
        return

    matn = (
        f"Salom, <b>{message.from_user.first_name}</b>! 👋\n\n"
        f"⚠️ Bot signallarini ochish uchun quyidagi shartlarni bajaring:\n\n"
        f"1️⃣ Pastdagi tugmalar orqali <b>Linebet</b> saytida yoki ilovasida yangi akkaunt oching.\n"
        f"2️⃣ Ro'yxatdan o'tishda majburiy <b>{PROMO_KOD}</b> promokodini kiriting.\n\n"
        f"Ro'yxatdan o'tib bo'lgach, Linebet shaxsiy kabinetingizdagi <b>Akkaunt ID (Foydalanuvchi ID)</b> raqamingizni botga yozib yuboring 👇:"
    )
    bot.send_message(message.chat.id, matn, reply_markup=royxatdan_otish_tugmalari())

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    if not kutilayotganlar:
        bot.send_message(ADMIN_ID, "📭 Hozircha tasdiqlash kutilayotgan a'zolar yo'q.")
        return
        
    for uid, linebet_id in list(kutilayotganlar.items()):
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"accept_{uid}"),
            types.InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{uid}")
        )
        bot.send_message(ADMIN_ID, f"👤 Foydalanuvchi: <a href='tg://user?id={uid}'>{uid}</a>\n🆔 Kiritgan Linebet ID: <code>{linebet_id}</code>\n\nUshbu ID sizning promokodingizdan o'tgan bo'lsa, tasdiqlang:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_javob(call):
    user_id = call.from_user.id
            
    if call.data.startswith("accept_") and user_id == ADMIN_ID:
        target_uid = int(call.data.split("_")[1])
        tasdiqlanganlar.add(target_uid)
        if target_uid in kutilayotganlar: del kutilayotganlar[target_uid]
        bot.edit_message_text(f"✅ Linebet ID ({target_uid}) tasdiqlandi!", ADMIN_ID, call.message.message_id)
        bot.send_message(target_uid, "🎉 <b>Tabriklaymiz!</b> Sizning Linebet ID raqamingiz tekshiruvdan muvaffaqiyatli o'tdi. Bot signallari siz uchun ochildi! 🚀", reply_markup=asosiy_menyu())
        
    elif call.data.startswith("reject_") and user_id == ADMIN_ID:
        target_uid = int(call.data.split("_")[1])
        if target_uid in kutilayotganlar: del kutilayotganlar[target_uid]
        bot.edit_message_text(f"❌ Foydalanuvchi ({target_uid}) arizasi rad etildi.", ADMIN_ID, call.message.message_id)
        bot.send_message(target_uid, f"❌ Siz kiritgan Linebet ID tekshiruvdan o'tmadi. Iltimos, faqat <b>{PROMO_KOD}</b> promokodi bilan ochilgan to'g'ri ID raqamingizni yuboring!")

@bot.message_handler(func=lambda message: True)
def xabarlar(message):
    user_id = message.from_user.id

    if user_id not in tasdiqlanganlar and user_id != ADMIN_ID:
        if message.text.isdigit():
            kutilayotganlar[user_id] = message.text
            bot.send_message(message.chat.id, "⏳ <b>Linebet ID qabul qilindi!</b>\nAdminlarimiz 5-10 daqiqa ichida sizni Linebet sheriklik tizimidan tekshirib, botni faollashtirishadi. Iltimos kuting...")
            bot.send_message(ADMIN_ID, f"🔔 Yangi Linebet ID ariza keldi! Ko'rish uchun /admin buyrug'ini bosing.")
        else:
            bot.send_message(message.chat.id, "🔢 Iltimos, faqat raqamlardan iborat bo'lgan Linebet ID raqamingizni yuboring!")
        return

    if message.text == "🚀 Signal olish":
        if user_id not in kunlik_limit:
            kunlik_limit[user_id] = 5
            
        if kunlik_limit[user_id] <= 0:
            bot.send_message(message.chat.id, "⚠️ Bugungi bepul signalingiz tugadi! Ertaga qayta urinib ko'ring yoki VIP guruhga qo'shiling. 💎")
            return
            
        kunlik_limit[user_id] -= 1
        
        msg = bot.send_message(message.chat.id, "🤖 <b>Linebet AI Algoritmi tahlil qilmoqda...</b>")
        time.sleep(1)
        bot.edit_message_text("⏳ Aviator grafiklari yuklanmoqda: [■□□□□□□□□□] 15%", message.chat.id, msg.message_id)
        time.sleep(1)
        bot.edit_message_text("⚡ Koeffitsiyent aniqlanmoqda: [■■■■■■■□□□] 75%", message.chat.id, msg.message_id)
        time.sleep(1)
        
        koef = round(random.uniform(1.2, 6.8), 2)
        natija_matn = f"🎯 <b>LINEBET AVIATOR SIGNAL:</b>\n\n🚀 Kutilayotgan koeffitsiyent: <pre>{koef}x</pre>\n\n⚠️ <i>Samolyot uchib ketishidan oldin pulingizni yechib oling!</i>\n📉 Bugungi signalingiz qoldi: {kunlik_limit[user_id]}"
        bot.edit_message_text(natija_matn, message.chat.id, msg.message_id)

    elif message.text == "📊 Statistika":
        bot.send_message(message.chat.id, f"📊 <b>Bugungi Linebet Aviator statistikasi:</b>\n\n✅ Signallar aniqligi: 95.4%\n🔥 Aktiv foydalanuvchilar: 1,850+\n🎁 Oxirgi 1 soatda eng yuqori natija: 14.5x ushlandi.")
        
    elif message.text == "ℹ️ Yordam":
        bot.send_message(message.chat.id, f"📌 Savollaringiz bo'lsa yoki VIP guruhga qo'shilishni istasangiz, adminimizga yozing.")

if __name__ == "__main__":
    print("Bot muvaffaqiyatli ishga tushdi...")
    bot.infinity_polling()
    
