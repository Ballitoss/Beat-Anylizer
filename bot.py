import telebot
import os
import uuid
import yt_dlp
from pydub import AudioSegment
import librosa
import numpy as np
import traceback
import flask

# === CONFIG ===
BOT_TOKEN = "7739002753:AAFgh-UlgRkYCd20CUrnUbhJ36ApQQ6ZL7o"
DOWNLOAD_DIR = "downloads"
WEBHOOK_HOST = 'https://<JOUW-RENDER-NAAM>.onrender.com'
WEBHOOK_PATH = f"/{BOT_TOKEN}/"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# === INIT ===
bot = telebot.TeleBot(BOT_TOKEN)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

app = flask.Flask(__name__)

@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    json_string = flask.request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return '', 200

@app.route('/')
def index():
    return "✅ BeatAnalyzer Bot draait met Webhook!"

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
        info = ydl.extract_info(url, download=True)
        mp3_path = os.path.join(DOWNLOAD_DIR, filename + ".mp3")
        return mp3_path

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
    bot.reply_to(message, "🎶 Welkom bij *Beat Analyzer Bot*!\n\nStuur me een YouTube-link van een beat en ik geef je de BPM en key terug, plus het MP3-bestand. 🎧", parse_mode="Markdown")

@bot.message_handler(func=lambda msg: True)
def handle_link(message):
    url = message.text.strip()
    if not url.startswith("http"):
        bot.reply_to(message, "❌ Stuur een geldige YouTube-link aub.")
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
        traceback.print_exc()
        bot.reply_to(message, f"❌ Analyse fout: `{e}`", parse_mode="Markdown")

# === WEBHOOK ACTIVEREN ===
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)
print(f"🚀 Webhook actief: {WEBHOOK_URL}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
