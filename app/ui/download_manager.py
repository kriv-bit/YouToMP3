"""Concurrent download coordinator.

`DownloadManager` schedules one or more `DownloadJob`s in parallel up to a
configurable concurrency, supports per-item cancellation and queue-level
pause/resume, and re-emits a single aggregated set of Qt signals so the
controller can stay simple.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Signal, Slot

from app.downloader import DownloadCancelled
from app.ui.worker import _metadata_payload, _needs_metadata

# Item shape mirrors the existing queue.get_queued_rows() contract:
#   (row_id, url, fmt, meta_dict)
Item = tuple[str, str, str, dict]


class DownloadJob(QObject):
    """Runs a single download in its own QThread, with cooperative cancellation."""

    progress = Signal(int)
    log_event = Signal(object)
    item_update = Signal(str, str, int, str, str)
    finished = Signal(str, str)  # row_id, final_status ("done" | "cancelled" | "error")

    def __init__(
        self,
        downloader,
        row_id: str,
        url: str,
        fmt: str,
        quality: str,
        meta: dict | None,
        *,
        index: int = 0,
        total: int = 0,
    ):
        super().__init__()
        self._downloader = downloader
        self._row_id = row_id
        self._url = url
        self._fmt = fmt
        self._quality = quality
        self._meta = dict(meta or {})
        self._index = index
        self._total = total

        self._cancelled = False
        self._current_title = str(self._meta.get("title") or "")
        self._current_output = ""

    @Slot()
    def cancel(self):
        self._cancelled = True

    @property
    def is_cancelled(self) -> bool:
        return self._cancelled

    @property
    def row_id(self) -> str:
        return self._row_id

    def hook(self, data):
        if self._cancelled:
            raise DownloadCancelled()

        status = data.get("status")
        if status == "downloading":
            total = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
            downloaded = data.get("downloaded_bytes") or 0
            if total:
                pct = int((downloaded / total) * 100)
                pct = max(0, min(100, pct))
                self.progress.emit(pct)
                self.item_update.emit(
                    self._row_id,
                    "downloading",
                    pct,
                    self._current_title,
                    self._current_output,
                )

        elif status == "finished":
            self.log_event.emit({"key": "post_processing", "args": {}})
            filename = data.get("filename") or ""
            if filename:
                self._current_output = filename

    @Slot()
    def run(self):
        if self._cancelled:
            self._emit_cancelled()
            return

        self.item_update.emit(self._row_id, "downloading", 0, self._current_title, "")
        self.log_event.emit(
            {
                "key": "item_downloading",
                "args": {"i": self._index, "total": self._total, "url": self._url},
            }
        )

        try:
            if _needs_metadata(self._meta):
                info = self._downloader.get_info(self._url)
                self._meta = _metadata_payload(info, self._url)

            title = self._meta.get("title") or self._url
            uploader = self._meta.get("uploader") or ""
            duration = self._meta.get("duration")
            thumbnail = self._meta.get("thumbnail") or ""
            nice = f"{title}" + (f" - {uploader}" if uploader else "")
            self._current_title = title

            self.log_event.emit({"key": "now_downloading", "args": {"title": nice}})
            self.log_event.emit(
                {
                    "key": "current_item_meta",
                    "args": {
                        "title": title,
                        "uploader": uploader,
                        "duration": duration,
                        "thumbnail": thumbnail,
                        "url": self._url,
                        "index": self._index,
                        "total": self._total,
                    },
                }
            )

            self.item_update.emit(self._row_id, "downloading", 0, title, "")

            result = self._downloader.download(
                self._url,
                format_type=self._fmt,
                quality=self._quality,
                progress_callback=self.hook,
            )

            out_file = ""
            artwork_warning = ""
            if isinstance(result, dict):
                out_file = result.get("filepath") or ""
                title = result.get("title") or title
                artwork_warning = result.get("artwork_warning") or ""

            if out_file:
                self._current_output = out_file

            self.item_update.emit(self._row_id, "done", 100, title, self._current_output)
            if artwork_warning:
                self.log_event.emit({"key": "artwork_warning", "args": {"warning": artwork_warning}})
            self.log_event.emit({"key": "done", "args": {}})
            self.finished.emit(self._row_id, "done")

        except DownloadCancelled:
            self._emit_cancelled()

        except Exception as exc:
            # yt-dlp may wrap our DownloadCancelled inside its own DownloadError;
            # if we already flagged cancellation, treat it as cancel rather than error.
            if self._cancelled:
                self._emit_cancelled()
                return
            self.item_update.emit(
                self._row_id, "error", 0, self._current_title or self._url, ""
            )
            self.log_event.emit({"key": "error", "args": {"error": str(exc)}})
            self.finished.emit(self._row_id, "error")

    def _emit_cancelled(self):
        self.item_update.emit(
            self._row_id, "cancelled", 0, self._current_title or self._url, ""
        )
        self.log_event.emit(
            {"key": "cancelled", "args": {"title": self._current_title or self._url}}
        )
        self.finished.emit(self._row_id, "cancelled")


class DownloadManager(QObject):
    """Schedules concurrent DownloadJob workers and aggregates their signals."""

    progress = Signal(int)
    status_key = Signal(str)
    log_event = Signal(object)
    item_update = Signal(str, str, int, str, str)
    finished = Signal()
    job_started = Signal(str)
    job_finished = Signal(str, str)

    def __init__(self, downloader, parent: QObject | None = None):
        super().__init__(parent)
        self._downloader = downloader
        self._concurrency = 1
        self._paused = False
        self._running_anything = False

        self._fmt = "mp3"
        self._quality = "192"

        self._pending: list[Item] = []
        self._running: dict[str, tuple[QThread, DownloadJob]] = {}
        self._item_progress: dict[str, int] = {}
        self._total = 0
        self._jobs_started = 0

    # ---- public API ----

    def set_concurrency(self, n: int):
        try:
            value = int(n)
        except (TypeError, ValueError):
            value = 1
        self._concurrency = max(1, min(4, value))
        if self._running_anything:
            self._maybe_dispatch()

    @property
    def concurrency(self) -> int:
        return self._concurrency

    @property
    def is_running(self) -> bool:
        return self._running_anything

    @property
    def is_paused(self) -> bool:
        return self._paused

    @property
    def active_count(self) -> int:
        return len(self._running)

    @Slot()
    def start(self, items, fmt: str, quality: str):
        if self._running_anything:
            return
        self._pending = list(items)
        self._fmt = fmt
        self._quality = quality
        self._total = len(self._pending)
        self._item_progress = {item[0]: 0 for item in self._pending}
        self._jobs_started = 0
        self._paused = False
        self._running_anything = True

        self.status_key.emit("downloading")
        self.progress.emit(0)
        self.log_event.emit({"key": "starting_batch", "args": {"count": self._total}})

        if not self._pending:
            self._wrap_up()
            return

        self._maybe_dispatch()

    @Slot()
    def pause(self):
        if not self._running_anything or self._paused:
            return
        self._paused = True
        self.status_key.emit("paused")
        self.log_event.emit({"key": "queue_paused", "args": {}})

    @Slot()
    def resume(self):
        if not self._running_anything or not self._paused:
            return
        self._paused = False
        self.status_key.emit("downloading")
        self.log_event.emit({"key": "queue_resumed", "args": {}})
        self._maybe_dispatch()

    @Slot(str)
    def cancel_item(self, row_id: str):
        if row_id in self._running:
            _, job = self._running[row_id]
            job.cancel()
            return

        for i, item in enumerate(self._pending):
            if item[0] == row_id:
                del self._pending[i]
                title = (item[3] or {}).get("title", "") or item[1]
                self.item_update.emit(row_id, "cancelled", 0, title, "")
                self._item_progress[row_id] = 100
                self._emit_progress()
                self._maybe_wrap_up()
                return

    @Slot()
    def cancel_all(self):
        if not self._running_anything:
            return
        for _, job in list(self._running.values()):
            job.cancel()

        for item in self._pending:
            row_id = item[0]
            title = (item[3] or {}).get("title", "") or item[1]
            self.item_update.emit(row_id, "cancelled", 0, title, "")
            self._item_progress[row_id] = 100
        self._pending.clear()
        self._emit_progress()
        self._maybe_wrap_up()

    # ---- internal ----

    def _maybe_dispatch(self):
        while (
            self._running_anything
            and not self._paused
            and len(self._running) < self._concurrency
            and self._pending
        ):
            self._spawn_job(self._pending.pop(0))

    def _spawn_job(self, item: Item):
        row_id, url, item_fmt, meta = item
        self._jobs_started += 1

        thread = QThread(self)
        job = DownloadJob(
            self._downloader,
            row_id=row_id,
            url=url,
            fmt=item_fmt or self._fmt,
            quality=self._quality,
            meta=meta,
            index=self._jobs_started,
            total=self._total,
        )
        job.moveToThread(thread)

        job.progress.connect(lambda pct, rid=row_id: self._on_job_progress(rid, pct))
        job.log_event.connect(self.log_event)
        job.item_update.connect(self.item_update)
        job.finished.connect(self._on_job_finished)

        thread.started.connect(job.run)
        job.finished.connect(thread.quit)
        job.finished.connect(job.deleteLater)
        thread.finished.connect(thread.deleteLater)

        self._running[row_id] = (thread, job)
        self.job_started.emit(row_id)
        thread.start()

    @Slot(str, int)
    def _on_job_progress(self, row_id: str, pct: int):
        self._item_progress[row_id] = pct
        self._emit_progress()

    @Slot(str, str)
    def _on_job_finished(self, row_id: str, final_status: str):
        self._item_progress[row_id] = 100
        self._running.pop(row_id, None)
        self._emit_progress()
        self.job_finished.emit(row_id, final_status)

        if self._pending and not self._paused:
            self._maybe_dispatch()
        else:
            self._maybe_wrap_up()

    def _emit_progress(self):
        if self._total == 0:
            self.progress.emit(0)
            return
        total = sum(self._item_progress.values())
        overall = int(total / self._total)
        self.progress.emit(max(0, min(100, overall)))

    def _maybe_wrap_up(self):
        if self._running or self._pending:
            return
        self._wrap_up()

    def _wrap_up(self):
        self.progress.emit(100 if self._total else 0)
        self.status_key.emit("idle")
        self.log_event.emit({"key": "all_done", "args": {}})
        self._running_anything = False
        self._paused = False
        self.finished.emit()
