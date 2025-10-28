#!/usr/bin/env python3
# main.py - Aviator bot (merged, improved)
# Features:
# - Admin (@akibet) can generate one-time activation codes (/genkey)
# - Per-user KF storage (user_kf.json)
# - Smart append/replace behavior for added KF lists
# - OCR from screenshot images to extract KF values
# - Signal menu (view last 20, add text, add photo)
# - Thread-safe JSON IO, logging, promo links preserved

import os
import json
import threading
import time
import random
import string
import logging
import re

from datetime import datetime
from PIL import Image, ImageFilter, ImageOps
import pytesseract
import telebot
from telebot import types

# ---------------- Config ----------------
TOKEN = os.getenv("TOKEN", "7253804878:AAGPZL3t3ugKYgeWDKB8_vvGG2KJvM_-AaA")
ADMIN_USERNAME = "akibet"    # admin username WITHOUT '@' (as requested)
PROMO_CODE = "AKIBET777"
REG_LINK = "https://lb-aff.com/L?tag=d_4114394m_22611c_site&site=4114394&ad=22611&r=registration"
APK_LINK = "https://lb-aff.com/L?tag=d_4114394m_66803c_apk1&site=4114394&ad=66803"
CHANNEL_LINK = "https://t.me/aviatorwinuzbot"
ADMIN_USERNAME_DISPLAY = "@akibet"

# Files
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "verified_users.json")   # list of user dicts
ACT_KEYS_FILE = os.path.join(DATA_DIR, "activation_keys.json")
USER_KF_FILE = os.path.join(DATA_DIR, "user_kf.json")        # dict of user_id -> [kf,...]
USER_SIGNALS = os.path.join(DATA_DIR, "user_signals.json")
GAME_HISTORY = os.path.join(DATA_DIR, "game_history.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")

os.makedirs(DATA_DIR, exist_ok=True)

# ---------------- Logging ----------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ---------------- Thread-safe JSON IO ----------------
_file_lock = threading.Lock()

def safe_load(path, default):
    with _file_lock:
        try:
            if not os.path.exists(path):
                return default
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logging.error("safe_load error %s: %s", path, e)
            return default

def safe_save(path, data):
    with _file_lock:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logging.error("safe_save error %s: %s", path, e)

# Ensure files exist
if not os.path.exists(SETTINGS_FILE):
    safe_save(SETTINGS_FILE, {"auto_signals": False, "cycle_min_s": 90, "cycle_max_s": 120})
for p, d in [(USERS_FILE, []), (ACT_KEYS_FILE, {}), (USER_KF_FILE, {}), (USER_SIGNALS, []), (GAME_HISTORY, [])]:
    if not os.path.exists(p):
        safe_save(p, d)

# ---------------- Bot init ----------------
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# ---------------- Helpers: activation keys ----------------
def gen_key(length=8):
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(random.choice(alphabet) for _ in range(length))

def gen_keys(count=1, created_by=None):
    keys = safe_load(ACT_KEYS_FILE, {})
    out = []
    for _ in range(count):
        for _ in range(10):
            k = gen_key(8)
            if k not in keys:
                break
        keys[k] = {
            "used": False,
            "created_by": created_by,
            "created_at": datetime.now().isoformat(),
            "used_by": None,
            "used_at": None
        }
        out.append(k)
    safe_save(ACT_KEYS_FILE, keys)
    return out

def using_key(key, user_id):
    keys = safe_load(ACT_KEYS_FILE, {})
    info = keys.get(key)
    if not info:
        return False, "NOT_FOUND"
    if info.get("used"):
        return False, "ALREADY"
    info["used"] = True
    info["used_by"] = int(user_id)
    info["used_at"] = datetime.now().isoformat()
    keys[key] = info
    safe_save(ACT_KEYS_FILE, keys)
    return True, "OK"

def key_info(key):
    keys = safe_load(ACT_KEYS_FILE, {})
    return keys.get(key)

# ---------------- Helpers: users ----------------
def get_all_users():
    return safe_load(USERS_FILE, [])

