from PySide6.QtCore import QThread, Signal
from yt_dlp import YoutubeDL

BATCH_SIZE = 20


class ClipLoaderThread(QThread):
    clip_ready = Signal(dict)
    finished_loading = Signal()
    error_occurred = Signal(str)

    def __init__(self, channel_name):
        super().__init__()
        self.channel_name = channel_name
        self._stopped = False

    def stop(self):
        self._stopped = True

    def run(self):
        try:
            base_url = f"https://www.twitch.tv/{self.channel_name}/videos?filter=clips&range=all"
            offset = 1

            while not self._stopped:
                ydl_opts = {
                    "extract_flat": True,
                    "playliststart": offset,
                    "playlistend": offset + BATCH_SIZE - 1,
                }

                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(base_url, download=False)

                entries = info.get("entries") or []
                if not entries:
                    break

                for entry in entries:
                    if self._stopped:
                        break
                    clip = {
                        "title": entry.get("title", ""),
                        "thumbnail": entry.get("thumbnail"),
                        "video_url": entry.get("url", ""),
                        "timestamp": entry.get("timestamp"),
                    }
                    self.clip_ready.emit(clip)

                if len(entries) < BATCH_SIZE:
                    break

                offset += BATCH_SIZE

        except Exception as e:
            if not self._stopped:
                self.error_occurred.emit(str(e))
        finally:
            self.finished_loading.emit()
