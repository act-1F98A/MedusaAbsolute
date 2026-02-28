from PySide6.QtCore import Qt, QUrl, QThread, Signal
from ClipWidget import ClipWidget
class ClipLoaderThread(QThread):
    clips_loaded = Signal(list)

    def __init__(self, url, mainWindow):
        super().__init__()
        self.url = url
        self.mainWindow = mainWindow

    def run(self):
        clips = self.mainWindow.get_clips(self.url)

        self.clips_loaded.emit(clips)
