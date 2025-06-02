import os
import logging
import tempfile
import telebot
import librosa
import numpy as np
import soundfile as sf
from flask import Flask, request
from yt_dlp import YoutubeDL

# Logging
logging.basicConfig(level=logging.DEBUG)

# Telegram + Flask setup
TOKEN = '7739002753:AAFgh-UlgRkYCd20CUrnUbhJ36ApQQ6ZL7o'
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Audio downloader
def download_youtube_audio(url, output_path="audio.mp3"):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'noplaylist': True,
        'quiet': True,
        'cookiefile': 'cookies.txt',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'user_agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        ),
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return output_path
    except Exception as e:
        logging.error(f"[DOWNLOAD FOUT] {e}")
        raise

# Analyse BPM + key
def analyse_audio(file_path):
    y, sr = librosa.load(file_path)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    chroma = librosa.feature.chroma_cens(y=y, sr=sr)
    key = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'][np.argmax(chroma.mean(axis=1))]
    return tempo, key

# /start
@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, "
