from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QUrl, QThread, Signal
import requests

class ImageLoaderThread(QThread):
    def __init__(self, main_window):
        self.main_window = main_window
        self.queue = []
        self.loading = False

    def update_queue(self):
        widgets = self.main_window.clip_widgets
        if not widgets:
            return

        scroll = self.main_window.scroll
        viewport = scroll.viewport()

        # Найдём видимые индексы
        first_visible = None
        last_visible = None

        for i, w in enumerate(widgets):
            pos = w.mapTo(viewport, w.rect().topLeft())
            if 0 <= pos.y() <= viewport.height():
                if first_visible is None:
                    first_visible = i
                last_visible = i

        if first_visible is None:
            return

        start = max(0, first_visible - 20)
        end = min(len(widgets) - 1, last_visible + 20)

        center_y = viewport.height() // 2

        candidates = []

        for i in range(start, end + 1):
            w = widgets[i]
            if w.image_loaded:
                continue

            pos = w.mapTo(viewport, w.rect().center())
            distance = abs(pos.y() - center_y)

            candidates.append((distance, w))

        candidates.sort(key=lambda x: x[0])

        self.queue = [w for _, w in candidates]

        if not self.loading:
            self.load_next()

    def load_next(self):
        if not self.queue:
            self.loading = False
            return

        self.loading = True
        widget = self.queue.pop(0)

        thread = ImageLoaderThread(widget, widget.thumbnail_url)
        thread.image_loaded.connect(self.on_image_loaded)
        thread.start()

        self.current_thread = thread

    def on_image_loaded(self, widget, pixmap):
        widget.set_image(pixmap)
        self.load_next()
