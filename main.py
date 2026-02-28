from MainWindow import MainWindow 
from yt_dlp import YoutubeDL
import sys
import requests
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QScrollArea, QLabel,
    QPushButton, QLineEdit, QHBoxLayout
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QUrl
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from yt_dlp import YoutubeDL

def get_clips(channel_url):
    ydl_opts = {"extract_flat": True}

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(channel_url, download=False)

    clips = []

    for entry in info["entries"]:
        clips.append({
            "title": entry["title"],
            "url": entry["url"],
            "thumbnail": entry.get("thumbnail")
        })

    return clips

chanale = "wolfofthebox"
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
# get_clips(f"https://www.twitch.tv/{chanale}/videos?filter=clips&range=all")

# ydl_opts = {"extract_flat": True}
# chanale = "wolfofthebox"

# with YoutubeDL(ydl_opts) as ydl:
    # info = ydl.extract_info(
        # f"https://www.twitch.tv/{chanale}/videos?filter=clips&range=all"
    # )

# for entry in info["entries"]:
    # print(entry["title"], entry["url"])