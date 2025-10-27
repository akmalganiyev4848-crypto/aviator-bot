#!/usr/bin/env python3
# main.py
# Aviator Auto-Signal + Statistik tahlilchi bot (final, merged)
# - Uses environment variables if available (recommended for Railway/GitHub)
# - Place TOKEN, ACCESS_KEY, ADMIN_IDS in Railway env (or in a .env locally)

import os
import telebot
from telebot import types
import threading
import time
import random
import json
from datetime import datetime
import statistics

# ---------------- CONFIG (env-first) ----------------
# put TOKEN as Railway secret or in .env locally
TOKEN = os.getenv("TOKEN", "7253804878:AAGPZL3t3ugKYgeWDKB8_vvGG2KJvM_-AaA")
ACCESS_KEY = os.getenv("ACCESS_KEY", "230220004848")

# ADMIN_IDS as comma-separated (e.g. "12345,67890")
_admins_env = os.getenv("ADMIN_IDS", "")
try:
    if _admins_env.strip():
        ADMIN_IDS = [int(x.strip()) for x in _admins_env.split(",") if x.strip()]
    else:
        # fallback default (edit here if you prefer)
        ADMIN_IDS = []
except Exception:
    ADMIN_IDS = []

# Files (note: Railway ephemeral FS warning)
USERS_FILE = os.getenv("USERS_FILE", "verified_users.json")
GAME_HISTORY = os.getenv("GAME_HISTORY", "game_history.json")
USER_SIGNALS = os.getenv("USER_SIGNALS", "user_signals.json")
SETTINGS_FILE = os.getenv("SETTINGS_FILE", "settings.json")

# Promo / branding (your fixed values)
PROMO_CODE = "AKIBET777"
REG_LINK = "https://lb-aff.com/L?tag=d_4114394m_22611c_site&site=4114394&ad=22611&r=registration"
APK_LINK = "https://lb-aff.com/L?tag=d_4114394m_66803c_apk1&site=4114394&ad=66803"
CHANNEL_LINK = "https://t.me/aviatorwinuzbot"
ADMIN_USERNAME = "@akibet1"

# ----------------- Ensure files exist -----------------
_init_files = [USERS_FILE, GAME_HISTORY, USER_SIGNALS, SETTINGS_FILE]
for p in _init_files:
    if not os.path.exists(p):
        try:
            with open(p, "w", encoding="utf-8") as f:
                if p == SETTINGS_FILE:
                    json.dump({"auto_signals": False, "cycle_min_s": 90, "cycle_max_s": 120}, f, indent=4)
                else:
                    json.dump([], f, indent=4)
        except Exception as e:
            print(f"[WARN] Cannot create file {p}: {e}")

# ----------------- Thread-safe JSON I/O -----------------
_file_lock = threading.Lock()

def safe_load_json(path):
    with _file_lock:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

def safe_save_json(path, data):
    with _file_lock:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[ERROR] save {path}: {e}")

def append_game(kf):
    history = safe_load_json(GAME_HISTORY)
    history.append({"kf": kf, "time": datetime.now().isoformat()})
    if len(history) > 200:
        history = history[-200:]
    safe_save_json(GAME_HISTORY, history)

def record_user_signal(user_id, signal_text):
    store = safe_load_json(USER_SIGNALS)
    store.append({"user_id": user_id, "time": datetime.now().isoformat(), "signal": signal_text})
    if len(store) > 2000:
        store = store[-2000:]
    safe_save_json(USER_SIGNALS, store)

def get_settings():
    s = safe_load_json(SETTINGS_FILE)
    if isinstance(s, dict):
        return s
    return {"auto_signals": False, "cycle_min_s": 90, "cycle_max_s": 120}

def save_settings(s):
    safe_save_json(SETTINGS_FILE, s)

# ----------------- Bot init -----------------
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# ----------------- KF simulator -----------------
def generate_kf_sim():
    r = random.random()
    if r < 0.70:
        return round(random.uniform(1.00, 2.50), 2)
    elif r < 0.90:
        return round(random.uniform(2.51, 5.00), 2)
    else:
        return round(random.uniform(5.01, 12.00), 2)

