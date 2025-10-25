import telebot

# Tokenni to‘g‘ridan kiritamiz
TOKEN = "7253804878:AAGPZL3t3ugKYgeWDKB8_vvGG2KJvM_-AaA"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Salom 👋 Bot ishlayapti ✅")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"Siz yozdingiz: {message.text}")

print("Bot ishga tushmoqda...")
bot.polling(none_stop=True)
