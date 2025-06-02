import telebot
import os
import logging
from flask import Flask, request
from youtube_download import download_youtube_audio
import librosa

API_TOKEN = '7739002753:AAFgh-UlgRkYCd20CUrnUbhJ36ApQQ6ZL7o'
WEBHOOK_URL = 'https://web-production-cfc73.up.railway.app/' + API_TOKEN

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

def analyze_audio(file_path):
    try:
        y, sr = librosa.load(file_path)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        avg_chroma = chroma.mean(axis=1)
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        key_index = avg_chroma.argmax()
        key = note_names[key_index]
        return tempo, key
    except Exception as e:
        logging.error(f"Fout bij analyse: {e}")
        return None, None

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, "🎧 Stuur me een YouTube-link van een beat, dan analyseer ik de BPM en Key.")

@bot.message_handler(func=lambda msg: msg.text and 'youtu' in msg.text)
def handle_youtube_link(message):
    url = message.text.strip()
    user_id = message.chat.id
    logging.debug(f"Ontvangen YouTube-link: {url}")

    file_path = download_youtube_audio(url, output_path="audio.mp3")
    if file_path is None:
        bot.send_message(user_id, "❌ Fout bij het downloaden van de audio.")
        return

    tempo, key = analyze_audio(file_path)
    if tempo and key:
        bot.send_message(user_id, f"✅ Analyse voltooid:\n🔑 Key: {key}\n🎶 BPM: {int(tempo)}")
    else:
        bot.send_message(user_id, "⚠️ Er ging iets mis bij de analyse.")
    
    try:
        os.remove("audio.mp3")
    except Exception:
        pass

@app.route('/' + API_TOKEN, methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    logging.debug(f"[Webhook] JSON ontvangen: {json_string}")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    logging.info("[Webhook] Update verwerkt")
    return '', 200

@app.route('/')
def index():
    return '✅ Telegram Bot draait!', 200

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host='0.0.0.0', port=8080)
