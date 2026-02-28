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
from ClipWidget import ClipWidget
from ClipLoaderThread import ClipLoaderThread

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Twitch → YouTube Manager")
        self.resize(900, 800)

        central = QWidget()
        self.setCentralWidget(central)

        self.main_layout = QVBoxLayout(central)

        # Ввод ссылки
        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText(
            "Вставь название Twitch канала или ссылку на клип"
        )
        self.input_line.returnPressed.connect(self.load_clips)

        self.load_btn = QPushButton("Загрузить")
        self.load_btn.clicked.connect(self.load_clips)

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.input_line)
        top_layout.addWidget(self.load_btn)

        self.main_layout.addLayout(top_layout)

        # Scroll area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

        self.scroll_container = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_container)

        self.scroll.setWidget(self.scroll_container)

        self.main_layout.addWidget(self.scroll)

        # Кнопка публикации (внизу)
        self.publish_btn = QPushButton("Опубликовать выбранные")
        self.publish_btn.clicked.connect(self.publish_selected)

        self.main_layout.addWidget(self.publish_btn)

        self.clip_widgets = []

    def load_clips(self):
        url = self.input_line.text().strip()
        if not url:
            return

        self.load_btn.setEnabled(False)


        self.loader_thread = ClipLoaderThread(url, self)
        self.loader_thread.clips_loaded.connect(self.on_clips_loaded)
        self.loader_thread.start()

    def on_clips_loaded(self, clips):
        for widget in self.clip_widgets:
            widget.deleteLater()
        self.clip_widgets.clear()
        for clip in clips:
            print(clip)
            widget = ClipWidget(
                clip["title"],
                clip["thumbnail"],
                clip["video_url"],
                clip["timestamp"]
            )
            self.scroll_layout.addWidget(widget)
        self.load_btn.setEnabled(True)

    def publish_selected(self):
        selected = [
            w.get_data()
            for w in self.clip_widgets
            if w.is_selected()
        ]

        print("Публикуем:")
        for clip in selected:
            print("Название:", clip["title"])
            print("Описание:", clip["description"])
            print("URL:", clip["video_url"])
            print("------")

        # Здесь потом будет реальный upload на YouTube


    def get_clips(self, channel_url):

        ydl_opts = {
            "extract_flat": True,
        }
        
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(
                "https://www.twitch.tv/" + channel_url + "/videos?filter=clips&range=all",
                download=False
            )

        entries = info["entries"] if "entries" in info else [info]

        clips = [
            {
                "title": entry["title"],
                "thumbnail": entry.get("thumbnail", None),
                "video_url": entry["url"],
                "timestamp": entry.get("timestamp"),
            }
            for entry in entries
        ]
        clips.sort(key=lambda clip: clip["timestamp"], reverse=True)
        return clips


    def load_image_for_widget(self, widget):
        thread = ImageLoaderThread(widget, widget.thumbnail_url)
        thread.image_loaded.connect(self.on_image_loaded)
        thread.start()

    def on_image_loaded(self, widget, pixmap):
        widget.set_image(pixmap)