# ----------------- Analysis algorithm -----------------
def analyze_list_and_build_signal(kf_list):
    n = len(kf_list)
    if n == 0:
        return ("🔹 Ma'lumot mavjud emas.", "🔸 Ma'lumot yo'q. Iltimos 10-20 ta KF yuboring yoki avtomatik signalni kuting.")
    t1 = len([x for x in kf_list if x < 2.0])
    t2 = len([x for x in kf_list if 2.0 <= x < 3.0])
    t3 = len([x for x in kf_list if 3.0 <= x < 4.0])
    t4 = len([x for x in kf_list if x >= 4.0])
    avg = round(statistics.mean(kf_list), 2) if n > 0 else 0
    summary = (
        f"📊 <b>Tahlil (so'nggi {n} ta):</b>\n"
        f"🔹 1.0–1.99: {t1} marta\n"
        f"🔹 2.0–2.99: {t2} marta\n"
        f"🔹 3.0–3.99: {t3} marta\n"
        f"🔹 4.0+: {t4} marta\n"
        f"📈 O'rtacha KF: <b>{avg}</b>\n"
    )
    total = n
    signal = ""
    try:
        if total == 0:
            signal = "🔸 Ma'lumot yetarli emas."
        elif t1 / total >= 0.6:
            signal = "🔺 Oxirgi o'yinlarda 1–2 oralig'ida ko'p natijalar — <b>ehtimol keyingi raund 2 dan baland bo'lishi mumkin</b>."
        elif t4 >= 3:
            signal = "⚠️ Yaqinda bir nechta 4+ natija kuzatildi — <b>keyingi raund past (1–2) bo'lishi mumkin</b>."
        elif (t2 + t3) / total >= 0.6:
            signal = "🔥 O'rtacha va yuqori (2–4) ko'rsatkichlar dominant — <b>keyingi raund 3 dan baland bo'lishi ehtimoli bor (lekin 4+ kam)</b>."
        else:
            if avg < 2.2:
                signal = "🔹 Aralash, ammo o'rtacha past — <b>2 dan baland chiqish ehtimoli mavjud</b>."
            elif avg >= 3.0:
                signal = "⚠️ O'rtacha yuqori — <b>keyingi raund pastga tushish xavfi bor</b>."
            else:
                signal = "♻️ Neytral holat — <b>2–3 oralig'ida</b> natija kutish tavsiya etiladi."
    except Exception as e:
        signal = "🔸 Tahlilda xato, qayta urinib ko'ring."
        print("[ERROR] analyze:", e)
    return summary, signal

# ----------------- Auto-signal worker -----------------
def auto_signal_worker():
    while True:
        settings = get_settings()
        wait_s = random.randint(settings.get("cycle_min_s", 90), settings.get("cycle_max_s", 120))
        # generate and append simulated round
        kf = generate_kf_sim()
        append_game(kf)
        history = safe_load_json(GAME_HISTORY)
        if settings.get("auto_signals", False):
            recent = [h["kf"] for h in history[-20:]]
            summary, signal = analyze_list_and_build_signal(recent)
            text = (
                f"⏱️ <b>Auto-signal</b>\n"
                f"🕒 Round: {datetime.now().strftime('%H:%M:%S')}\n"
                f"{summary}\n"
                f"🧠 <b>Tavsiya:</b>\n{signal}\n\n"
                f"🔹 Promo: <b>{PROMO_CODE}</b>\n"
                f"🔗 Ro'yxat: {REG_LINK}\n"
                f"📲 APK: {APK_LINK}\n"
                f"👤 Admin: {ADMIN_USERNAME}\n"
                f"🤖 Kanal: {CHANNEL_LINK}"
            )
            # send to verified users
            users = safe_load_json(USERS_FILE)
            for uid in users:
                try:
                    bot.send_message(uid, text)
                except Exception:
                    # ignore send errors (user blocked bot, etc.)
                    pass
            record_user_signal("AUTO_BROADCAST", f"{datetime.now().isoformat()} | {signal}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Simulated round: {kf}x. Next in {wait_s}s. Auto:{settings.get('auto_signals')}")
        time.sleep(wait_s)

