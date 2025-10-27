#!/usr/bin/env python3
# aviator_signal_bot.py
# Professional Auto-Signal + Statistik Aviator tahlilchi bot

import telebot
from telebot import types
import threading
import time
import random
import json
import os
from datetime import datetime
import statistics

# ================== CONFIG ==================
TOKEN = "7253804878:AAGPZL3t3ugKYgeWDKB8_vvGG2KJvM_-AaA"  # <-- o'zingizni tokenni shu yerga qo'ying
ACCESS_KEY = "230220004848"  # aktivatsiya kodi
USERS_FILE = "verified_users.json"
GAME_HISTORY = "game_history.json"
USER_SIGNALS = "user_signals.json"
SETTINGS_FILE = "settings.json"
# Adminlar: telegram chat id larini kiriting (raqam). Misol: [123456789]
ADMIN_IDS = [123456789]  # <-- shu yerga admin chat id qo'ying
# ============================================

# ======== Fayl yaratish / boshlang'ich sozlash ========
for p in [USERS_FILE, GAME_HISTORY, USER_SIGNALS, SETTINGS_FILE]:
    if not os.path.exists(p):
        with open(p, "w") as f:
            if p == SETTINGS_FILE:
                json.dump({"auto_signals": False, "cycle_min_s": 90, "cycle_max_s": 120}, f, indent=4)
            else:
                json.dump([], f, indent=4)

# ======== Yordamchi funksiyalar ========
file_lock = threading.Lock()

