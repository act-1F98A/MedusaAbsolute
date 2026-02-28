from PySide6.QtCore import QThread, Signal
from yt_dlp import YoutubeDL

EMIT_BATCH = 20


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
            url = f"https://www.twitch.tv/{self.channel_name}/videos?filter=clips&range=all"
            ydl_opts = {"extract_flat": True}

            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            if self._stopped:
                return

            entries = info.get("entries") or []

            clips = [
                {
                    "title": entry.get("title", ""),
                    "thumbnail": entry.get("thumbnail"),
                    "video_url": entry.get("url", ""),
                    "timestamp": entry.get("timestamp"),
                }
                for entry in entries
            ]
            clips.sort(key=lambda c: c.get("timestamp") or 0, reverse=True)

            for clip in clips:
                if self._stopped:
                    break
                self.clip_ready.emit(clip)

        except Exception as e:
            if not self._stopped:
                self.error_occurred.emit(str(e))
        finally:
            self.finished_loading.emit()
