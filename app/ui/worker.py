# app/ui/worker.py
from PySide6.QtCore import QObject, Signal, Slot


class DownloadWorker(QObject):
    log_event = Signal(object)     # {"key": str, "args": dict}
    progress = Signal(int)         # 0..100 (global)
    status_key = Signal(str)       # "idle" | "downloading"
    finished = Signal()

    # NUEVO: updates por fila para la tabla
    item_update = Signal(int, str, int, str, str)
    # row, status_key ("queued","downloading","done","error"), pct, title, output_file

    def __init__(self, downloader, urls, fmt, quality):
        super().__init__()
        self.downloader = downloader
        self.urls = urls
        self.fmt = fmt
        self.quality = quality

        # contexto del ítem actual (para que hook sepa a qué fila actualizar)
        self._current_row = -1
        self._current_title = ""
        self._current_output = ""

    def hook(self, d):
        status = d.get("status")

        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes") or 0
            if total:
                pct = int((downloaded / total) * 100)
                pct = max(0, min(100, pct))

                # progreso global (si quieres: promedio simple por item)
                self.progress.emit(pct)

                # update por fila
                if self._current_row >= 0:
                    self.item_update.emit(
                        self._current_row, "downloading", pct, self._current_title, self._current_output
                    )

        elif status == "finished":
            self.log_event.emit({"key": "post_processing", "args": {}})

            # a veces d trae filename final/temporal
            fn = d.get("filename") or ""
            if fn:
                self._current_output = fn

    @Slot()
    def run(self):
        self.status_key.emit("downloading")
        self.progress.emit(0)

        total_items = len(self.urls)
        self.log_event.emit({"key": "starting_batch", "args": {"count": total_items}})

        for row, url in enumerate(self.urls):
            i = row + 1

            # marcar queued->downloading en tabla
            self._current_row = row
            self._current_title = url
            self._current_output = ""
            self.item_update.emit(row, "downloading", 0, "", "")

            self.log_event.emit({"key": "item_downloading", "args": {"i": i, "total": total_items, "url": url}})

            try:
                info = self.downloader.get_info(url)
                title = info.get("title") or url
                uploader = info.get("uploader") or info.get("channel") or ""
                duration = info.get("duration")  # seconds (int) or None
                thumbnail = info.get("thumbnail") or ""
                nice = f"{title}" + (f" — {uploader}" if uploader else "")

                self._current_title = nice
                self.log_event.emit({"key": "now_downloading", "args": {"title": nice}})

                # Emit metadata for the Now Downloading card
                self.log_event.emit({
                    "key": "current_item_meta",
                    "args": {
                        "title": title,
                        "uploader": uploader,
                        "duration": duration,
                        "thumbnail": thumbnail,
                        "url": url,
                        "index": i,
                        "total": total_items,
                    }
                })

                # update title en tabla (sin esperar progreso)
                self.item_update.emit(row, "downloading", 0, nice, "")

                result = self.downloader.download(
                    url,
                    format_type=self.fmt,
                    quality=self.quality,
                    progress_callback=self.hook,
                )

                # si downloader retorna filepath, lo mostramos (lo agregamos abajo)
                if isinstance(result, dict):
                    out_file = result.get("filepath") or ""
                else:
                    out_file = ""

                if out_file:
                    self._current_output = out_file

                self.item_update.emit(row, "done", 100, nice, self._current_output)
                self.log_event.emit({"key": "done", "args": {}})

            except Exception as e:
                self.item_update.emit(row, "error", 0, self._current_title or url, "")
                self.log_event.emit({"key": "error", "args": {"error": str(e)}})

        self.progress.emit(100)
        self.status_key.emit("idle")
        self.log_event.emit({"key": "all_done", "args": {}})
        self.finished.emit()