# ----------------- /start with promo & inline buttons -----------------
@bot.message_handler(commands=['start'])
def cmd_start(message):
    chat_id = message.chat.id
    txt = (
        "👋 <b>Salom!</b> Aviator tahlilchi botga xush kelibsiz.\n\n"
        "📌 <b>Foydalanish:</b>\n"
        "1️⃣ Admindan aktivatsiya kodini oling va shu yerga yuboring.\n"
        "2️⃣ Aktiv bo‘lgach, /signal buyrug‘i orqali so‘nggi o‘yinlar tahlilini oling.\n"
        "3️⃣ Yoki o‘zingizning so‘nggi 10–30 ta KF’ni yuboring formatda:\n"
        "   <code>KF: 1.25, 1.80, 2.30, 1.15, 3.50, ...</code>\n"
        "4️⃣ /mysignals — sizga yuborilgan signal tarixini ko‘rish.\n\n"
        "🔒 <i>Eslatma:</i> Bot real o‘yin serveriga ulanmaydi; faqat statistik model asosida tavsiya beradi.\n\n"
        f"💎 <b>Rasmiy havolalar:</b>\n"
        f"🔗 Ro'yxatdan o'tish: {REG_LINK}\n"
        f"📲 APK: {APK_LINK}\n"
        f"🤖 Kanal: {CHANNEL_LINK}\n"
        f"👨‍💼 Admin: {ADMIN_USERNAME}\n\n"
        f"🎁 <b>Promo kod:</b> <code>{PROMO_CODE}</code>\n"
    )
    # Inline keyboard with quick links and copy promo
    kb = types.InlineKeyboardMarkup()
    kb_row = [
        types.InlineKeyboardButton("🔗 Ro'yxat", url=REG_LINK),
        types.InlineKeyboardButton("📲 APK", url=APK_LINK)
    ]
    kb.add(*kb_row)
    kb.add(types.InlineKeyboardButton("🎁 Promo nusxa", callback_data="copy_promo"))
    kb.add(types.InlineKeyboardButton("🤖 Kanal", url=CHANNEL_LINK))
    bot.send_message(chat_id, txt, parse_mode="HTML", disable_web_page_preview=True, reply_markup=kb)

# handle "copy_promo" callback: send promo as plain text so user can copy
@bot.callback_query_handler(func=lambda call: call.data == "copy_promo")
def callback_copy_promo(call):
    try:
        bot.answer_callback_query(call.id, text="Promo kodi yuborildi (nusxa uchun bosib ushlab ko‘ring).", show_alert=False)
        bot.send_message(call.message.chat.id, f"🎁 Promo kodi: <code>{PROMO_CODE}</code>\n\nAdmin: {ADMIN_USERNAME}", parse_mode="HTML")
    except Exception:
        pass

# ----------------- /signal command -----------------
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

# ----------------- /mysignals -----------------
@bot.message_handler(commands=['mysignals'])
def cmd_mysignals(message):
    user_id = message.chat.id
    store = safe_load_json(USER_SIGNALS)
    my = [s for s in store if s.get("user_id") == user_id]
    if not my:
        bot.send_message(user_id, "🔎 Sizga hech qanday signal yuborilmagan yoki tarix topilmadi.")
        return
    last = my[-10:]
    text = "📜 So'nggi signallar:\n\n"
    for it in last:
        t = it.get("time", "")[:19].replace("T", " ")
        text += f"{t} — {it.get('signal')}\n\n"
    bot.send_message(user_id, text)

