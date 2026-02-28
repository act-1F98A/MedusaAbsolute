from collections import deque

from PySide6.QtGui import QPixmap
from PySide6.QtCore import QThread, Signal, QMutex, QWaitCondition
import requests


class ImageLoaderThread(QThread):
    image_loaded = Signal(object, QPixmap)

    def __init__(self):
        super().__init__()
        self._queue = deque()
        self._mutex = QMutex()
        self._condition = QWaitCondition()
        self._running = True

    def enqueue(self, widget):
        self._mutex.lock()
        if widget not in self._queue:
            self._queue.appendleft(widget)
        self._mutex.unlock()
        self._condition.wakeOne()

    def set_queue(self, widgets):
        self._mutex.lock()
        self._queue = deque(widgets)
        self._mutex.unlock()
        self._condition.wakeOne()

    def clear_queue(self):
        self._mutex.lock()
        self._queue.clear()
        self._mutex.unlock()

    def stop(self):
        self._running = False
        self._condition.wakeOne()
        self.wait()

    def run(self):
        while self._running:
            self._mutex.lock()
            if not self._queue:
                self._condition.wait(self._mutex)
            if not self._running:
                self._mutex.unlock()
                break
            if not self._queue:
                self._mutex.unlock()
                continue
            widget = self._queue.popleft()
            self._mutex.unlock()

            if widget.image_loaded:
                continue

            url = widget.thumbnail_url
            if not url:
                continue

            try:
                response = requests.get(url, timeout=10)
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                if not pixmap.isNull():
                    self.image_loaded.emit(widget, pixmap)
            except Exception:
                pass
