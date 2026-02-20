# app/ui/worker.py
from PySide6.QtCore import QObject, Signal, Slot


class DownloadWorker(QObject):
    log_event = Signal(object)     # {"key": str, "args": dict}
    progress = Signal(int)         # 0..100
    status_key = Signal(str)       # "idle" | "downloading"
    finished = Signal()

    def __init__(self, downloader, urls, fmt, quality):
        super().__init__()
        self.downloader = downloader
        self.urls = urls
        self.fmt = fmt
        self.quality = quality

    def hook(self, d):
        status = d.get("status")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes") or 0
            if total:
                pct = int((downloaded / total) * 100)
                self.progress.emit(pct)
        elif status == "finished":
            self.log_event.emit({"key": "post_processing", "args": {}})

    @Slot()
    def run(self):
        self.status_key.emit("downloading")
        self.progress.emit(0)

        total_items = len(self.urls)
        self.log_event.emit({"key": "starting_batch", "args": {"count": total_items}})

        for i, url in enumerate(self.urls, start=1):
            self.log_event.emit({"key": "item_downloading", "args": {"i": i, "total": total_items, "url": url}})
            try:
                self.downloader.download(
                    url,
                    format_type=self.fmt,
                    quality=self.quality,
                    progress_callback=self.hook,
                )
                self.log_event.emit({"key": "done", "args": {}})
            except Exception as e:
                self.log_event.emit({"key": "error", "args": {"error": str(e)}})

        self.progress.emit(100)
        self.status_key.emit("idle")
        self.log_event.emit({"key": "all_done", "args": {}})
        self.finished.emit()