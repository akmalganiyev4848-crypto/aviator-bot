import asyncio
import random
from aiogram import Bot, Dispatcher, html
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart

# Tokeningiz shu yerga xavfsiz joylashtirildi
BOT_TOKEN = "7253804878:AAGPZL3t3ugKYgeWDKB8_vvGG2KJvM_-AaA"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Bot tugmalari
menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🚀 Signal olish"), KeyboardButton(text="📊 Statistika")]
    ],
    resize_keyboard=True
)

@dp.message(CommandStart())
async def start_command(message: Message):
    await message.answer(
        f"Salom, {html.bold(message.from_user.full_name)}!\n\n"
        f"Aviator o'yini uchun simulyatsiya botiga xush kelibsiz.\n"
        f"Signal olish uchun pastdagi tugmani bosing.",
        reply_markup=menu_keyboard
    )

@dp.message(lambda message: message.text == "🚀 Signal olish")
async def get_signal(message: Message):
    # Analiz jarayonini taqlid qilish
    waiting_msg = await message.answer("🔄 Algoritm tahlil qilinmoqda, kuting...")
    await asyncio.sleep(1.5) # 1.5 soniya kutish
    
    # Tasodifiy koeffitsiyent yaratish
    chance = random.random()
    if chance < 0.6: # 60% ehtimollik bilan 1.0 dan 2.0 gacha
        coefficient = round(random.uniform(1.0, 2.0), 2)
    elif chance < 0.9: # 30% ehtimollik bilan 2.0 dan 5.0 gacha
        coefficient = round(random.uniform(2.0, 5.0), 2)
    else: # 10% ehtimollik bilan 5.0 dan 20.0 gacha
        coefficient = round(random.uniform(5.0, 20.0), 2)
        
    # Tasodifiy aniqlik foizi
    accuracy = random.randint(75, 95)
    
    # Signal matni
    signal_text = (
        f"🚀 {html.bold('AVIATOR SIGNAL')} 🚀\n\n"
        f"📈 Kutilayotgan koeffitsiyent: {html.code(f'{coefficient}x')}\n"
        f"🎯 Aniqlik ehtimoli: {accuracy}%\n\n"
        f"⚠️ Ogohlantirish: Bu shunchaki matematik ehtimollik hisobi!"
    )
    
    # Kutish xabarini o'chirib, signalni yuborish
    await waiting_msg.delete()
    await message.answer(signal_text, parse_mode="HTML")

@dp.message(lambda message: message.text == "📊 Statistika")
async def show_stats(message: Message):
    await message.answer(
        f"📊 Bot statistikasi:\n"
        f"🟢 Bot holati: Onlayn\n"
        f"⚡ Server tezligi: 0.04s\n"
        f"🤖 Algoritm versiyasi: v2.1"
    )

async def main():
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
  
