import os
import uuid
import yt_dlp
import librosa
import numpy as np
import logging
from flask import Flask, request
from telebot import TeleBot
from telebot.types import Update

# === CONFIG ===
BOT_TOKEN = "7739002753:AAFgh-UlgRkYCd20CUrnUbhJ36ApQQ6ZL7o"
WEBHOOK_URL = "https://beat-anylizer-1.onrender.com"
DOWNLOAD_DIR = "downloads"

# === INIT ===
bot = TeleBot(BOT_TOKEN)
app = Flask(__name__)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# === LOGGER ===
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

# === AUDIO DOWNLOAD ===
def download_audio(url, filename):
    logging.debug(f"⏬ Start download van: {url}")
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(DOWNLOAD_DIR, filename + '.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': False,
        'no_warnings': False,
        'verbose': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return os.path.join(DOWNLOAD_DIR, filename + ".mp3")

# === ANALYSE ===
def analyze_beat(path):
    y, sr = librosa.load(path)
    tempo_data, _ = librosa.beat.beat_track(y=y, sr=sr)
    tempo = float(tempo_data)
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    key_index = chroma.mean(axis=1).argmax()
    keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    key = keys[key_index]
    return round(tempo), key

# === COMMAND: /start ===
@bot.message_handler(commands=["start"])
def handle_start(message):
    text = (
        "🎶 *Welkom bij Beat Analyzer Bot!*\n\n"
        "📎 Stuur me een YouTube-link van een beat en ik geef je de BPM en key terug, plus het MP3-bestand.\n\n"
        "💸 Wil je ons steunen of extra functies?\n"
        "[Betaal via PayPal](https://paypal.me/Balskiee)"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# === HANDLE YOUTUBE LINK ===
@bot.message_handler(func=lambda msg: msg.text and msg.text.startswith("http"))
def handle_link(message):
    url = message.text.strip()
    bot.send_message(message.chat.id, "⏬ Downloaden gestart...")

    try:
        uid = str(uuid.uuid4())
        bot.send_message(message.chat.id, f"📡 URL ontvangen:\n{url}")
        
        mp3_path = download_audio(url, uid)
        bot.send_message(message.chat.id, f"✅ MP3 opgeslagen:\n{mp3_path}")

        tempo, key = analyze_beat(mp3_path)
        bot.send_message(message.chat.id, f"🎼 Analyse: {tempo} BPM, Key: {key}")

        with open(mp3_path, 'rb') as audio:
            bot.send_audio(
                message.chat.id,
                audio,
                caption=f"🎵 *Beat Analyse*\nBPM: `{tempo}`\nKey: `{key}`",
                performer="BeatAnalyzer",
                title=f"Beat {tempo}BPM in {key}",
                parse_mode="Markdown"
            )

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Fout:\n`{e}`", parse_mode="Markdown")
        logger.exception("Fout tijdens downloaden/analyseren")

# === FLASK ROUTES ===
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    try:
        json_str = request.get_data().decode("utf-8")
        logger.debug(f"[Webhook] JSON ontvangen: {json_str}")
        update = Update.de_json(json_str)
        bot.process_new_updates([update])
        logger.info("[Webhook] Update verwerkt")
    except Exception as e:
        logger.exception(f"[Webhook] Fout bij verwerken update: {e}")
    return "", 200

@app.route("/", methods=["GET"])
def index():
    return "🤖 Beat Analyzer Bot is live!"

# === STARTUP ===
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/{BOT_TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
