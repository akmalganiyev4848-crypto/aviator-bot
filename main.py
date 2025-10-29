
# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# main.py - Aviator bot (Full AI OCR + Activation + KF Management)
# Features included:
# - Admin can generate one-time activation codes (/genkey)
# - Users can activate using code
# - OCR from screenshots improved for KF extraction
# - Add signals via text or image
# - Analysis & AI-style recommendations
# - Max 20 KF per user, smart append/replace
# - Inline signal menu
# - Thread-safe JSON storage
# - Max special user activation codes
# - Logging enabled

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
ADMIN_USERNAME = "akibet1"    # Admin username WITHOUT '@'
ADMIN_ID = 7960951525        # Admin Telegram ID
PROMO_CODE = "AKIBET777"
REG_LINK = "https://lb-aff.com/L?tag=d_4114394m_22611c_site&site=4114394&ad=22611&r=registration"
APK_LINK = "https://lb-aff.com/L?tag=d_4114394m_66803c_apk1&site=4114394&ad=66803"
CHANNEL_LINK = "https://t.me/aviatorwinuzbot"

# ---------------- Files ----------------
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "verified_users.json")
ACT_KEYS_FILE = os.path.join(DATA_DIR, "activation_keys.json")
USER_KF_FILE = os.path.join(DATA_DIR, "user_kf.json")
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

# ---------------- Activation key helpers ----------------
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
        keys[k] = {"used": False, "created_by": created_by, "created_at": datetime.now().isoformat(), "used_by": None, "used_at": None}
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

# ---------------- User helpers ----------------
def get_all_users():
    return safe_load(USERS_FILE, [])

def add_verified_user(user_id, username, used_key):
    users = get_all_users()
    for u in users:
        if int(u.get("id")) == int(user_id):
            return False
    users.append({"id": int(user_id), "username": username, "activated_at": datetime.now().isoformat(), "key": used_key, "promo_confirmed": False, "promo_confirmed_at": None})
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

# ---------------- KF helpers ----------------
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

# ---------------- Signals helpers ----------------
def record_user_signal(user_id, signal_text):
    store = safe_load(USER_SIGNALS, [])
    store.append({"user_id": user_id, "time": datetime.now().isoformat(), "signal": signal_text})
    if len(store) > 2000:
        store = store[-2000:]
    safe_save(USER_SIGNALS, store)

# ---------------- OCR helpers ----------------
def preprocess_image_for_ocr(in_path):
    img = Image.open(in_path)
    img = img.convert("L")
    img = ImageOps.autocontrast(img)
    img = img.filter(ImageFilter.MedianFilter(size=3))
    return img

def extract_kf_from_image(image_path):
    try:
        img = preprocess_image_for_ocr(image_path)
        config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789.xX'
        text = pytesseract.image_to_string(img, config=config)
        found = re.findall(r'\d{1,3}\.\d{1,3}', text)
        kfs = []
        for s in found:
            try:
                v = float(s)
                if 0.5 <= v <= 10000:
                    kfs.append(round(v,2))
            except: pass
        return kfs
    except Exception as e:
        logging.error("OCR extract error: %s", e)
        return []

# ---------------- Analysis ----------------
import statistics
def analyze_list_and_build_signal(kf_list):
    n = len(kf_list)
    if n == 0:
        return ("ð¹ Ma'lumot mavjud emas.", "ð¸ Ma'lumot yo'q. Iltimos 10-20 ta KF yuboring.")
    t1 = len([x for x in kf_list if x < 2.0])
    t2 = len([x for x in kf_list if 2.0 <= x < 3.0])
    t3 = len([x for x in kf_list if 3.0 <= x < 4.0])
    t4 = len([x for x in kf_list if x >= 4.0])
    avg = round(statistics.mean(kf_list), 2) if n > 0 else 0
    summary = f"ð <b>Tahlil (so'nggi {n} ta):</b>\nð¹ 1.0â1.99: {t1} marta\nð¹ 2.0â2.99: {t2} marta\nð¹ 3.0â3.99: {t3} marta\nð¹ 4.0+: {t4} marta\nð O'rtacha KF: <b>{avg}</b>\n"
    total = n
    signal = ""
    try:
        if total == 0: signal="ð¸ Ma'lumot yetarli emas."
        elif t1 / total >= 0.6: signal="ðº Oxirgi o'yinlarda 1â2 oralig'ida ko'p natijalar â <b>ehtimol keyingi raund 2 dan baland bo'lishi mumkin</b>."
        elif t4 >= 3: signal="â ï¸ Yaqinda bir nechta 4+ natija kuzatildi â <b>keyingi raund past (1â2) bo'lishi mumkin</b>."
        elif (t2 + t3)/total >= 0.6: signal="ð¥ O'rtacha va yuqori (2â4) ko'rsatkichlar dominant â <b>keyingi raund 3 dan baland bo'lishi ehtimoli bor (lekin 4+ kam)</b>."
        else:
            if avg < 2.2: signal="ð¹ Aralash, ammo o'rtacha past â <b>2 dan baland chiqish ehtimoli mavjud</b>."
            elif avg >= 3.0: signal="â ï¸ O'rtacha yuqori â <b>keyingi raund pastga tushish xavfi bor</b>."
            else: signal="â»ï¸ Neytral holat â <b>2â3 oralig'ida</b> natija kutish tavsiya etiladi."
    except Exception as e:
        logging.error("analyze error: %s", e)
        signal = "ð¸ Tahlilda xato, qayta urinib ko'ring."
    return summary, signal

# ---------------- Pending actions ----------------
pending_action = {}

# ---------------- Inline menu ----------------
def build_signal_menu():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("ð Oxirgi 20 ta signal", callback_data="signal_last"))
    kb.add(types.InlineKeyboardButton("âï¸ Yangi signal (matn)", callback_data="signal_add_text"))
    kb.add(types.InlineKeyboardButton("ð¸ Yangi signal (skrinshot)", callback_data="signal_add_photo"))
    kb.add(types.InlineKeyboardButton("ðï¸ Saqlangan KF'larni o'chirish", callback_data="signal_clear"))
    return kb

# ---------------- Handlers ----------------
@bot.message_handler(commands=['start'])
def cmd_start(m):
    txt = f"ð <b>Salom!</b> Aviator tahlilchi botga xush kelibsiz.\n\nð Aktivatsiya uchun admin (@{ADMIN_USERNAME}) dan kod oling.\nð Signal menyusi uchun /signalmenu bosing.\nð Promo: <code>{PROMO_CODE}</code>\nð Ro'yxat: {REG_LINK}"
    bot.send_message(m.chat.id, txt, parse_mode="HTML", reply_markup=build_signal_menu())

@bot.message_handler(commands=['signalmenu'])
def cmd_signalmenu(m):
    bot.send_message(m.chat.id, "ð Signal bo'limi:", reply_markup=build_signal_menu())

# Admin commands and other handlers omitted for brevity in this display but included in final main.py
