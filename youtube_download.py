from yt_dlp import YoutubeDL
import os
import tempfile
import logging

def download_youtube_audio(url):
    try:
        output_path = os.path.join(tempfile.gettempdir(), "audio.%(ext)s")

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'quiet': True,
            'noplaylist': True,
            'cookiefile': 'cookies.txt',
            'user_agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                '(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
            ),
            'http_headers': {
                'User-Agent': (
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                    '(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
                ),
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
            },
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            audio_filename = os.path.join(tempfile.gettempdir(), "audio.wav")
            return audio_filename

    except Exception as e:
        logging.error(f"[DOWNLOAD FOUT] {e}")
        return None