def add_verified_user(user_id, username, used_key):
    users = get_all_users()
    # avoid duplicates
    for u in users:
        if int(u.get("id")) == int(user_id):
            return False
    users.append({
        "id": int(user_id),
        "username": username,
        "activated_at": datetime.now().isoformat(),
        "key": used_key,
        "promo_confirmed": False,
        "promo_confirmed_at": None
    })
    safe_save(USERS_FILE, users)
    return True

def set_promo_confirmed(user_id):
    users = get_all_users()
    changed = False
    for u in users:
        if int(u.get("id")) == int(user_id):
            u["promo_confirmed"] = True
            u["promo_confirmed_at"] = datetime.now().isoformat()
            changed = True
            break
    if changed:
        safe_save(USERS_FILE, users)
    return changed

def is_user_activated(user_id):
    users = get_all_users()
    return any(int(u.get("id")) == int(user_id) for u in users)

# ---------------- Helpers: per-user KF ----------------
def get_all_user_kf():
    return safe_load(USER_KF_FILE, {})

def get_user_kf(user_id):
    d = get_all_user_kf()
    return d.get(str(user_id), [])

def save_user_kf(user_id, kf_list):
    d = get_all_user_kf()
    d[str(user_id)] = kf_list
    safe_save(USER_KF_FILE, d)

def delete_user_kf(user_id):
    d = get_all_user_kf()
    if str(user_id) in d:
        del d[str(user_id)]
        safe_save(USER_KF_FILE, d)
        return True
    return False

# ---------------- Helpers: signals log ----------------
def record_user_signal(user_id, signal_text):
    store = safe_load(USER_SIGNALS, [])
    store.append({"user_id": user_id, "time": datetime.now().isoformat(), "signal": signal_text})
    if len(store) > 2000:
        store = store[-2000:]
    safe_save(USER_SIGNALS, store)

# ---------------- OCR and extract ----------------
# Preprocessing to improve OCR accuracy
def preprocess_image_for_ocr(in_path, out_path=None):
    img = Image.open(in_path)
    # convert to grayscale, increase contrast
    img = img.convert("L")
    img = ImageOps.autocontrast(img)
    # optional: sharpen
    img = img.filter(ImageFilter.MedianFilter(size=3))
    if out_path:
        img.save(out_path)
    return img

def extract_kf_from_image(image_path):
    try:
        img = preprocess_image_for_ocr(image_path)
        # use pytesseract to get text; set config to digits and punctuation
        custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789.xX'
        text = pytesseract.image_to_string(img, config=custom_config)
        # find numbers like "1.23", "180.98", maybe with trailing 'x' or 'x.'
        # common patterns: 1.23x, 1.23, 1.23 x
        found = re.findall(r'\d{1,3}\.\d{1,3}', text)
        # convert to float and filter unrealistic (0 < kf < 1000)
        kfs = []
        for s in found:
            try:
                v = float(s)
                if 0.5 <= v <= 10000:  # wide limit
                    kfs.append(round(v, 2))
            except:
                continue
        return kfs
    except Exception as e:
        logging.error("OCR extract error: %s", e)
        return []

# ---------------- Analysis algorithm (same logic as before) ----------------
import statistics

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
        logging.error("analyze error: %s", e)
        signal = "🔸 Tahlilda xato, qayta urinib ko'ring."
    return summary, signal

# ---------------- Pending actions (simple in-memory state) ----------------
pending_action = {}  # user_id -> {"action": "await_text"|"await_photo", "meta": {...}}

# ---------------- Inline menu for signal ----------------
def build_signal_menu():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("📜 Oxirgi 20 ta signal", callback_data="signal_last"))
    kb.add(types.InlineKeyboardButton("✏️ Yangi signal (matn)", callback_data="signal_add_text"))
    kb.add(types.InlineKeyboardButton("📸 Yangi signal (skrinshot)", callback_data="signal_add_photo"))
    kb.add(types.InlineKeyboardButton("🗑️ Saqlangan KF'larni o'chirish", callback_data="signal_clear"))
    return kb

