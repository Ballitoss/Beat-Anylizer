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

# YouTube audio downloaden
def download_youtube_audio(url, output_path):
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
        }
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True
    except Exception as e:
        logging.error(f"[DOWNLOAD FOUT] {e}")
        return False

# BPM en toonhoogte analyseren
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

# YouTube-link verwerken
@bot.message_handler(func=lambda message: 'youtu' in message.text)
def handle_youtube_link(message):
    url = message.text.strip()
    chat_id = message.chat.id
    bot.send_message(chat_id, "🎷 Downloaden en analyseren... een moment.")

    with tempfile.TemporaryDirectory() as tmpdir:
        audio_path = os.path.join(tmpdir, "audio.mp3")

        if not download_youtube_audio(url, audio_path):
            bot.send_message(chat_id, "❌ Downloaden mislukt. Probeer een andere video of check je cookies.txt.")
            return

        try:
            bpm, key = analyse_audio(audio_path)
            bot.send_message(chat_id, f"✅ Analyse voltooid:\n\n🔑 Key: {key}\n🎵 BPM: {round(bpm)}")
        except Exception as e:
            logging.error(f"Fout bij analyse: {e}")
            bot.send_message(chat_id, "❌ Er ging iets mis bij het analyseren van de audio.")

# Webhook voor Telegram
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = request.get_json()
    logging.debug(f"[Webhook] JSON ontvangen: {update}")
    if update:
        bot.process_new_updates([telebot.types.Update.de_json(update)])
    return 'OK', 200

@app.route('/', methods=['GET'])
def index():
    return 'Bot draait!', 200

if __name__ == '__main__':
    app.run(debug=True)
