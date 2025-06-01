import os
import logging
from flask import Flask, request
import telebot
import yt_dlp
import librosa
import soundfile as sf

# Logging voor debugging
logging.basicConfig(level=logging.DEBUG)

# Telegram bot config
TOKEN = "7739002753:AAFgh-UlgRkYCd20CUrnUbhJ36ApQQ6ZL7o"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is live"

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    logging.info("[Webhook] Update verwerkt")
    bot.process_new_updates([update])
    return '', 200

# /start commando
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "✅ Update ontvangen. Bot is actief.")

# YouTube-link verwerken
@bot.message_handler(func=lambda message: "youtu" in message.text.lower())
def handle_youtube(message):
    url = message.text.strip()
    bot.send_message(message.chat.id, "🎧 Download wordt gestart...")

    try:
        filename = "audio.mp3"
        # Download audio
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': filename,
            'quiet': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Analyseer BPM & Key
        y, sr = librosa.load(filename)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        key_index = chroma.mean(axis=1).argmax()
        key = ['C', 'C#', 'D', 'D#', 'E', 'F',
               'F#', 'G', 'G#', 'A', 'A#', 'B'][key_index]

        bot.send_message(message.chat.id, f"🎵 *Analyse Voltooid:*\nBPM: `{round(tempo)}`\nKey: `{key}`", parse_mode="Markdown")

        # Stuur mp3 terug
        with open(filename, "rb") as audio:
            bot.send_audio(message.chat.id, audio)

        os.remove(filename)

    except Exception as e:
        logging.error(f"Fout bij verwerking: {e}")
        bot.send_message(message.chat.id, "❌ Er is iets misgegaan bij het verwerken.")

# Zet Webhook bij start (Render only)
WEBHOOK_URL = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{TOKEN}"
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)