# ---------------- Handlers ----------------
@bot.message_handler(commands=['start'])
def cmd_start(m):
    txt = (
        "👋 <b>Salom!</b> Aviator tahlilchi botga xush kelibsiz.\n\n"
        "🔐 Aktivatsiya uchun admin (@akibet) dan bir martalik kod oling.\n"
        "📊 Signal menyusi uchun /signalmenu bosing.\n"
        "📸 Skrinshot yuborish orqali ham KFlarni avtomatik qabul qilamiz.\n\n"
        f"🎁 Promo: <code>{PROMO_CODE}</code>\n"
        f"🔗 Ro'yxat: {REG_LINK}"
    )
    bot.send_message(m.chat.id, txt, parse_mode="HTML", reply_markup=build_signal_menu())

@bot.message_handler(commands=['signalmenu'])
def cmd_signalmenu(m):
    bot.send_message(m.chat.id, "📊 Signal bo'limi (menyu):", reply_markup=build_signal_menu())

# Admin: generate keys
@bot.message_handler(commands=['genkey', 'createkey'])
def cmd_genkey(m):
    username = m.from_user.username or ""
    if username.lower() != ADMIN_USERNAME.lower():
        bot.send_message(m.chat.id, "⛔ Bu buyruq faqat admin uchun.")
        return
    parts = m.text.strip().split()
    cnt = 1
    if len(parts) >= 2:
        try:
            cnt = min(50, max(1, int(parts[1])))
        except:
            cnt = 1
    keys = gen_keys(cnt, created_by=m.from_user.id)
    reply = "✅ Yangi kod(lar):\n\n" + "\n".join(keys)
    reply += f"\n\nHar bir kod faqat 1 marta ishlatiladi. Admin: {ADMIN_USERNAME_DISPLAY}"
    bot.send_message(m.chat.id, reply)

@bot.message_handler(commands=['users'])
def cmd_users(m):
    username = m.from_user.username or ""
    if username.lower() != ADMIN_USERNAME.lower():
        bot.send_message(m.chat.id, "⛔ Bu buyruq faqat admin uchun.")
        return
    users = get_all_users()
    if not users:
        bot.send_message(m.chat.id, "🔎 Hozircha tasdiqlangan foydalanuvchi yo'q.")
        return
    txt = "📋 Tasdiqlangan foydalanuvchilar:\n\n"
    for u in users:
        txt += f"ID: {u['id']} | @{u.get('username') or '—'} | key: {u.get('key')} | promo: {'✅' if u.get('promo_confirmed') else '❌'}\n"
    bot.send_message(m.chat.id, txt)

# Activation: user sends code directly (case-insensitive)
@bot.message_handler(func=lambda m: isinstance(m.text, str) and len(m.text.strip()) >= 4)
def handle_text_activation_or_actions(m):
    text = m.text.strip().upper()
    uid = m.from_user.id

    # If user is pending to add text signals, handle separately
    if pending_action.get(str(uid), {}).get("action") == "await_text":
        pending_action.pop(str(uid), None)
        process_user_text_signals(m)
        return

    # Check activation if matches an existing key
    keys = safe_load(ACT_KEYS_FILE, {})
    if text in keys:
        # Activation attempt
        info = keys.get(text)
        if info and not info.get("used"):
            ok, reason = using_key(text, uid)
            if ok:
                username = m.from_user.username if m.from_user and m.from_user.username else None
                add_verified_user(uid, username, text)
                # Ask to confirm registration via promo link
                kb = types.InlineKeyboardMarkup()
                kb.add(types.InlineKeyboardButton("🔗 Ro'yxatdan o'tish (bosib o'ting)", url=REG_LINK))
                kb.add(types.InlineKeyboardButton("✅ Men ro'yxatdan o'tdim (tasdiqlash)", callback_data=f"confirm_reg|{text}"))
                bot.send_message(uid, "✅ Aktivatsiya muvaffaqiyatli! Iltimos, ro'yxatdan o'tganingizni tasdiqlang.", reply_markup=kb)
            else:
                bot.send_message(uid, "⚠️ Kodni ishlatishda muammo. Iltimos admin bilan bog'laning.")
        else:
            bot.send_message(uid, "⚠️ Bu kod allaqachon ishlatilgan yoki mavjud emas.")
        return

    # Not activation; allow other text commands to flow to numeric handler (fallback below)
    # Continue to fallback numeric handling
    # (Do not return here)

    # Numeric list fallback or plain-number messages handled by below fallback handler

