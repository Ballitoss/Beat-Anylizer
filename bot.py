import os
import logging
from flask import Flask, request
import telebot
from telebot.types import Update

# === CONFIG ===
BOT_TOKEN = "7739002753:AAFgh-UlgRkYCd20CUrnUbhJ36ApQQ6ZL7o"
WEBHOOK_URL = f"https://beat-anylizer-1.onrender.com/{BOT_TOKEN}"

# === INIT ===
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# === LOGGING ===
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

# === HANDLERS ===
@bot.message_handler(commands=["start"])
def handle_start(message):
    logger.debug(f"[Handler] /start ontvangen van {message.chat.id}")
    text = (
        "🎶 *Welkom bij Beat Analyzer Bot!*\n\n"
        "📎 Stuur me een YouTube-link van een beat en ik geef je de BPM en key terug, plus het MP3-bestand.\n\n"
        "💸 Wil je ons steunen of extra functies?\n"
        "[Betaal via PayPal](https://paypal.me/Balskiee)"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    logger.debug(f"[Handler] Onbekend bericht ontvangen: {message.text}")
    bot.send_message(message.chat.id, "❌ Ongeldige input. Stuur een YouTube-link of gebruik /start.")

# === FLASK ROUTES ===
@app.route("/", methods=["GET"])
def home():
    return "✅ Beat Analyzer draait!"

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    try:
        json_str = request.get_data().decode("utf-8")
        update = Update.de_json(json_str)
        logger.debug(f"[Webhook] Update ontvangen: {update.to_dict()}")
        bot.process_new_updates([update])
    except Exception as e:
        logger.exception(f"[Webhook] Fout bij verwerken update: {e}")
    return "", 200

# === STARTUP ===
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
