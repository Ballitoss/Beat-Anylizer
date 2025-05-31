import os
import uuid
import logging
import yt_dlp
import librosa
import numpy as np
from flask import Flask, request
import telebot
from telebot import types

# === CONFIG ===
BOT_TOKEN = "7739002753:AAFgh-UlgRkYCd20CUrnUbhJ36ApQQ6ZL7o"
WEBHOOK_URL = "https://beat-anylizer-1.onrender.com"
DOWNLOAD_DIR = "downloads"

# === INIT ===
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# === HELPERFUNCTIES ===
def download_audio(url, filename):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(DOWNLOAD_DIR, filename + '.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return os.path.join(DOWNLOAD_DIR, filename + ".mp3")

def analyze_beat(path):
    y, sr = librosa.load(path)
    tempo_data, _ = librosa.beat.beat_track(y=y, sr=sr)
    tempo = float(tempo_data) if isinstance(tempo_data, (float, int)) else float(tempo_data[0])
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    key_index = chroma.mean(axis=1).argmax()
    keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    key = keys[key_index]
    return round(tempo), key

# === HANDLERS ===
@bot.message_handler(commands=['start'])
def handle_start(message):
    logging.debug("✅ /start geactiveerd")
    bot.send_message(
        message.chat.id,
        "🎶 *Welkom bij Beat Analyzer Bot!*\n\n"
        "📎 Stuur een YouTube-link van een beat en ik geef je de BPM en toonsoort terug.\n\n"
        "💸 Doneren? [PayPal](https://paypal.me/Balskiee)",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda msg: True)
def handle_beat_link(message):
    url = message.text.strip()
    if not url.startswith("http"):
        bot.reply_to(message, "❌ Ongeldige YouTube-link.")
        return

    bot.reply_to(message, "🔄 Beat wordt gedownload en geanalyseerd...")

    try:
        uid = str(uuid.uuid4())
        mp3_path = download_audio(url, uid)
        tempo, key = analyze_beat(mp3_path)

        caption = f"✅ *Analyse voltooid!*\n🎵 BPM: `{tempo}`\n🎹 Key: `{key}`"
        with open(mp3_path, 'rb') as audio:
            bot.send_audio(
                message.chat.id,
                audio,
                caption=caption,
                parse_mode="Markdown",
                title=f"Beat {tempo}BPM in {key}",
                performer="BeatAnalyzer"
            )
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Fout bij analyse:\n`{e}`", parse_mode="Markdown")
        logging.error(f"❌ Analysefout: {e}")

# === FLASK ROUTES ===
@app.route('/', methods=['GET'])
def index():
    return "✅ Beat Analyzer is live"

@app.route(f"/{BOT_TOKEN}", methods=['POST'])
def webhook():
    try:
        json_str = request.get_data().decode('utf-8')
        update = types.Update.de_json(json_str)
        logging.debug(f"[Webhook] Update ontvangen: {update}")
        bot.process_new_updates([update])
    except Exception as e:
        logging.error(f"[Webhook Error] {e}")
    return '', 200

# === STARTUP ===
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/{BOT_TOKEN}")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