# Callback handlers for signal menu
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    uid = call.from_user.id
    data = call.data
    if data == "signal_last":
        if not is_user_activated(uid):
            bot.answer_callback_query(call.id, "⚠️ Siz hali aktivatsiya qilinmagansiz.", show_alert=True)
            return
        kfs = get_user_kf(uid)
        if not kfs:
            bot.answer_callback_query(call.id, "🔎 Saqlangan KF topilmadi.", show_alert=True)
            return
        # Show last up to 20 in single message (one per line)
        text = "📜 So'nggi saqlangan KF (oxirgi {} ta):\n\n".format(len(kfs))
        # show from oldest->newest or newest->oldest? We'll show newest last (chronological)
        text += "\n".join([f"{v}x" for v in kfs[-20:]])
        bot.answer_callback_query(call.id, "Oxirgi signallar yuborildi.")
        bot.send_message(uid, text)
        return

    if data == "signal_add_text":
        if not is_user_activated(uid):
            bot.answer_callback_query(call.id, "⚠️ Siz hali aktivatsiya qilinmagansiz.", show_alert=True)
            return
        pending_action[str(uid)] = {"action": "await_text", "since": time.time()}
        bot.answer_callback_query(call.id, "Matnli signal yuborish uchun tayyor.", show_alert=False)
        bot.send_message(uid, "Iltimos, yangi signalni quyidagi formatda yuboring — har qatorda bitta qiymat yoki vergul bilan ajratilgan:\n\nMisol:\n1.23, 1.45, 1.67\nyoki\n1.23\n1.45\n1.67")
        return

    if data == "signal_add_photo":
        if not is_user_activated(uid):
            bot.answer_callback_query(call.id, "⚠️ Siz hali aktivatsiya qilinmagansiz.", show_alert=True)
            return
        pending_action[str(uid)] = {"action": "await_photo", "since": time.time()}
        bot.answer_callback_query(call.id, "Skrinshot yuboring — men uni avtomatik o‘qib olaman.", show_alert=False)
        bot.send_message(uid, "Iltimos, Aviator o'yinidagi <b>История раундов</b> qismidan skrinshot yuboring (faqat bitta rasm kerak).", parse_mode="HTML")
        return

    if data == "signal_clear":
        if not is_user_activated(uid):
            bot.answer_callback_query(call.id, "⚠️ Siz hali aktivatsiya qilinmagansiz.", show_alert=True)
            return
        ok = delete_user_kf(uid)
        if ok:
            bot.answer_callback_query(call.id, "✅ Saqlangan KF'lar o'chirildi.", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "🔎 Saqlangan KF topilmadi.", show_alert=True)
        return

    # registration confirm callback
    if data.startswith("confirm_reg|"):
        key = data.split("|", 1)[1]
        k = key_info(key)
        if not k:
            bot.answer_callback_query(call.id, "⚠️ Kod topilmadi.", show_alert=True)
            return
        if int(k.get("used_by") or -1) != int(uid):
            bot.answer_callback_query(call.id, "⚠️ Ushbu kod sizga tegishli emas.", show_alert=True)
            return
        ok = set_promo_confirmed(uid)
        if ok:
            bot.answer_callback_query(call.id, "✅ Ro'yxatdan o'tish tasdiqlandi.", show_alert=True)
            bot.send_message(uid, "🎉 Rahmat! Ro'yxatdan o'tishingiz tasdiqlandi.")
        else:
            bot.answer_callback_query(call.id, "⚠️ Tizimda xato yoki siz aktivatsiya qilinmagansiz.", show_alert=True)
        return

