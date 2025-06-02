import os
import logging
import tempfile
import yt_dlp
import librosa
import telebot
from flask import Flask, request
from pydub import AudioSegment

# Botconfig
TOKEN = "7739002753:AAFgh-UlgRkYCd20CUrnUbhJ36ApQQ6ZL7o"
URL = f"https://web-production-cfc73.up.railway.app/{TOKEN}"
bot = telebot.TeleBot(TOKEN)

# Logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

# Flask app
app = Flask(__name__)

# YouTube download & analyse
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
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.download([url])
            mp3_path = output_path.replace("%(ext)s", "mp3")
            return mp3_path
        except Exception as e:
            logger.error(f"[DOWNLOAD FOUT] {e}")
            raise

def analyze_audio(mp3_path):
    try:
        wav_path = mp3_path.replace(".mp3", ".wav")
        sound = AudioSegment.from_mp3(mp3_path)
        sound.export(wav_path, format="wav")

        y, sr = librosa.load(wav_path)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        key_index = chroma.mean(axis=1).argmax()
        key = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'][key_index]

        return round(tempo), key
    except Exception as e:
        logger.error(f"[ANALYSE FOUT] {e}")
        raise

# Telegram handlers
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

# Webhook handler
@app.route(f"/{TOKEN}", methods=['POST'])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    logger.debug(f"[Webhook] JSON ontvangen: {json_str}")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200

# Main
if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=URL)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
