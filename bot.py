import logging
from aiogram import Bot, Dispatcher, html
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.client.session.aiohttp import AiohttpSession
import asyncio

# ⚠️ MANA SHU YERDAGI QO'SHTIRNOQ ICHIGA O'ZINGNING TOKENINGNI TASHLA:
TOKEN = "7123456789:ABCdefGhIJKlmNoPQRstUVwXyZ"

# PythonAnywhere tekin akkauntidagi blokni aylanib o'tish uchun bepul Proxy:
PROXY_URL = "http://proxy.server:3128"
session = AiohttpSession(proxy=PROXY_URL)

# SIZNING MA'LUMOTLARINGIZ
PROMO_KOD = "AKIBET777"
SAYT_LINK = "https://lb-aff.com/L?tag=d_4114394m_22611c_site&site=4114394&ad=22611&r=registration"
APK_LINK = "https://lb-aff.com/L?tag=d_4114394m_66803c_apk1&site=4114394&ad=66803"
REF_START_PARAM = "myref"

logging.basicConfig(level=logging.INFO)
# Botni maxsus proxy sessiyasi bilan ishga tushiramiz:
bot = Bot(token=TOKEN, session=session)
dp = Dispatcher()

tasdiqlangan_foydalanuvchilar = set()

class BotHolatlari(StatesGroup):
    promokod_kutish = State()

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

    if user_id in tasdiqlangan_foydalanuvchilar:
        await message.answer(f"🚀 Xush kelibsiz, {html.bold(message.from_user.full_name)}! Bot siz uchun faol.")
        return

    if argument == REF_START_PARAM:
        tasdiqlangan_foydalanuvchilar.add(user_id)
        await message.answer(f"🎉 Tabriklaymiz! Siz maxsus havola orqali kirdingiz. Bot ochildi!")
        await state.clear()
        return

    matn = (
        f"Salom, {html.bold(message.from_user.full_name)}! 👋\n\n"
        f"⚠️ Botdan to'liq foydalanish va signallarni ko'rish uchun quyidagi shartlarni bajaring:\n\n"
        f"1️⃣ Pastdagi tugmalar orqali sayt yoki APK ilovadan ro'yxatdan o'tishingiz shart.\n"
        f"2️⃣ Ro'yxatdan o'tishda {html.bold(PROMO_KOD)} promokodini kiriting.\n\n"
        f"Ro'yxatdan o'tib bo'lgach, faollashtirish uchun botga {html.underline('promokodingizni')} yozib yuboring 👇:"
    )
    
    await message.answer(matn, reply_markup=royxatdan_otish_tugmalari())
    await state.set_state(BotHolatlari.promokod_kutish)


@dp.message(BotHolatlari.promokod_kutish)
async def promokod_tekshirish(message: Message, state: FSMContext):
    user_id = message.from_user.id
    kiritilgan_kod = message.text.strip().upper()

    if kiritilgan_kod == PROMO_KOD:
        tasdiqlangan_foydalanuvchilar.add(user_id)
        await message.answer(
            f"✅ {html.bold('Muvaffaqiyatli faollashtirildi!')}\n"
            f"Promokod to'g'ri. Bot siz uchun ochildi! 🚀"
        )
        await state.clear()
    else:
        await message.answer(
            f"❌ Noto'g'ri promokod kiritildi!\n"
            f"Qaytadan urinib ko'ring yoki to'g'ri havoladan kiring:",
            reply_markup=royxatdan_otish_tugmalari()
        )


@dp.message()
async def bot_asosiy_ishlashi(message: Message):
    user_id = message.from_user.id

    if user_id not in tasdiqlangan_foydalanuvchilar:
        await message.answer("🛑 Botdan foydalanish uchun avval promokodni tasdiqlang. /start buyrug'ini bosing.")
        return

    if message.text == "Signal 🚀":
        await message.answer("🎯 Keyingi Aviator koeffitsiyenti: 1.95x\nTikishga tayyorlaning!")
    else:
        await message.answer("Bot faol! Kerakli buyruqni tanlang.")


async def main():
    print("Bot muvaffaqiyatli ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
