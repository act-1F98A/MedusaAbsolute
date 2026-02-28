from PySide6.QtWidgets import (
    QMainWindow, QWidget,
    QVBoxLayout, QScrollArea, QLabel,
    QPushButton, QLineEdit, QHBoxLayout
)
from PySide6.QtCore import Qt, QTimer
from ClipWidget import ClipWidget
from ClipLoaderThread import ClipLoaderThread
from ImageLoaderThread import ImageLoaderThread


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

        # Статус
        self.status_label = QLabel("")
        self.main_layout.addWidget(self.status_label)

        # Scroll area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

        self.scroll_container = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_container)
        self.scroll_layout.addStretch()

        self.scroll.setWidget(self.scroll_container)
        self.scroll.verticalScrollBar().valueChanged.connect(self._on_scroll)

        self.main_layout.addWidget(self.scroll)

        # Кнопка публикации (внизу)
        self.publish_btn = QPushButton("Опубликовать выбранные")
        self.publish_btn.clicked.connect(self.publish_selected)

        self.main_layout.addWidget(self.publish_btn)

        self.clip_widgets = []
        self.loader_thread = None

        # Фоновый поток для загрузки картинок
        self.image_loader = ImageLoaderThread()
        self.image_loader.image_loaded.connect(self._on_image_loaded)
        self.image_loader.start()

        # Таймер для ленивой подгрузки картинок при скролле
        self._scroll_timer = QTimer()
        self._scroll_timer.setSingleShot(True)
        self._scroll_timer.setInterval(150)
        self._scroll_timer.timeout.connect(self._load_visible_images)

    def load_clips(self):
        channel = self.input_line.text().strip()
        if not channel:
            return

        self.load_btn.setEnabled(False)
        self.status_label.setText("Загрузка клипов...")

        # Очистить старые виджеты
        for widget in self.clip_widgets:
            widget.deleteLater()
        self.clip_widgets.clear()
        self.image_loader.clear_queue()

        self.loader_thread = ClipLoaderThread(channel)
        self.loader_thread.clip_ready.connect(self._on_clip_ready)
        self.loader_thread.finished_loading.connect(self._on_loading_finished)
        self.loader_thread.error_occurred.connect(self._on_error)
        self.loader_thread.start()

    def _on_clip_ready(self, clip):
        widget = ClipWidget(
            clip["title"],
            clip["thumbnail"],
            clip["video_url"],
            clip["timestamp"]
        )
        self.scroll_layout.insertWidget(self.scroll_layout.count() - 1, widget)
        self.clip_widgets.append(widget)

        self.status_label.setText(f"Загружено клипов: {len(self.clip_widgets)}")

        # Подгружаем картинку если виджет виден
        self._schedule_image_load(widget)

    def _on_loading_finished(self):
        self.load_btn.setEnabled(True)
        self.status_label.setText(
            f"Готово! Загружено клипов: {len(self.clip_widgets)}"
        )
        self._load_visible_images()

    def _on_error(self, error_msg):
        self.load_btn.setEnabled(True)
        self.status_label.setText(f"Ошибка: {error_msg}")

    def _on_scroll(self):
        self._scroll_timer.start()

    def _load_visible_images(self):
        if not self.clip_widgets:
            return

        viewport = self.scroll.viewport()
        viewport_height = viewport.height()
        margin = viewport_height

        visible = []
        for w in self.clip_widgets:
            if w.image_loaded:
                continue
            try:
                pos = w.mapTo(viewport, w.rect().topLeft())
                bottom = pos.y() + w.height()
                if -margin <= pos.y() <= viewport_height + margin or \
                   -margin <= bottom <= viewport_height + margin:
                    visible.append(w)
            except RuntimeError:
                continue

        if visible:
            self.image_loader.enqueue_batch(visible)

    def _schedule_image_load(self, widget):
        if widget.image_loaded or not widget.thumbnail_url:
            return
        viewport = self.scroll.viewport()
        try:
            pos = widget.mapTo(viewport, widget.rect().topLeft())
            if -200 <= pos.y() <= viewport.height() + 200:
                self.image_loader.enqueue(widget)
        except RuntimeError:
            pass

    def _on_image_loaded(self, widget, pixmap):
        widget.set_image(pixmap)

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

    def closeEvent(self, event):
        self.image_loader.stop()
        if self.loader_thread and self.loader_thread.isRunning():
            self.loader_thread.quit()
            self.loader_thread.wait()
        super().closeEvent(event)