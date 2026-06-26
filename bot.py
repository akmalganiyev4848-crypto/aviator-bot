import logging
from aiogram import Bot, Dispatcher, html
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import asyncio

# Bot tokeningizni shu yerga yozing
TOKEN = "BOT_TOKENINGIZNI_SHU_YERGA_YOZING"

# SIZNING MA'LUMOTLARINGIZ
PROMO_KOD = "AKIBET777"
SAYT_LINK = "https://lb-aff.com/L?tag=d_4114394m_22611c_site&site=4114394&ad=22611&r=registration"
APK_LINK = "https://lb-aff.com/L?tag=d_4114394m_66803c_apk1&site=4114394&ad=66803"
REF_START_PARAM = "myref"  # t.me/bot_nomi?start=myref (avtomatik ochish uchun link)

# Botni sozlash
logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Tasdiqlangan foydalanuvchilar bazasi (fonda saqlanadi)
tasdiqlangan_foydalanuvchilar = set()

class BotHolatlari(StatesGroup):
    promokod_kutish = State()

# Ro'yxatdan o'tish uchun tugmalarni yaratish
def royxatdan_otish_tugmalari():
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 Sayt orqali ro'yxatdan o'tish", url=SAYT_LINK)],
        [InlineKeyboardButton(text="📱 APK yuklab olish (Android)", url=APK_LINK)]
    ])
    return markup

@dp.message(CommandStart())
async def start_komandasi(message: Message, state: FSMContext):
    user_id = message.from_user.id
    argument = message.text.split()[1] if len(message.text.split()) > 1 else None

    # 1. Agar foydalanuvchi allaqachon tasdiqlangan bo'lsa
    if user_id in tasdiqlangan_foydalanuvchilar:
        await message.answer(f"🚀 Xush kelibsiz, {html.bold(message.from_user.full_name)}! Bot siz uchun faol. Foydalanishishingiz mumkin.")
        return

    # 2. Agar maxsus ref-link orqali kir

