import os
import logging
from flask import Flask, request
import telebot
import yt_dlp
import librosa
import soundfile as sf
import requests

API_TOKEN = os.getenv("BOT_TOKEN") or "7739002753:AAFgh-UlgRkYCd20CUrnUbhJ36ApQQ6ZL7o"
bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)

@app.route(f"/{API_TOKEN}", methods=["POST"])
def webhook():
    json_string = request.get_data().decode("utf-8")
    logging.debug("[Webhook] JSON ontvangen: %s", json_string)
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    logging.info("[Webhook] Update verwerkt")
    return "!", 200

@bot.message_handler(commands=["start"])
def start_message(message):
    bot.send_message(message.chat.id, "👋 Stuur me een YouTube-link en ik analyseer de beat (key & bpm).")

@bot.message_handler(func=lambda message: "youtube.com" in message.text or "youtu.be" in message.text)
def handle_youtube_link(message):
    url = message.text.strip()
    user_id = message.chat.id
    bot.send_message(user_id, "🎷 Downloaden en analyseren van audio...")

    try:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": "audio.%(ext)s",
            "quiet": True,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192"
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        filename = "audio.wav"
        y, sr = librosa.load(filename, sr=None)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        key = librosa.key.key_to_note(librosa.key.estimate_tuning(y, sr=sr))

        response = f"🎼 **Analyse voltooid!**\n\n🔑 Key: `{key}`\n🕒 BPM: `{round(tempo)}`"
        bot.send_message(user_id, response, parse_mode="Markdown")

        with open(filename, "rb") as audio_file:
            bot.send_audio(user_id, audio_file)

    except Exception as e:
        logging.error("Fout bij verwerken van YouTube-link: %s", e)
        bot.send_message(user_id, f"❌ Fout bij verwerken van de link: {str(e)}")

@app.before_first_request
def setup_webhook():
    URL = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/{API_TOKEN}"
    bot.remove_webhook()
    bot.set_webhook(url=URL)
    logging.info(f"[Setup] Webhook ingesteld op: {URL}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