# Process user text signals (when pending)
def process_user_text_signals(message):
    uid = message.from_user.id
    txt = (message.text or "").strip()
    if not txt:
        bot.send_message(uid, "⚠️ Noto'g'ri format. Iltimos: 1.23,1.45 yoki har qatorga bitta qiymat.")
        return
    parts = [p.strip() for p in re.split(r'[,\n;]+', txt) if p.strip()]
    nums = []
    for p in parts:
        try:
            v = float(p)
            nums.append(round(v, 2))
        except:
            # try replace comma as decimal (rare)
            p2 = p.replace(',', '.')
            try:
                v = float(p2)
                nums.append(round(v,2))
            except:
                pass
    if len(nums) < 1:
        bot.send_message(uid, "⚠️ Hech qanday KF topilmadi. Iltimos to'g'ri formatda yuboring.")
        return
    # Smart append/replace logic:
    old = get_user_kf(uid)
    if len(nums) >= 10:
        updated = nums[-20:]
        action = "yangilandi (butun ro'yxat sifatida)"
    else:
        updated = (old + nums)[-20:]
        action = "qo'shildi (davomi sifatida)"
    save_user_kf(uid, updated)
    summary, signal = analyze_list_and_build_signal(updated[-20:])
    msg = "✅ Signal saqlandi (" + action + ")\n\n" + "📊 Tanlangan KFlar:\n" + "\n".join([f"{x}" for x in updated[-20:]]) + "\n\n" + summary + "\n🧠 Tavsiya:\n" + signal
    bot.send_message(uid, msg, parse_mode="HTML")
    record_user_signal(uid, "user_text_input")
    return

# Photo handler (handles both spontaneous screenshot uploads and pending photo requests)
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    uid = message.from_user.id
    if not is_user_activated(uid):
        bot.send_message(uid, "❌ Siz hali aktivatsiya qilinmagansiz.")
        return
    # Download highest resolution photo
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded = bot.download_file(file_info.file_path)
    tmp_path = os.path.join(DATA_DIR, f"{uid}_{int(time.time())}.jpg")
    with open(tmp_path, "wb") as f:
        f.write(downloaded)

    # Extract KF values via OCR
    kfs = extract_kf_from_image(tmp_path)
    try:
        os.remove(tmp_path)
    except:
        pass

    if not kfs:
        bot.send_message(uid, "⚠️ KF topilmadi. Iltimos rasmni yana biroz aniqroq yuboring yoki tekst formatida yuboring.")
        return

    # Smart logic: if user sent many numbers (>=10) treat as full list, else append
    old = get_user_kf(uid)
    if len(kfs) >= 10:
        updated = kfs[-20:]
        action = "yangilandi (to'liq ro'yxat)"
    else:
        updated = (old + kfs)[-20:]
        action = "qo'shildi (davomi sifatida)"
    save_user_kf(uid, updated)
    summary, signal = analyze_list_and_build_signal(updated[-20:])
    msg = "✅ Rasmdan KFlar tanib olindi (" + action + ")\n\n" + "📊 Tanlangan KFlar:\n" + "\n".join([f"{x}" for x in updated[-20:]]) + "\n\n" + summary + "\n🧠 Tavsiya:\n" + signal
    bot.send_message(uid, msg, parse_mode="HTML")
    record_user_signal(uid, "user_photo_input")
    return

