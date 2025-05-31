import os
import uuid
import yt_dlp
import librosa
import numpy as np
from flask import Flask, request
from telebot import TeleBot, types

# === CONFIG ===
BOT_TOKEN = "7739002753:AAFgh-UlgRkYCd20CUrnUbhJ36ApQQ6ZL7o"
WEBHOOK_URL = f"https://beat-anylizer-1.onrender.com/{BOT_TOKEN}"
DOWNLOAD_DIR = "downloads"

# === INIT ===
bot = TeleBot(BOT_TOKEN)
app = Flask(__name__)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# === HULPFUNCTIES ===
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
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    key_index = chroma.mean(axis=1).argmax()
    keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    key = keys[key_index]
    return round(float(tempo)), key

# === TELEGRAM HANDLERS ===
@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id,
        "🎶 *Welkom bij Beat Analyzer Bot!*\n"
        "Stuur een YouTube-link en ik stuur je het tempo (BPM), key en mp3 van de beat terug.\n"
        "💸 [Steun via PayPal](https://paypal.me/Balskiee)",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda msg: True)
def handle_link(message):
    url = message.text.strip()
    if not url.startswith("http"):
        bot.reply_to(message, "❌ Ongeldige YouTube-link.")
        return

    bot.reply_to(message, "⏬ Downloaden en analyseren van je beat, momentje...")

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
        bot.send_message(message.chat.id, f"❌ Fout tijdens analyse:\n`{e}`", parse_mode="Markdown")

# === FLASK ROUTES ===
@app.route('/', methods=['GET'])
def index():
    return "🤖 Bot draait op webhook."

@app.route(f"/{BOT_TOKEN}", methods=['POST'])
def receive_update():
    try:
        update = types.Update.de_json(request.stream.read().decode("utf-8"))
        print("[DEBUG] Webhook update ontvangen:", update)
        bot.process_new_updates([update])
    except Exception as e:
        print(f"[ERROR] Webhook fout: {e}")
    return '', 200

# === STARTUP (Webhook instellen) ===
if __name__ == "__main__":
    import telebot.apihelper
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
