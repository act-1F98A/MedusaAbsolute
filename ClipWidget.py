from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget,
    QVBoxLayout, QScrollArea, QLabel,
    QPushButton, QLineEdit, QHBoxLayout,
    QTextEdit, QCheckBox
)
from datetime import datetime
from PySide6.QtGui import QPixmap, QFontMetrics
from PySide6.QtCore import Qt, QUrl
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
import requests

class ClipWidget(QWidget):
    def __init__(self, title, thumbnail_url, video_url, timestamp):
        super().__init__()
        

        self.image_loaded = False
        
        self.video_url = video_url

        main_layout = QHBoxLayout(self)

        # Чекбокс
        self.checkbox = QCheckBox()
        main_layout.addWidget(self.checkbox)
        self.checkbox.setStyleSheet(
            "border: none;"
            "outline: none;"
        )

        # ===== Контейнер под видео/превью =====
        self.preview_container = QWidget()
        self.preview_container.setFixedSize(320, 180)

        container_layout = QVBoxLayout(self.preview_container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        self.thumbnail = QLabel("Loading...")
        self.thumbnail.setFixedSize(320, 180)
        self.thumbnail.setAlignment(Qt.AlignCenter)
        # pixmap = self.load_image(thumbnail_url)
        # if pixmap:
            # self.thumbnail.setPixmap(
                # pixmap.scaled(320, 180, Qt.KeepAspectRatio)
            # )

        container_layout.addWidget(self.thumbnail)

        self.date_label = QLabel(self.preview_container)
        self.date_label.setStyleSheet(
            "color: #222222;"
            "background-color: rgba(0,0,0,120);"
            "border-radius: 10px;"
            "border: none;"
            "outline: none;"
        )
        self.date_label.setAlignment(Qt.AlignRight)
        
        if timestamp:
            dt = datetime.fromtimestamp(timestamp)
            self.date_label.setText(dt.strftime("%H:%M %d.%m.%Y"))

        metrics = QFontMetrics(self.date_label.font())
        text = self.date_label.text()

        text_width = metrics.horizontalAdvance(text)
        text_height = metrics.height()

        padding_x = 15
        padding_y = 10

        self.date_label.setFixedSize(
            text_width + padding_x,
            text_height + padding_y
        )

        main_layout.addWidget(self.preview_container)

        right_layout = QVBoxLayout()
        self.title_edit = QLineEdit(title)
        self.title_edit.setPlaceholderText("Название...")
        right_layout.addWidget(self.title_edit)

        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Описание...")
        self.description_edit.setFixedHeight(100)
        right_layout.addWidget(self.description_edit)

        main_layout.addLayout(right_layout)


        self.setStyleSheet("border: 1px solid gray; padding: 6px;")

    def load_image(self, url):
        try:
            response = requests.get(url)
            pixmap = QPixmap()
            pixmap.loadFromData(response.content)
            return pixmap
        except:
            return None

    def is_selected(self):
        return self.checkbox.isChecked()

    def get_data(self):
        return {
            "title": self.title_edit.text(),
            "description": self.description_edit.toPlainText(),
            "video_url": self.video_url
        }
