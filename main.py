#!/usr/bin/env python3
# main.py - Aviator bot (full AI-ready version)

import os, json, threading, time, random, string, logging, re
from datetime import datetime
from PIL import Image, ImageFilter, ImageOps
import pytesseract
import telebot
from telebot import types

# ---------------- CONFIG ----------------
TOKEN = os.getenv("TOKEN", "7253804878:AAGPZL3t3ugKYgeWDKB8_vvGG2KJvM_-AaA")
ADMIN_USERNAME = "akibet1"
ADMIN_ID = 7960951525
PROMO_CODE = "AKIBET777"
REG_LINK = "https://lb-aff.com/L?tag=d_4114394m_22611c_site&site=4114394&ad=22611&r=registration"
APK_LINK = "https://lb-aff.com/L?tag=d_4114394m_66803c_apk1&site=4114394&ad=66803"
CHANNEL_LINK = "https://t.me/aviatorwinuzbot"

DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "verified_users.json")
ACT_KEYS_FILE = os.path.join(DATA_DIR, "activation_keys.json")
USER_KF_FILE = os.path.join(DATA_DIR, "user_kf.json")
USER_SIGNALS = os.path.join(DATA_DIR, "user_signals.json")
GAME_HISTORY = os.path.join(DATA_DIR, "game_history.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")

os.makedirs(DATA_DIR, exist_ok=True)

# ---------------- LOGGING ----------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ---------------- THREAD-SAFE JSON ----------------
_file_lock = threading.Lock()
def safe_load(path, default): 
    with _file_lock:
        try:
            if not os.path.exists(path): return default
            with open(path,"r",encoding="utf-8") as f: return json.load(f)
        except Exception as e: logging.error("safe_load %s: %s", path, e); return default
def safe_save(path, data):
    with _file_lock:
        try:
            with open(path,"w",encoding="utf-8") as f: json.dump(data,f,ensure_ascii=False,indent=4)
        except Exception as e: logging.error("safe_save %s: %s", path, e)

# Ensure files
for p,d in [(USERS_FILE,[]),(ACT_KEYS_FILE,{}),(USER_KF_FILE,{}),(USER_SIGNALS,[]),(GAME_HISTORY,[]),(SETTINGS_FILE,{"auto_signals":False,"cycle_min_s":90,"cycle_max_s":120})]:
    if not os.path.exists(p): safe_save(p,d)

# ---------------- BOT INIT ----------------
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
pending_action = {}  # user_id -> action

# ---------------- HELPERS ----------------
def gen_key(length=8):
    return ''.join(random.choice(string.ascii_uppercase+string.digits) for _ in range(length))
def gen_keys(count=1, created_by=None):
    keys = safe_load(ACT_KEYS_FILE,{})
    out=[]
    for _ in range(count):
        for _ in range(10):
            k = gen_key(8)
            if k not in keys: break
        keys[k]={"used":False,"created_by":created_by,"created_at":datetime.now().isoformat(),"used_by":None,"used_at":None}
        out.append(k)
    safe_save(ACT_KEYS_FILE,keys)
    return out
def using_key(key,user_id):
    keys=safe_load(ACT_KEYS_FILE,{})
    info=keys.get(key)
    if not info: return False,"NOT_FOUND"
    if info.get("used"): return False,"ALREADY"
    info["used"]=True; info["used_by"]=int(user_id); info["used_at"]=datetime.now().isoformat()
    keys[key]=info; safe_save(ACT_KEYS_FILE,keys)
    return True,"OK"
def key_info(key): return safe_load(ACT_KEYS_FILE,{}).get(key)

# ---------------- USERS ----------------
def get_all_users(): return safe_load(USERS_FILE,[])
def add_verified_user(user_id,username,used_key):
    users=get_all_users()
    for u in users:
        if int(u.get("id"))==int(user_id): return False
    users.append({"id":int(user_id),"username":username,"activated_at":datetime.now().isoformat(),"key":used_key,"promo_confirmed":False,"promo_confirmed_at":None})
    safe_save(USERS_FILE,users)
    return True
def set_promo_confirmed(user_id):
    users=get_all_users(); changed=False
    for u in users:
        if int(u.get("id"))==int(user_id):
            u["promo_confirmed"]=True
            u["promo_confirmed_at"]=datetime.now().isoformat()
            changed=True; break
    if changed: safe_save(USERS_FILE,users)
    return changed
def is_user_activated(user_id): return any(int(u.get("id"))==int(user_id) for u in get_all_users())

