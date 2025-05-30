import telebot
import os
import uuid
import yt_dlp
from pydub import AudioSegment
import librosa
import numpy as np
import traceback

# === CONFIG ===
BOT_TOKEN = "7739002753:AAFgh-UlgRkYCd20CUrnUbhJ36ApQQ6ZL7o"
DOWNLOAD_DIR = "downloads"

# === INIT ===
bot = telebot.TeleBot(BOT_TOKEN)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# === HULPFUNCTIES ===
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
        info = ydl.extract_info(url, download=True)
        mp3_path = os.path.join(DOWNLOAD_DIR, filename + ".mp3")
        return mp3_path

def analyze_beat(path):
    y, sr = librosa.load(path)
    tempo_array, _ = librosa.beat.beat_track(y=y, sr=sr)
    tempo = float(tempo_array) if isinstance(tempo_array, (float, int)) else float(tempo_array[0])
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    key_index = chroma.mean(axis=1).argmax()
    keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    key = keys[key_index]
    return round(tempo), key

# === COMMANDOS ===
@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, 
        "🎶 Welkom bij *Beat Analyzer Bot*!\n\n"
        "Stuur een YouTube-link van een beat en je ontvangt automatisch:\n"
        "✅ BPM\n✅ Key\n✅ MP3-download van de audio\n\n"
        "👉 Voor premiumfuncties zoals sample-detectie, gebruik `/subscribe`",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['subscribe'])
def handle_subscribe(message):
    bot.send_message(
        message.chat.id,
        "💳 Om toegang te krijgen tot premium functies:\n"
        "👉 [Klik hier om te betalen via PayPal](https://www.paypal.me/Balskiee)\n\n"
        "Na betaling: stuur `/verify` of neem contact op.",
        parse_mode="Markdown"
    )

# === LINK HANDLER ===
@bot.message_handler(func=lambda msg: True)
def handle_link(message):
    url = message.text.strip()
    if not url.startswith("http"):
        bot.reply_to(message, "❌ Stuur een geldige YouTube-link aub.")
        return

    bot.reply_to(message, "⏬ Downloaden en analyseren van je beat, even geduld...")

    try:
        uid = str(uuid.uuid4())
        mp3_path = download_audio(url, uid)
        tempo, key = analyze_beat(mp3_path)

        caption = f"✅ *Analyse voltooid!*\n🎵 BPM: `{tempo}`\n🎹 Key: `{key}`"
        with open(mp3_path, 'rb') as audio:
            bot.send_audio(
                message.chat.id,
                audio,
                caption=caption,
                performer="BeatAnalyzer",
                title=f"Beat {tempo}BPM in {key}",
                parse_mode="Markdown"
            )

    except Exception as e:
        traceback.print_exc()
        bot.reply_to(message, f"❌ Analyse fout: `{e}`", parse_mode="Markdown")

# === START ===
print("🤖 Bot draait...")
bot.infinity_polling()
