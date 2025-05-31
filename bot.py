import os
import uuid
import yt_dlp
import librosa
import numpy as np
from flask import Flask, request
from telebot import TeleBot, types

# === CONFIG ===
BOT_TOKEN = "7739002753:AAFgh-UlgRkYCd20CUrnUbhJ36ApQQ6ZL7o"
WEBHOOK_URL = "https://beat-anylizer-1.onrender.com"
DOWNLOAD_DIR = "downloads"

# === INIT ===
bot = TeleBot(BOT_TOKEN)
app = Flask(__name__)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# === HELPER FUNCTIONS ===
def download_audio(url, filename):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(DOWNLOAD_DIR, filename + '.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return os.path.join(DOWNLOAD_DIR, filename + ".mp3")

def analyze_beat(path):
    y, sr = librosa.load(path)
    tempo_data, _ = librosa.beat.beat_track(y=y, sr=sr)
    tempo = float(tempo_data) if isinstance(tempo_data, (float, int)) else float(tempo_data[0])
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    key_index = chroma.mean(axis=1).argmax()
    keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    key = keys[key_index]
    return round(tempo), key

# === FLASK WEBHOOK ENDPOINT ===
@app.route('/', methods=['GET'])
def index():
    return "✅ Beat Analyzer draait!"

@app.route(f"/{BOT_TOKEN}", methods=['POST'])
def webhook():
    try:
        json_string = request.get_data().decode('utf-8')
        update = types.Update.de_json(json_string)
        message = update.message

        if message.text == "/start":
            print("[DEBUG] /start ontvangen")
            bot.send_message(
                message.chat.id,
                "🎶 *Welkom bij Beat Analyzer Bot!*\n\nStuur me een YouTube-link en ik geef je de BPM + key terug.\n\n💸 Steun via [paypal.me/Balskiee](https://paypal.me/Balskiee)",
                parse_mode="Markdown"
            )

        elif message.text.startswith("http"):
            print("[DEBUG] YouTube link ontvangen:", message.text)
            bot.send_message(message.chat.id, "⏬ Downloaden en analyseren, momentje...")

            try:
                uid = str(uuid.uuid4())
                mp3_path = download_audio(message.text, uid)
                tempo, key = analyze_beat(mp3_path)

                caption = f"✅ *Analyse voltooid!*\n🎵 BPM: `{tempo}`\n🎹 Key: `{key}`"
                with open(mp3_path, 'rb') as audio:
                    bot.send_audio(
                        message.chat.id,
                        audio,
                        caption=caption,
                        parse_mode="Markdown"
                    )
            except Exception as e:
                print("[ERROR] tijdens analyse:", e)
                bot.send_message(message.chat.id, f"❌ Analyse fout:\n`{e}`", parse_mode="Markdown")

        else:
            print("[DEBUG] Onbekend bericht ontvangen:", message.text)
            bot.send_message(message.chat.id, "❌ Ongeldige input. Stuur een YouTube-link.")

    except Exception as e:
        print(f"[ERROR] Webhook crash: {e}")
    return '', 200

# === STARTUP ===
if __name__ == "__main__":
    import telebot.apihelper
    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/{BOT_TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