# ---------------- USER KF ----------------
def get_all_user_kf(): return safe_load(USER_KF_FILE,{})
def get_user_kf(user_id): return get_all_user_kf().get(str(user_id),[])
def save_user_kf(user_id,kf_list):
    d=get_all_user_kf(); d[str(user_id)]=kf_list; safe_save(USER_KF_FILE,d)
def delete_user_kf(user_id):
    d=get_all_user_kf()
    if str(user_id) in d: del d[str(user_id)]; safe_save(USER_KF_FILE,d); return True
    return False

# ---------------- SIGNALS ----------------
def record_user_signal(user_id,signal_text):
    store = safe_load(USER_SIGNALS,[])
    store.append({"user_id":user_id,"time":datetime.now().isoformat(),"signal":signal_text})
    if len(store)>2000: store=store[-2000:]
    safe_save(USER_SIGNALS,store)

# ---------------- OCR ----------------
def preprocess_image_for_ocr(in_path,out_path=None):
    img=Image.open(in_path).convert("L")
    img=ImageOps.autocontrast(img)
    img=img.filter(ImageFilter.MedianFilter(3))
    if out_path: img.save(out_path)
    return img
def extract_kf_from_image(image_path):
    try:
        img=preprocess_image_for_ocr(image_path)
        text=pytesseract.image_to_string(img,config='--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789.xX')
        found=re.findall(r'\d{1,3}\.\d{1,3}',text)
        kfs=[]
        for s in found:
            try: v=float(s); 
            except: continue
            if 0.5<=v<=10000: kfs.append(round(v,2))
        return kfs
    except Exception as e: logging.error("OCR extract error: %s", e); return []

# ---------------- ANALYSIS ----------------
import statistics
def analyze_list_and_build_signal(kf_list):
    n=len(kf_list)
    if n==0: return ("🔹 Ma'lumot mavjud emas.","🔸 Ma'lumot yo'q.")
    t1=len([x for x in kf_list if x<2.0])
    t2=len([x for x in kf_list if 2.0<=x<3.0])
    t3=len([x for x in kf_list if 3.0<=x<4.0])
    t4=len([x for x in kf_list if x>=4.0])
    avg=round(statistics.mean(kf_list),2)
    summary=(f"📊 <b>Tahlil (so'nggi {n} ta):</b>\n🔹 1.0–1.99: {t1} marta\n🔹 2.0–2.99: {t2} marta\n🔹 3.0–3.99: {t3} marta\n🔹 4.0+: {t4} marta\n📈 O'rtacha KF: <b>{avg}</b>\n")
    total=n; signal=""
    try:
        if t1/total>=0.6: signal="🔺 Oxirgi o'yinlarda 1–2 oralig'ida ko'p natijalar — <b>keyingi raund 2 dan baland bo'lishi mumkin</b>."
        elif t4>=3: signal="⚠️ Yaqinda bir nechta 4+ natija kuzatildi — <b>keyingi raund past bo'lishi mumkin</b>."
        elif (t2+t3)/total>=0.6: signal="🔥 O'rtacha va yuqori (2–4) dominant — <b>keyingi raund 3 dan baland bo'lishi ehtimoli bor</b>."
        elif avg<2.2: signal="🔹 Aralash, ammo o'rtacha past — <b>2 dan baland chiqish ehtimoli mavjud</b>."
        elif avg>=3.0: signal="⚠️ O'rtacha yuqori — <b>keyingi raund pastga tushish xavfi bor</b>."
        else: signal="♻️ Neytral holat — <b>2–3 oralig'ida</b> natija kutish tavsiya etiladi."
    except: signal="🔸 Tahlilda xato, qayta urinib ko'ring."
    return summary,signal

# ---------------- INLINE MENU ----------------
def build_signal_menu():
    kb=types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("📜 Oxirgi 20 ta signal",callback_data="signal_last"))
    kb.add(types.InlineKeyboardButton("✏️ Yangi signal (matn)",callback_data="signal_add_text"))
    kb.add(types.InlineKeyboardButton("📸 Yangi signal (skrinshot)",callback_data="signal_add_photo"))
    kb.add(types.InlineKeyboardButton("🗑️ Saqlangan KF'larni o'chirish",callback_data="signal_clear"))
    return kb

# ---------------- HANDLERS ----------------
@bot.message_handler(commands=['start'])
def cmd_start(m):
    bot.send_message(m.chat.id, f"👋 <b>Salom!</b>\n\n🔐 Aktivatsiya uchun admin (@{ADMIN_USERNAME}) dan kod oling.\n🎁 Promo: <code>{PROMO_CODE}</code>\n🔗 Ro'yxat: {REG_LINK}", reply_markup=build_signal_menu())