# Fallback numeric-list handler (if user just sends numbers without going through menu)
@bot.message_handler(func=lambda m: isinstance(m.text, str))
def fallback_numeric_handler(m):
    uid = m.from_user.id
    text = m.text.strip()
    # If user was pending to add text, that was handled earlier in handle_text_activation_or_actions
    # Here we check if the message looks like a numeric list (several numbers)
    maybe_parts = [p.strip() for p in re.split(r'[,\n;]+', text) if p.strip()]
    nums = []
    if 1 <= len(maybe_parts) <= 500:
        for p in maybe_parts:
            # Accept forms like "1.23", "1,23" (comma decimal)
            p2 = p.replace(',', '.')
            try:
                v = float(p2)
                nums.append(round(v,2))
            except:
                nums = []
                break
    if nums:
        if not is_user_activated(uid):
            bot.send_message(uid, "⚠️ Siz hali aktivatsiya qilinmagansiz. Admindan kod oling.")
            return
        # Smart append/replace decision
        old = get_user_kf(uid)
        if len(nums) >= 10:
            updated = nums[-20:]
            action = "yangilandi (butun ro'yxat sifatida)"
        else:
            updated = (old + nums)[-20:]
            action = "qo'shildi (davomi sifatida)"
        save_user_kf(uid, updated)
        summary, signal = analyze_list_and_build_signal(updated[-20:])
        msg = "✅ Signal saqlandi (" + action + ")\n\n" + "📊 Tanlangan KFlar:\n" + "\n".join([f"{x}" for x in updated[-20:]]) + "\n\n" + summary + "\n🧠 Tavsiya:\n" + signal
        bot.send_message(uid, msg, parse_mode="HTML")
        record_user_signal(uid, "user_numeric_input")
        return

    # Otherwise, help message
    bot.send_message(uid,
                     "❓ Men tushunmadim.\n"
                     " - /signalmenu — signal menyusini ochish\n"
                     " - /genkey N — (admin) N dona kod yaratish\n"
                     " - Rasm yuboring (skrinshot) yoki KF larni matn ko'rinishida yuboring.\n"
                     " - /mykf — saqlangan KF'laringizni ko'rish\n                     ")


# /mykf and /clearkf commands
@bot.message_handler(commands=['mykf'])
def cmd_mykf(m):
    uid = m.from_user.id
    if not is_user_activated(uid):
        bot.send_message(uid, "⚠️ Siz hali aktivatsiya qilinmagansiz.")
        return
    kf = get_user_kf(uid)
    if not kf:
        bot.send_message(uid, "🔎 Saqlangan KF topilmadi.")
        return
    txt = "📂 Sizning saqlangan KF'laringiz (oxirgi {} ta):\n\n".format(len(kf))
    txt += "\n".join([f"{v}x" for v in kf[-20:]])
    bot.send_message(uid, txt)

@bot.message_handler(commands=['clearkf'])
def cmd_clearkf(m):
    uid = m.from_user.id
    if not is_user_activated(uid):
        bot.send_message(uid, "⚠️ Siz hali aktivatsiya qilinmagansiz.")
        return
    ok = delete_user_kf(uid)
    if ok:
        bot.send_message(uid, "✅ Saqlangan KF'laringiz o'chirildi.")
    else:
        bot.send_message(uid, "🔎 Saqlangan KF topilmadi.")

# ---------------- Auto-signal worker (keeps the old behavior) ----------------
def generate_kf_sim():
    r = random.random()
    if r < 0.70:
        return round(random.uniform(1.00, 2.50), 2)
    elif r < 0.90:
        return round(random.uniform(2.51, 5.00), 2)
    else:
        return round(random.uniform(5.01, 12.00), 2)

def append_game(kf):
    history = safe_load(GAME_HISTORY, [])
    history.append({"kf": kf, "time": datetime.now().isoformat()})
    if len(history) > 200:
        history = history[-200:]
    safe_save(GAME_HISTORY, history)

def auto_signal_worker():
    while True:
        settings = safe_load(SETTINGS_FILE, {"auto_signals": False, "cycle_min_s": 90, "cycle_max_s": 120})
        wait_s = random.randint(settings.get("cycle_min_s", 90), settings.get("cycle_max_s", 120))
        kf = generate_kf_sim()
        append_game(kf)
        if settings.get("auto_signals"):
            history = safe_load(GAME_HISTORY, [])
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
                f"👤 Admin: {ADMIN_USERNAME_DISPLAY}\n"
                f"🤖 Kanal: {CHANNEL_LINK}"
            )
            users = get_all_users()
            for u in users:
                try:
                    bot.send_message(u["id"], text)
                except Exception as e:
                    logging.info("auto send fail %s: %s", u["id"], e)
            record_user_signal("AUTO_BROADCAST", signal)
        logging.debug("Simulated round: %s next in %ss", kf, wait_s)
        time.sleep(wait_s)

threading.Thread(target=auto_signal_worker, daemon=True).start()

# ---------------- Run bot ----------------
def run():
    logging.info("Bot started.")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)

if __name__ == "__main__":
    run()