def safe_load_json(path):
    with file_lock:
        try:
            with open(path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

def safe_save_json(path, data):
    with file_lock:
        with open(path, "w") as f:
            json.dump(data, f, indent=4)

def append_game(kf):
    history = safe_load_json(GAME_HISTORY)
    history.append({"kf": kf, "time": datetime.now().isoformat()})
    # saqlash: oxirgi 100 ta
    if len(history) > 100:
        history = history[-100:]
    safe_save_json(GAME_HISTORY, history)

def record_user_signal(user_id, signal_text):
    store = safe_load_json(USER_SIGNALS)
    store.append({
        "user_id": user_id,
        "time": datetime.now().isoformat(),
        "signal": signal_text
    })
    # limit saqlash
    if len(store) > 1000:
        store = store[-1000:]
    safe_save_json(USER_SIGNALS, store)

def get_settings():
    s = safe_load_json(SETTINGS_FILE)
    # qaytadi dict
    if isinstance(s, dict):
        return s
    else:
        return {"auto_signals": False, "cycle_min_s": 90, "cycle_max_s": 120}

def save_settings(s):
    safe_save_json(SETTINGS_FILE, s)

# ======== Bot obyekt ========
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# ======== KF generator (Aviatorga o'xshash simulyatsiya) ========
def generate_kf_sim():
    r = random.random()
    if r < 0.70:
        return round(random.uniform(1.00, 2.50), 2)
    elif r < 0.90:
        return round(random.uniform(2.51, 5.00), 2)
    else:
        return round(random.uniform(5.01, 12.00), 2)

# ======== Tahlil algoritmi ========
def analyze_list_and_build_signal(kf_list):
    """
    kiruvchi: list of floats (oxirgi N kf)
    chiqish: (summary_text, signal_text)
    Signal: raqamlarni aytmaydi, faqat toifadagi prognoz: 
      - "1 dan 2 gacha asosan" -> keyingi 2+ mumkin
      - "2 dan baland ko'proq" -> keyingi 3+ ehtimoli
      - va hokazo
    """
    n = len(kf_list)
    if n == 0:
        return ("🔹 Ma'lumot mavjud emas.", "🔸 Ma'lumot yo'q. Iltimos 10-20 ta KF yuboring yoki avtomatik signalni kuting.")

    # toifalarga bo'lish
    t1 = len([x for x in kf_list if x < 2.0])       # 1-2
    t2 = len([x for x in kf_list if 2.0 <= x < 3.0])# 2-3
    t3 = len([x for x in kf_list if 3.0 <= x < 4.0])# 3-4
    t4 = len([x for x in kf_list if x >= 4.0])      # 4+

    avg = round(statistics.mean(kf_list), 2) if n>0 else 0

    summary = (
        f"📊 <b>Tahlil (so'nggi {n} ta):</b>\n"
        f"🔹 1.0–1.99: {t1} marta\n"
        f"🔹 2.0–2.99: {t2} marta\n"
        f"🔹 3.0–3.99: {t3} marta\n"
        f"🔹 4.0+: {t4} marta\n"
        f"📈 O'rtacha KF: <b>{avg}</b>\n"
    )

    # Sodda qoidalar asosida signal yaratish (soniyu foydalanuvchi so'roviga mos)
    signal = ""
    total = n

    # qoidalarga prioritet beramiz:
    if t1 / total >= 0.6:
        # juda ko'p past
        signal = "🔺 Oxirgi o'yinlarda 1–2 oralig'ida natijalar ko'p chiqmoqda — <b>ehtimol keyingi raund 2 dan baland</b> bo'lishi mumkin."
    elif t4 >= 3:
        # yaqinda bir nechta 4+ bo'lgan
        signal = "⚠️ So'nggi o'yinlarda bir nechta 4+ ko'rsatkichlari mavjud — <b>keyingi raund ehtimol past (1–2) bo'lishi mumkin</b>."
    elif (t2 + t3) / total >= 0.6:
        signal = "🔥 O'rtacha va yuqori (2–4) ko'rsatkichlar dominant — <b>keyingi raund 3 dan baland bo'lishi ehtimoli bor (lekin 4+ kam)</b>."
    else:
        # aralash holat
        # qaror: agar avg past bo'lsa 2+, agar avg yuqori bo'lsa ehtiyot
        if avg < 2.2:
            signal = "🔹 Aralash, ammo o'rtacha past — <b>2 dan baland chiqish ehtimoli mavjud</b>."
        elif avg >= 3.0:
            signal = "⚠️ O'rtacha yuqori — oldingi katta natijalar tashqari, <b>keyingi raund pastga tushish xavfi bor</b>."
        else:
            signal = "♻️ Neytral holat — <b>2–3 oralig'ida</b> natija kutish tavsiya etiladi."

    # Qisqa tavsiya shakli (foydalanuvchi so‘ragan formatga yaqin)
    # Misol: "1 dan 2 dan baland uchmadi yoki 2 dan baland uchadi yoki 3 dan baland 4 gacha Busa Yech"
    # Biz: aniq raqam aytmaymiz, balki kategoriyalar yordamida
    if "2 dan baland" in signal or "2 dan baland" in summary:
        pass

    return summary, signal

# ======== Avtomatik signal generatsiyasi (fon oqimi) ========
def auto_signal_worker():
    """
    Bu funksiya:
      - fon rejimida o'yin roundlarini generatsiya qiladi (generate_kf_sim)
      - yangi round qo'shib boradi (GAME_HISTORY)
      - va agar settings['auto_signals'] True bo'lsa, tahlil qilib, barcha verified foydalanuvchilarga signal yuboradi
      - oraliq vaqt: SETTINGS cycle_min_s..cycle_max_s
    """
    while True:
        # settingsni o'qish
        settings = get_settings()
        wait_s = random.randint(settings.get("cycle_min_s", 90), settings.get("cycle_max_s", 120))

        # yangi KF
        kf = generate_kf_sim()
        append_game(kf)
        history = safe_load_json(GAME_HISTORY)

        # agar auto_signals yoqilgan bo'lsa -> tahlil va yuborish
        if settings.get("auto_signals", False):
            # tahlil uchun so'nggi 20 ta
            recent = [h["kf"] for h in history[-20:]]
            summary, signal = analyze_list_and_build_signal(recent)
            # yuborish matni: o'yin hisobi va signal (rasim yo'q)
            text = (
                f"⏱️ <b>Auto-signal</b>\n"
                f"🕒 Round: {datetime.now().strftime('%H:%M:%S')}\n"
                f"{summary}\n"
                f"🧠 <b>Tavsiya:</b>\n{signal}\n"
                f"🔁 Agar xohlasangiz, /signal orqali yoki 'KF: ...' yuborib o'zingiz ham tahlil olishingiz mumkin."
            )

            # kimlarga yuborish
            users = safe_load_json(USERS_FILE)
            for uid in users:
                try:
                    bot.send_message(uid, text)
                except Exception:
                    # muammo bo'lsa davom etamiz
                    pass

            # record every broadcast (optional)
            record_user_signal("AUTO_BROADCAST", f"{datetime.now().isoformat()} | {signal}")

        # konsol uchun print
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Simulated round: {kf}x. Next in {wait_s}s. Auto:{settings.get('auto_signals')}")
        time.sleep(wait_s)

# ======== Bot komandalar va xabarlarni qayta ishlash ========

@bot.message_handler(commands=['start'])
def cmd_start(message):
    txt = (
        "👋 Salom! Aviator tahlilchi botga xush kelibsiz.\n\n"
        "📌 Foydalanish:\n"
        "1) Admindan aktivatsiya kodini olganingizdan so'ng, ACCESS_KEY ni yuboring (faqat kodni yuboring).\n"
        "2) Aktiv bo'lsangiz, /signal bilan so'nggi avtomatik tarix asosida tahlil olishingiz mumkin.\n"
        "3) Istasangiz, oxirgi 10–30 ta KF ni to'g'ridan-to'g'ri yuboring formatda:\n"
        "   KF: 1.25,1.80,2.30,1.15,3.50, ...\n"
        "4) /mysignals — sizga yuborilgan signal tarixini ko'rish.\n\n"
        "🔒 Eslatma: Bu bot haqiqiy o'yin serveriga ulanmaydi, faqat statistik model va foydalanuvchi ma'lumotlari asosida tahlil beradi."
    )
    bot.send_message(message.chat.id, txt)

@bot.message_handler(commands=['signal'])
def cmd_signal(message):
    user_id = message.chat.id
    users = safe_load_json(USERS_FILE)
    if user_id not in users:
        bot.send_message(user_id, "⚠️ Siz hali aktivatsiya qilinmagansiz. Iltimos admin orqali kod oling.")
        return
    history = safe_load_json(GAME_HISTORY)
    recent = [h["kf"] for h in history[-20:]] if history else []
    summary, signal = analyze_list_and_build_signal(recent)
    out = f"📡 <b>So'nggi auto-tahlil:</b>\n\n{summary}\n🧠 <b>Tavsiya:</b>\n{signal}"
    bot.send_message(user_id, out)
    record_user_signal(user_id, signal)

@bot.message_handler(commands=['mysignals'])
def cmd_mysignals(message):
    user_id = message.chat.id
    store = safe_load_json(USER_SIGNALS)
    # filter user entries
    my = [s for s in store if s.get("user_id") == user_id]
    if not my:
        bot.send_message(user_id, "🔎 Sizga hech qanday signal yuborilmagan yoki tarix topilmadi.")
        return
    # so'nggi 10 yozuv
    last = my[-10:]
    text = "📜 So'nggi signallar:\n\n"
    for it in last:
        t = it.get("time", "")[:19].replace("T", " ")
        text += f"{t} — {it.get('signal')}\n\n"
    bot.send_message(user_id, text)

# Admin: /on /off /stat
@bot.message_handler(commands=['on','off','stat'])
def admin_commands(message):
    user_id = message.chat.id
    if user_id not in ADMIN_IDS:
        bot.send_message(user_id, "❌ Siz admin emassiz.")
        return
    cmd = message.text.strip().lower()
    settings = get_settings()
    if cmd == "/on":
        settings["auto_signals"] = True
        save_settings(settings)
        bot.send_message(user_id, "✅ Auto-signallar yoqildi.")
    elif cmd == "/off":
        settings["auto_signals"] = False
        save_settings(settings)
        bot.send_message(user_id, "⛔ Auto-signallar o‘chirildi.")
    elif cmd == "/stat":
        users = safe_load_json(USERS_FILE)
        history = safe_load_json(GAME_HISTORY)
        settings = get_settings()
        stext = (
            f"📊 Statistika:\n"
            f" - Tasdiqlangan foydalanuvchilar: {len(users)}\n"
            f" - Saqlangan o'yinlar: {len(history)}\n"
            f" - Auto-signallar: {settings.get('auto_signals')}\n"
            f" - Cycle interval: {settings.get('cycle_min_s')}–{settings.get('cycle_max_s')} s\n"
        )
        bot.send_message(user_id, stext)

# Aktivatsiya — user ACCESS_KEY yuborsa
@bot.message_handler(func=lambda m: m.text is not None and m.text.strip() == ACCESS_KEY)
def activate_user(message):
    user_id = message.chat.id
    users = safe_load_json(USERS_FILE)
    if user_id in users:
        bot.send_message(user_id, "⚡ Siz allaqachon aktivatsiya qilingansiz.")
        return
    users.append(user_id)
    safe_save_json(USERS_FILE, users)
    bot.send_message(user_id, "✅ Bot aktivatsiya qilindi! /signal bilan tahlil oling.")
    # welcome hint
    bot.send_message(user_id, "🔎 Agar oxirgi 20 ta KF ni yuborsangiz 'KF: ...' formatida to'g'ridan-to'g'ri tahlil olasiz.")

# Foydalanuvchi to'g'ridan-to'g'ri KF ro'yxatini yubordi: "KF: 1.25,1.80,..."
@bot.message_handler(func=lambda m: m.text is not None and m.text.strip().lower().startswith("kf:"))
def user_provide_kf(message):
    user_id = message.chat.id
    users = safe_load_json(USERS_FILE)
    if user_id not in users:
        bot.send_message(user_id, "⚠️ Siz hali aktivatsiya qilinmagansiz. Iltimos admindan kod oling.")
        return
    payload = message.text.strip()[3:]  # 'KF:' dan keyin
    # tozalash
    payload = payload.replace("\n", " ").replace(";", ",")
    # split va float
    parts = [p.strip() for p in payload.split(",") if p.strip()]
    try:
        numbers = [float(p) for p in parts]
    except Exception:
        bot.send_message(user_id, "⚠️ Noto'g'ri format. Iltimos: KF: 1.25,1.80,2.30,...")
        return
    if len(numbers) < 10:
        bot.send_message(user_id, "⚠️ Kamida 10 ta KF yuboring (ideal — 20 ta).")
        return
    if len(numbers) > 100:
        numbers = numbers[-100:]
    # analiz
    summary, signal = analyze_list_and_build_signal(numbers[-20:])  # oxirgi 20 ta tahlil qilamiz
    out = f"🔎 <b>Foydalanuvchi yuborgan KF asosida tahlil:</b>\n\n{summary}\n🧠 <b>Tavsiya:</b>\n{signal}"
    bot.send_message(user_id, out)
    record_user_signal(user_id, signal)

# Fallback: boshqa matnlar
@bot.message_handler(func=lambda m: True)
def fallback_handler(message):
    text = message.text.strip()
    # Agar foydalanuvchi sondan iborat ro'yxat yuborsa (vergul bilan)
    # lekin u "KF:" bilan boshlamasa ham sinab ko'ramiz
    maybe_parts = [p.strip() for p in text.replace("\n"," ").replace(";",",").split(",") if p.strip()]
    is_all_numbers = True
    nums = []
    if 5 <= len(maybe_parts) <= 50:
        for p in maybe_parts:
            try:
                nums.append(float(p))
            except:
                is_all_numbers = False
                break
    else:
        is_all_numbers = False

    if is_all_numbers:
        # agar foydalanuvchi aktyiv bo'lsa tahlil qilamiz
        user_id = message.chat.id
        users = safe_load_json(USERS_FILE)
        if user_id not in users:
            bot.send_message(user_id, "⚠️ Siz hali aktivatsiya qilinmagansiz. Iltimos admindan kod oling.")
            return
        if len(nums) < 10:
            bot.send_message(user_id, "⚠️ Kamida 10 ta KF yuboring (ideal — 20 ta).")
            return
        summary, signal = analyze_list_and_build_signal(nums[-20:])
        out = f"🔎 <b>Yuborgan KF asosida tahlil:</b>\n\n{summary}\n🧠 <b>Tavsiya:</b>\n{signal}"
        bot.send_message(user_id, out)
        record_user_signal(user_id, signal)
        return

    # Akhirida umumiy ko'rsatma
    bot.send_message(message.chat.id,
                     "❓ Men tushunmadim. Qo'llanma:\n"
                     "- Aktivatsiya kodi yuboring (faqat kodni yuboring).\n"
                     "- /signal — so'nggi avtomatik tahlilni ko'rish.\n"
                     "- KF: 1.25,1.80,...  — o'zingiz oxirgi natijalarni yuboring va batafsil tahlil oling.\n"
                     "- /mysignals — sizga yuborilgan signallar tarixini ko'rish.")

# ======== Fon oqimni ishga tushiramiz ========
threading.Thread(target=auto_signal_worker, daemon=True).start()

# ======== Bot polling ========
if __name__ == "__main__":
    print("Bot ishga tushmoqda...")
    bot.polling(none_stop=True)
