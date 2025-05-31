import os
import uuid
import yt_dlp
import librosa
import numpy as np
from flask import Flask, request
from telebot import TeleBot, types

# === CONFIG ===
BOT_TOKEN = "7739002753:AAFgh-UlgRkYCd20CUrnUbhJ36ApQQ6ZL7o"
WEBHOOK_URL = f"https://beat-anylizer-1.onrender.com/{BOT_TOKEN}"  # Juiste URL incl. token
DOWNLOAD_DIR = "downloads"

# === INIT ===
bot = TeleBot(BOT_TOKEN)
app = Flask(__name__)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# === ANALYSE FUNCTIE ===
def download_audio(url, filename):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(DOWNLOAD_DIR, filename + '.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return os.path.join(DOWNLOAD_DIR, filename + '.mp3')

def analyze_beat(path):
    y, sr = librosa.load(path)
    tempo_data, _ = librosa.beat.beat_track(y=y, sr=sr)
    tempo = float(tempo_data) if isinstance(tempo_data, (float, int)) else float(tempo_data[0])
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    key_index = chroma.mean(axis=1).argmax()
    keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    key = keys[key_index]
    return round(tempo), key

# === TELEGRAM HANDLERS ===
@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, "🎶 Stuur me een YouTube-link en ik geef je BPM + Key + MP3!")

@bot.message_handler(func=lambda msg: True)
def handle_url(message):
    url = message.text.strip()
    if not url.startswith("http"):
        bot.send_message(message.chat.id, "❌ Ongeldige YouTube-link.")
        return

    bot.send_message(message.chat.id, "⏬ Beat wordt gedownload en geanalyseerd...")

    try:
        uid = str(uuid.uuid4())
        mp3_path = download_audio(url, uid)
        tempo, key = analyze_beat(mp3_path)

        caption = f"✅ *Analyse klaar!*\n🎵 BPM: `{tempo}`\n🎹 Key: `{key}`"
        with open(mp3_path, 'rb') as audio:
            bot.send_audio(
                message.chat.id,
                audio,
                caption=caption,
                performer="BeatAnalyzer",
                title=f"BPM {tempo} | Key {key}",
                parse_mode="Markdown"
            )

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Fout bij analyse: `{e}`", parse_mode="Markdown")

# === WEBHOOK HANDLING ===
@app.route(f"/{BOT_TOKEN}", methods=['POST'])
def webhook():
    update = types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return '', 200

@app.route("/", methods=['GET'])
def index():
    return "🤖 Bot online en klaar voor gebruik!", 200

# === LAUNCH ===
if __name__ == "__main__":
    import telebot.apihelper
    telebot.apihelper.delete_webhook(BOT_TOKEN)
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
