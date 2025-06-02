import os
import logging
import tempfile
import telebot
import librosa
from flask import Flask, request
from yt_dlp import YoutubeDL

# Zet logging aan
logging.basicConfig(level=logging.DEBUG)

# Bot setup
TOKEN = '7739002753:AAFgh-UlgRkYCd20CUrnUbhJ36ApQQ6ZL7o'
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# YouTube audio download met cookies.txt ondersteuning
def download_audio_from_youtube(url):
    temp_dir = tempfile.gettempdir()
    output_path = os.path.join(temp_dir, 'audio.%(ext)s')
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'cookiefile': 'cookies.txt',
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            final_path = os.path.join(temp_dir, 'audio.wav')
            if os.path.exists(final_path):
                return final_path
            else:
                raise Exception("Bestand is niet aangemaakt.")
    except Exception as e:
        logging.error(f"[DOWNLOAD FOUT] {e}")
        raise

# Analyse van BPM en key
def analyse_audio(file_path):
    y, sr = librosa.load(file_path)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    chroma = librosa.feature.chroma_cens(y=y, sr=sr)
    key_index = chroma.mean(axis=1).argmax()
    key = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'][key_index]
    return tempo, key

# Telegram: start command
@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, "🎶 Stuur een YouTube-link en ik analyseer het voor je!")

# Telegram: YouTube link handler
@bot.message_handler(func=lambda message: 'youtu' in message.text)
def handle_youtube_link(message):
    url = message.text.strip()
    try:
        bot.send_message(message.chat.id, "🎧 Downloaden en analyseren... een moment.")
        file_path = download_audio_from_youtube(url)
        bpm, key = analyse_audio(file_path)
        bot.send_message(message.chat.id, f"✅ Analyse:\n\n🔑 Key: {key}\n🎵 BPM: {round(bpm)}")
        os.remove(file_path)
    except Exception as e:
        logging.error(f"Fout bij analyse: {e}")
        bot.send_message(message.chat.id, "❌ Fout bij het downloaden of analyseren van de audio.")

# Webhook endpoint
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = request.get_json()
    logging.debug(f"[Webhook] JSON ontvangen: {update}")
    if update:
        bot.process_new_updates([telebot.types.Update.de_json(update)])
    return 'OK', 200

# Index voor Railway
@app.route('/', methods=['GET'])
def index():
    return 'Bot draait!', 200

# Alleen lokaal runnen, niet in productie
if __name__ == '__main__':
    app.run(debug=True)
