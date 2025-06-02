import os
import logging
import tempfile
from flask import Flask, request
from yt_dlp import YoutubeDL
import telebot
import librosa
import soundfile as sf

# === Configuratie ===
BOT_TOKEN = '7739002753:AAFgh-UlgRkYCd20CUrnUbhJ36ApQQ6ZL7o'
COOKIE_FILE = 'cookies.txt'
WEBHOOK_URL = 'https://web-production-cfc73.up.railway.app/'

# === Init ===
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

# === Audio Analyse ===
def analyse_audio(file_path):
    try:
        y, sr = librosa.load(file_path)
        bpm = librosa.beat.tempo(y=y, sr=sr)[0]
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        key_index = chroma.mean(axis=1).argmax()
        key_name = ['C', 'C#', 'D', 'D#', 'E', 'F',
                    'F#', 'G', 'G#', 'A', 'A#', 'B'][key_index % 12]
        return round(bpm), key_name
    except Exception as e:
        logging.error(f"[ANALYSE FOUT] {e}")
        return None, None

# === Download Audio ===
def download_youtube_audio(url):
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp:
            output_path = temp.name
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'quiet': True,
            'noplaylist': True,
            'cookiefile': COOKIE_FILE,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        }
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return output_path
    except Exception as e:
        logging.error(f"[DOWNLOAD FOUT] {e}")
        return None

# === Handlers ===
@bot.message_handler(commands=['start'])
def start_handler(message):
    bot.send_message(message.chat.id, "🎶 Stuur een YouTube-link en ik analyseer het voor je!")

@bot.message_handler(func=lambda m: 'youtube.com' in m.text or 'youtu.be' in m.text)
def youtube_handler(message):
    url = message.text.strip()
    bot.send_message(message.chat.id, "🎷 Downloaden en analyseren... een moment.")

    mp3_path = download_youtube_audio(url)
    if not mp3_path:
        bot.send_message(message.chat.id, "⚠️ Kan audio niet downloaden. Check cookies.txt of probeer een andere video.")
        return

    bpm, key = analyse_audio(mp3_path)
    if bpm and key:
        bot.send_message(message.chat.id, f"🔊 BPM: {bpm}\n🎵 Key: {key}")
    else:
        bot.send_message(message.chat.id, "⚠️ Kon de audio niet analyseren.")

    with open(mp3_path, 'rb') as audio:
        bot.send_audio(message.chat.id, audio)

    os.remove(mp3_path)

# === Webhook Endpoint ===
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json()
    logging.debug("[Webhook] JSON ontvangen: %s", update)
    bot.process_new_updates([telebot.types.Update.de_json(update)])
    return "", 200

# === Set Webhook ===
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL + BOT_TOKEN)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
