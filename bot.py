import os
import logging
import yt_dlp
import telebot
from flask import Flask, request

# Vaste token direct ingevuld
TOKEN = "7739002753:AAFgh-UlgRkYCd20CUrnUbhJ36ApQQ6ZL7o"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    logging.debug(f"[Webhook] JSON ontvangen: {json_str}")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    logging.info("[Webhook] Update verwerkt")
    return '', 200

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(
        message.chat.id,
        "🎧 Welkom bij de *Beat Analyzer Bot*!\n\n"
        "Stuur een YouTube-link om de beat te analyseren (BPM + sleutel).",
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda msg: msg.text and ("youtube.com" in msg.text or "youtu.be" in msg.text))
def handle_youtube(message):
    bot.send_message(message.chat.id, "🔍 Download wordt gestart...")

    try:
        url = message.text.strip()
        output_path = "audio.mp3"

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'quiet': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        bot.send_audio(message.chat.id, audio=open(output_path, 'rb'))
        os.remove(output_path)

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Fout bij downloaden: {str(e)}")

@app.route('/', methods=['GET'])
def index():
    return "Service draait!"

# Start de app alleen lokaal (Render gebruikt gunicorn)
if __name__ == "__main__":
    app.run(debug=True)
