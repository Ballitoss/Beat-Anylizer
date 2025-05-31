import os
import logging
from flask import Flask, request
import telebot
from telebot import types

# === CONFIG ===
BOT_TOKEN = "7739002753:AAFgh-UlgRkYCd20CUrnUbhJ36ApQQ6ZL7o"
WEBHOOK_URL = "https://beat-anylizer-1.onrender.com"

# === INIT ===
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

# === HANDLERS ===
@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, "👋 Welkom bij je bot!")

@bot.message_handler(func=lambda m: True)
def echo_all(message):
    bot.send_message(message.chat.id, f"Je zei: {message.text}")

# === FLASK ROUTES ===
@app.route('/', methods=['GET'])
def home():
    return 'Bot draait ✅'

@app.route(f"/{BOT_TOKEN}", methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = types.Update.de_json(json_str)
    logging.debug(f"[Webhook] Update ontvangen: {update}")
    bot.process_new_updates([update])
    return '', 200

# === STARTUP ===
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/{BOT_TOKEN}")
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