@bot.message_handler(commands=['signalmenu'])
def cmd_signalmenu(m): bot.send_message(m.chat.id,"📊 Signal menyusi:",reply_markup=build_signal_menu())

@bot.message_handler(commands=['genkey'])
def cmd_genkey(m):
    if m.from_user.id!=ADMIN_ID: bot.send_message(m.chat.id,"⛔ Bu faqat admin uchun."); return
    parts=m.text.split(); cnt=1
    if len(parts)>=2: cnt=int(parts[1])
    keys=gen_keys(cnt,created_by=ADMIN_ID)
    bot.send_message(m.chat.id,"✅ Kodlar:\n"+"\n".join(keys))

# ---------------- CALLBACK ----------------
@bot.callback_query_handler(func=lambda c: True)
def callback_query(call):
    uid=call.from_user.id; data=call.data
    if data=="signal_last":
        kf=get_user_kf(uid)
        if not kf: bot.answer_callback_query(call.id,"📭 Signal topilmadi."); return
        bot.send_message(uid,"📜 Oxirgi KF:\n"+"\n".join([str(x) for x in kf[-20:]]))
    elif data=="signal_add_text": pending_action[uid]={"action":"await_text"}; bot.send_message(uid,"✏️ Matn signalini yuboring")
    elif data=="signal_add_photo": pending_action[uid]={"action":"await_photo"}; bot.send_message(uid,"📸 Rasmini yuboring")
    elif data=="signal_clear":
        if delete_user_kf(uid): bot.send_message(uid,"✅ O'chirildi")
        else: bot.send_message(uid,"❌ Topilmadi")
    elif data.startswith("confirm_reg|"):
        key=data.split("|",1)[1]; k=key_info(key)
        if not k: bot.answer_callback_query(call.id,"❌ Kod topilmadi"); return
        if int(k.get("used_by") or -1)!=uid: bot.answer_callback_query(call.id,"❌ Sizga tegishli emas"); return
        if set_promo_confirmed(uid): bot.answer_callback_query(call.id,"✅ Ro'yxat tasdiqlandi"); bot.send_message(uid,"🎉 Rahmat!"); return
        bot.answer_callback_query(call.id,"❌ Xato")

# ---------------- MESSAGE ----------------
@bot.message_handler(func=lambda m: True, content_types=["text","photo"])
def main_handler(m):
    uid=m.from_user.id
    # pending
    if uid in pending_action:
        act=pending_action[uid]; pending_action.pop(uid)
        if act["action"]=="await_text" and m.content_type=="text":
            nums=[round(float(x.replace(",",".")),2) for x in re.split(r'[,;\n]+',m.text.strip()) if x.strip()]
            old=get_user_kf(uid); old.extend(nums); save_user_kf(uid,old)
            summary,signal=analyze_list_and_build_signal(old); record_user_signal(uid,signal)
            bot.send_message(uid,f"✅ Signal qo‘shildi.\n{summary}\n🧠 Tavsiya:\n<b>{signal}</b>")
            return
        elif act["action"]=="await_photo" and m.content_type=="photo":
            file_id=m.photo[-1].file_id; path=bot.get_file(file_id).file_path
            downloaded=bot.download_file(path); tmp_path=os.path.join(DATA_DIR,f"{uid}_tmp.jpg")
            with open(tmp_path,"wb") as f: f.write(downloaded)
            kfs=extract_kf_from_image(tmp_path); os.remove(tmp_path)
            if kfs:
                old=get_user_kf(uid); old.extend(kfs); save_user_kf(uid,old)
                summary,signal=analyze_list_and_build_signal(old); record_user_signal(uid,signal)
                bot.send_message(uid,f"✅ Rasm signal qo‘shildi.\n{summary}\n🧠 Tavsiya:\n<b>{signal}</b>")
            else: bot.send_message(uid,"❌ Rasmdan KF topilmadi")
            return

    # activation
    if m.text and re.match(r'^[A-Z0-9]{8}$',m.text.strip()):
        success,msg=using_key(m.text.strip(),uid)
        if success: add_verified_user(uid,m.from_user.username or "",m.text.strip()); bot.send_message(uid,f"✅ Faollashtirildingiz. Kod: {m.text.strip()}")
        else: bot.send_message(uid,f"❌ Kod xato yoki ishlatilgan ({msg})")
        return

    bot.send_message(uid,"ℹ️ Noma’lum buyruq. /signalmenu orqali signal bo‘limiga kirishingiz mumkin.")

# ---------------- AUTO SIGNAL ----------------
def generate_kf_sim(): r=random.random(); return round(random.uniform
