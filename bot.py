import os
import uuid
import yt_dlp
import librosa
import numpy as np
from flask import Flask, request
from telebot import TeleBot, types

# === CONFIG ===
BOT_TOKEN = "7739002753:AAFgh-UlgRkYCd20CUrnUbhJ36ApQQ6ZL7o"
WEBHOOK_URL = "https://beat-anylizer-1.onrender.com"
DOWNLOAD_DIR = "downloads"

bot = TeleBot(BOT_TOKEN)
app = Flask(__name__)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# === HANDLERS MOETEN HIERBOVEN STAAN! ===
@bot.message_handler(commands=['start'])
def start_handler(message):
    bot.send_message(message.chat.id, "👋 Welkom bij Beat Analyzer Bot! Stuur een YouTube-link voor BPM & Key.")

@bot.message_handler(commands=['premium'])
def premium_handler(message):
    bot.send_message(message.chat.id, "💎 Premium komt eraan! Steun via PayPal: https://paypal.me/Balskiee")

@bot.message_handler(func=lambda msg: True)
def handle_link(message):
    url = message.text.strip()
    if not url.startswith("http"):
        bot.reply_to(message, "❌ Ongeldige YouTube-link.")
        return

    bot.reply_to(message, "⏬ Downloaden en analyseren van je beat...")

    try:
        filename = str(uuid.uuid4())
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
        mp3_path = os.path.join(DOWNLOAD_DIR, filename + ".mp3")

        y, sr = librosa.load(mp3_path)
        tempo_data, _ = librosa.beat.beat_track(y=y, sr=sr)
        tempo = float(tempo_data)
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        key_index = chroma.mean(axis=1).argmax()
        keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        key = keys[key_index]

        caption = f"✅ *Analyse voltooid!*\n🎵 BPM: `{round(tempo)}`\n🎹 Key: `{key}`"
        with open(mp3_path, 'rb') as audio:
            bot.send_audio(
                message.chat.id,
                audio,
                caption=caption,
                performer="BeatAnalyzer",
                title=f"Beat {round(tempo)} BPM - {key}",
                parse_mode="Markdown"
            )

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Fout: `{e}`", parse_mode="Markdown")

# === WEBHOOKS ===
@app.route('/', methods=['GET'])
def index():
    return "Bot draait."

@app.route(f"/{BOT_TOKEN}", methods=['POST'])
def webhook():
    update = types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return '', 200

# === STARTUP ===
if __name__ == "__main__":
    import telebot.apihelper
    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/{BOT_TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
