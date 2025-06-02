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

# YouTube audio downloaden met cookies
def download_audio_from_youtube(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(tempfile.gettempdir(), 'audio.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'cookiefile': 'cookies.txt',
        'quiet': True,
        'no_warnings': True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return os.path.join(tempfile.gettempdir(), 'audio.wav')

# BPM en toonhoogte analyseren
def analyse_audio(file_path):
    y, sr = librosa.load(file_path)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    chroma = librosa.feature.chroma_cens(y=y, sr=sr)
    chroma_mean = chroma.mean(axis=1)
    key_index = chroma_mean.argmax()
    key = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'][key_index]
    return tempo, key

# Telegram start command
@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, "🎶 Stuur me een YouTube-link en ik analyseer het voor je!")

# YouTube-link ontvangen
@bot.message_handler(func=lambda message: 'youtu' in message.text)
def handle_youtube_link(message):
    url = message.text
    try:
        bot.send_message(message.chat.id, "🎧 Downloaden en analyseren... Even geduld.")
        file_path = download_audio_from_youtube(url)
        bpm, key = analyse_audio(file_path)
        bot.send_message(message.chat.id, f"✅ Analyse voltooid:\n\n🔑 Key: {key}\n🎵 BPM: {round(bpm)}")
        os.remove(file_path)
    except Exception as e:
        logging.error(f"Fout bij analyse: {e}")
        bot.send_message(message.chat.id, "❌ Er ging iets mis bij het downloaden of analyseren.")

# Flask route voor webhook
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = request.get_json()
    logging.debug(f"[Webhook] JSON ontvangen: {update}")
    if update:
        bot.process_new_updates([telebot.types.Update.de_json(update)])
    return 'OK', 200

# Root endpoint
@app.route('/', methods=['GET'])
def index():
    return 'Bot draait!', 200

# Run alleen in development (Railway gebruikt gunicorn)
if __name__ == '__main__':
    app.run(debug=True)