# ----------------- Admin commands (/on /off /stat /setinterval) -----------------
@bot.message_handler(commands=['on','off','stat','setinterval'])
def admin_commands(message):
    user_id = message.chat.id
    if user_id not in ADMIN_IDS:
        bot.send_message(user_id, "❌ Siz admin emassiz.")
        return
    cmd = message.text.strip().lower()
    settings = get_settings()
    if cmd.startswith("/on"):
        settings["auto_signals"] = True
        save_settings(settings)
        bot.send_message(user_id, "✅ Auto-signallar yoqildi.")
    elif cmd.startswith("/off"):
        settings["auto_signals"] = False
        save_settings(settings)
        bot.send_message(user_id, "⛔ Auto-signallar o‘chirildi.")
    elif cmd.startswith("/stat"):
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
    elif cmd.startswith("/setinterval"):
        # format: /setinterval 60 90
        parts = cmd.split()
        if len(parts) == 3:
            try:
                mn = int(parts[1]); mx = int(parts[2])
                settings["cycle_min_s"] = max(10, mn)
                settings["cycle_max_s"] = max(settings["cycle_min_s"], mx)
                save_settings(settings)
                bot.send_message(user_id, f"✅ Interval yangilandi: {settings['cycle_min_s']}–{settings['cycle_max_s']} s")
            except:
                bot.send_message(user_id, "⚠️ Noto'g'ri format. Misol: /setinterval 60 120")
        else:
            bot.send_message(user_id, "⚠️ Foydalanish: /setinterval MIN MAX")

# ----------------- Activation by ACCESS_KEY -----------------
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
    bot.send_message(user_id, f"🔎 Agar oxirgi 20 ta KF ni yuborsangiz 'KF: ...' formatida tahlil olasiz.\n🎁 Promo kodi: <code>{PROMO_CODE}</code>", parse_mode="HTML")

# ----------------- User-provided KF parsing (KF: 1.2,2.3,...) -----------------
@bot.message_handler(func=lambda m: m.text is not None and m.text.strip().lower().startswith("kf:"))
def user_provide_kf(message):
    user_id = message.chat.id
    users = safe_load_json(USERS_FILE)
    if user_id not in users:
        bot.send_message(user_id, "⚠️ Siz hali aktivatsiya qilinmagansiz. Iltimos admindan kod oling.")
        return
    payload = message.text.strip()[3:]
    payload = payload.replace("\n", " ").replace(";", ",")
    parts = [p.strip() for p in payload.split(",") if p.strip()]
    try:
        numbers = [float(p) for p in parts]
    except Exception:
        bot.send_message(user_id, "⚠️ Noto'g'ri format. Iltimos: KF: 1.25,1.80,2.30,...")
        return
    if len(numbers) < 10:
        bot.send_message(user_id, "⚠️ Kamida 10 ta KF yuboring (ideal — 20 ta).")
        return
    if len(numbers) > 200:
        numbers = numbers[-200:]
    summary, signal = analyze_list_and_build_signal(numbers[-20:])
    out = f"🔎 <b>Foydalanuvchi yuborgan KF asosida tahlil:</b>\n\n{summary}\n🧠 <b>Tavsiya:</b>\n{signal}"
    bot.send_message(user_id, out)
    record_user_signal(user_id, signal)

# ----------------- Generic numeric-list fallback -----------------
@bot.message_handler(func=lambda m: True)
def fallback_handler(message):
    text = (message.text or "").strip()
    maybe_parts = [p.strip() for p in text.replace("\n"," ").replace(";",",").split(",") if p.strip()]
    is_all_numbers = True
    nums = []
    if 5 <= len(maybe_parts) <= 500:
        for p in maybe_parts:
            try:
                nums.append(float(p))
            except:
                is_all_numbers = False
                break
    else:
        is_all_numbers = False

    if is_all_numbers:
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

    # default help
    bot.send_message(message.chat.id,
        "❓ Men tushunmadim. Qo'llanma:\n"
        "- Aktivatsiya kodi yuboring (faqat kodni yuboring).\n"
        "- /signal — so'nggi avtomatik tahlilni ko'rish.\n"
        "- KF: 1.25,1.80,...  — o'zingiz oxirgi natijalarni yuboring va batafsil tahlil oling.\n"
        "- /mysignals — sizga yuborilgan signallar tarixini ko'rish.")

# ----------------- Start background worker -----------------
threading.Thread(target=auto_signal_worker, daemon=True).start()

# ----------------- Robust polling loop -----------------
def run_bot_polling():
    while True:
        try:
            print("Bot polling started...")
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"[ERROR] Bot polling crashed: {e}. Restarting in 5s...")
            time.sleep(5)

if __name__ == "__main__":
    run_bot_polling()
