from PySide6.QtCore import QThread, Signal
from yt_dlp import YoutubeDL


class ClipLoaderThread(QThread):
    clip_ready = Signal(dict)
    finished_loading = Signal()
    error_occurred = Signal(str)

    def __init__(self, channel_name):
        super().__init__()
        self.channel_name = channel_name

    def run(self):
        try:
            ydl_opts = {"extract_flat": True}
            url = f"https://www.twitch.tv/{self.channel_name}/videos?filter=clips&range=all"

            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            entries = info.get("entries", [info])

            clips = [
                {
                    "title": entry["title"],
                    "thumbnail": entry.get("thumbnail"),
                    "video_url": entry["url"],
                    "timestamp": entry.get("timestamp"),
                }
                for entry in entries
            ]
            clips.sort(key=lambda c: c.get("timestamp") or 0, reverse=True)

            for clip in clips:
                self.clip_ready.emit(clip)

        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            self.finished_loading.emit()
