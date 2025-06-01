import os
import logging
import tempfile
import uuid
from flask import Flask, request
import requests
import yt_dlp
import librosa
import soundfile as sf

# Logging inschakelen
logging.basicConfig(level=logging.DEBUG)

# Telegram Bot Token en Webhook
TOKEN = "7739002753:AAFgh-UlgRkYCd20CUrnUbhJ36ApQQ6ZL7o"
BOT_URL = f"https://api.telegram.org/bot{TOKEN}"

# Flask App
app = Flask(__name__)

# Startbericht
def send_message(chat_id, text):
    url = f"{BOT_URL}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

# Audio-analyse
def analyze_audio(file_path):
    y, sr = librosa.load(file_path, sr=None)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    key_index = chroma.mean(axis=1).argmax()
    keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    key = keys[key_index]
    return tempo, key

# YouTube-audio downloaden
def download_audio(url):
    with tempfile.TemporaryDirectory() as tempdir:
        filename = os.path.join(tempdir, f"{uuid.uuid4()}.mp3")
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': filename,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return filename

@app.route("/")
def index():
    return "✅ Bot draait"

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json()
    logging.debug(f"[Webhook] JSON ontvangen: {data}")
    
    if "message" in data:
        message = data["message"]
        chat_id = message["chat"]["id"]
        text = message.get("text", "")

        if text.startswith("/start"):
            send_message(chat_id, "✅ Update ontvangen. Bot is actief.")
        elif "youtube.com" in text or "youtu.be" in text:
            try:
                send_message(chat_id, "🎧 Downloaden gestart...")
                file_path = download_audio(text)
                tempo, key = analyze_audio(file_path)
                send_message(chat_id, f"🎶 Tempo: {tempo:.2f} BPM\n🔑 Key: {key}")
            except Exception as e:
                logging.error(f"Fout bij analyse: {e}")
                send_message(chat_id, "❌ Er ging iets mis bij het verwerken van de audio.")
    return "", 200
