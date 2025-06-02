import os
import logging
import tempfile
import telebot
import librosa
import numpy as np
import soundfile as sf
from flask import Flask, request
from yt_dlp import YoutubeDL

# Logging activeren
logging.basicConfig(level=logging.DEBUG)

# Telegram token en Flask
TOKEN = '7739002753:AAFgh-UlgRkYCd20CUrnUbhJ36ApQQ6ZL7o'
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Audio downloaden met fallback headers & cookies
def download_audio_from_youtube(url):
    output_path = os.path.join(tempfile.gettempdir(), 'audio.%(ext)s')
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'quiet': True,
        'noplaylist': True,
        'cookiefile': 'cookies.txt',
        'user_agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        ),
        'http_headers': {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                '(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
            ),
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
        },
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }]
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            logging.debug(f"[DOWNLOAD INFO] {info}")
            return os.path.join(tempfile.gettempdir(), 'audio.wav')
    except Exception as e:
        logging.error(f"[DOWNLOAD FOUT] {e}")
        raise

# Analyse van audio (BPM & key)
def analyse_audio(file_path):
    y, sr = librosa.load(file_path)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    chroma = librosa.feature.chroma_cens(y=y, sr=sr)
    chroma_mean = chroma.mean(axis=1)
    key_index = chroma_mean.argmax()
    key = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'][key_index]
    return tempo, key

# Telegram /start
@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, "🎶 Stuur een YouTube-link en ik analyseer het voor je!")

# YouTube-link afhandelen
@bot.message_handler(func=lambda message: 'youtu' in message.text)
def handle_youtube_link(message):
    url = message.text.strip()
    try:
        bot.send_message(message.chat.id, "🎧 Downloaden en analyseren... een moment.")
        file_path = download_audio_from_youtube(url)
        bpm, key = analyse_audio(file_path)
        bot.send_message(message.chat.id, f"✅ Analyse voltooid:\n\n🔑 Key: {key}\n🎵 BPM: {round(bpm)}")
        os.remove(file_path)
    except Exception as e:
        logging.error(f"Fout bij analyse: {e}")
        bot.send_message(message.chat.id, "❌ Er ging iets mis bij het downloaden of analyseren.")

# Webhook route
@app.route(f"/{TOKEN}", methods=['POST'])
def webhook():
    update = request.get_json()
    logging.debug(f"[Webhook] JSON ontvangen: {update}")
    if update:
        bot.process_new_updates([telebot.types.Update.de_json(update)])
    return 'OK', 200

# Testpagina
@app.route('/', methods=['GET'])
def index():
    return 'Bot draait!', 200

# Alleen lokaal starten (niet op Railway)
if __name__ == '__main__':
    app.run(debug=True)
