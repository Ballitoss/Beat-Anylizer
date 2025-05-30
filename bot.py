import os
import uuid
import yt_dlp
import librosa
import numpy as np
from flask import Flask, request
import telebot
from telebot import types

# === CONFIG ===
BOT_TOKEN = "7739002753:AAFgh-UlgRkYCd20CUrnUbhJ36ApQQ6ZL7o"
DOWNLOAD_DIR = "downloads"
WEBHOOK_URL = "https://beat-analyzer-1.onrender.com"  # Vervang met je juiste render URL

# === INIT ===
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# === HULPFUNCTIES ===
def download_audio(url, filename):
    mp3_path = os.path.join(DOWNLOAD_DIR, f"{filename}.mp3")
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': mp3_path,
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
    return mp3_path

def analyze_beat(path):
    y, sr = librosa.load(path)
    tempo_data, _ = librosa.beat.beat_track(y=y, sr=sr)
    tempo = float(tempo_data) if isinstance(tempo_data, (float, int, np.floating)) else float(tempo_data[0])
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    key_index = chroma.mean(axis=1).argmax()
    keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    key = keys[key_index]
    return round(tempo), key

# === HANDLERS ===
@bot.message_handler(commands=['start'])
def handle_start(message):
    text = (
        "🎶 *Welkom bij Beat Analyzer Bot!*\n\n"
        "📎 Stuur een YouTube-link van een beat en ik geef je de BPM, key en het mp3-bestand terug.\n\n"
        "💸 *Extra functies of support?*\n"
        "[Doneer via PayPal](https://paypal.me/Balskiee)"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: True)
def handle_link(message):
    url = message.text.strip()
    if not url.startswith("http"):
        bot.reply_to(message, "❌ Ongeldige YouTube-link.")
        return

    bot.reply_to(message, "⏬ Downloaden en analyseren van je beat, even geduld...")

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
                performer="BeatAnalyzer",
                title=f"Beat {tempo}BPM in {key}",
                parse_mode="Markdown"
            )
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Analyse fout:\n`{e}`", parse_mode="Markdown")

# === FLASK ROUTES ===
@app.route('/', methods=['GET'])
def index():
    return "🤖 Beat Analyzer Bot draait!"

@app.route(f"/{BOT_TOKEN}", methods=['POST'])
def webhook():
    update = types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return '', 200

# === START SERVER ===
if __name__ == "__main__":
    import telebot.apihelper
    telebot.apihelper.delete_webhook(BOT_TOKEN)  # Fout zat hier
    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/{BOT_TOKEN}")
    print("🌐 Webhook ingesteld.")
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
