import os
import logging
from flask import Flask, request
import telebot
from yt_dlp import YoutubeDL
import librosa
import soundfile as sf
import uuid

# Logging inschakelen
logging.basicConfig(level=logging.DEBUG)

TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Audio-analysefunctie
def analyseer_audio(pad):
    try:
        y, sr = librosa.load(pad)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        key = librosa.key.key_to_note(librosa.key.estimate_key(y, sr))
        return f"BPM: {round(tempo)}\nKey: {key}"
    except Exception as e:
        logging.error(f"Fout bij analyse: {e}")
        return "Fout bij analyseren van audio."

# YouTube-download en analyse
def verwerk_youtube_link(link):
    try:
        bestandnaam = f"audio_{uuid.uuid4()}.mp3"
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": bestandnaam,
            "quiet": True,
            "noplaylist": True,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])

        analyse_resultaat = analyseer_audio(bestandnaam)
        return bestandnaam, analyse_resultaat
    except Exception as e:
        logging.error(f"Fout bij analyse: {e}")
        return None, "Fout bij het downloaden of analyseren van de video."

# Webhook handler
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json()
    logging.debug(f"[Webhook] JSON ontvangen: {update}")
    if update:
        bot.process_new_updates([telebot.types.Update.de_json(update)])
    return "ok", 200

# Start commando
@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, "🎶 Welkom bij de Beat Analyzer Bot!\nStuur een YouTube-link en ik geef je BPM + toonhoogte.")

# Link-handler
@bot.message_handler(func=lambda msg: msg.text and "youtube.com" in msg.text or "youtu.be" in msg.text)
def handle_youtube_link(message):
    bestand, analyse = verwerk_youtube_link(message.text)
    if bestand:
        with open(bestand, "rb") as audio:
            bot.send_audio(message.chat.id, audio)
        bot.send_message(message.chat.id, analyse)
        os.remove(bestand)
    else:
        bot.send_message(message.chat.id, analyse)

# Root
@app.route("/")
def index():
    return "🎵 Beat Analyzer draait."

# Exporteer app voor Gunicorn
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
