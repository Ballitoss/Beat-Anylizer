import os
import logging
import tempfile
import yt_dlp
import librosa
import telebot
from flask import Flask, request
from pydub import AudioSegment

TOKEN = "7739002753:AAFgh-UlgRkYCd20CUrnUbhJ36ApQQ6ZL7o"
URL = f"https://web-production-cfc73.up.railway.app/{TOKEN}"
bot = telebot.TeleBot(TOKEN)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

app = Flask(__name__)

COOKIES_FILE = "cookies.txt"

def download_youtube_audio(url):
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "audio.%(ext)s")
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'noplaylist': True,
            'quiet': True,
            'cookiefile': COOKIES_FILE,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return output_path.replace("%(ext)s", "mp3")

def analyze_audio(mp3_path):
    wav_path = mp3_path.replace(".mp3", ".wav")
    AudioSegment.from_mp3(mp3_path).export(wav_path, format="wav")
    y, sr = librosa.load(wav_path)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    key_index = chroma.mean(axis=1).argmax()
    key = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'][key_index]
    return round(tempo), key

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "🎶 Stuur een YouTube-link en ik analyseer het voor je!")

@bot.message_handler(func=lambda m: m.entities and m.entities[0].type == "url")
def handle_youtube_url(message):
    url = message.text.strip()
    bot.send_message(message.chat.id, "🎷 Downloaden en analyseren... een moment.")
    try:
        mp3_path = download_youtube_audio(url)
        bpm, key = analyze_audio(mp3_path)
        caption = f"🔢 Analyse voltooid:\n⏱ BPM: {bpm}\n♪ Key: {key}"
        with open(mp3_path, "rb") as audio:
            bot.send_audio(message.chat.id, audio, caption=caption)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Fout: {e}")

@app.route(f"/{TOKEN}", methods=['POST'])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=URL)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
