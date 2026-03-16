from __future__ import annotations

from urllib.request import Request, urlopen

from PySide6.QtCore import QObject, Signal, Slot


def _best_thumbnail_url(info: dict) -> str:
    if not isinstance(info, dict):
        return ""

    thumbnail = info.get("thumbnail")
    if thumbnail:
        return str(thumbnail)

    thumbs = info.get("thumbnails")
    if isinstance(thumbs, list):
        for thumb in reversed(thumbs):
            if isinstance(thumb, dict) and thumb.get("url"):
                return str(thumb["url"])
    return ""


def _fetch_thumbnail_bytes(url: str) -> bytes | None:
    if not url:
        return None

    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=12) as resp:
            return resp.read()
    except Exception:
        return None


def _display_title(info: dict, fallback: str) -> str:
    if not isinstance(info, dict):
        return fallback
    title = str(info.get("title") or "").strip()
    return title or fallback


class QueueMetadataWorker(QObject):
    item_resolved = Signal(str, str, object)
    finished = Signal()

    def __init__(self, downloader, jobs):
        super().__init__()
        self.downloader = downloader
        self.jobs = list(jobs)

    @Slot()
    def run(self):
        for row_id, url in self.jobs:
            title = url
            thumb_bytes = None
            try:
                info = self.downloader.get_info(url)
                title = _display_title(info, url)
                thumb_bytes = _fetch_thumbnail_bytes(_best_thumbnail_url(info))
            except Exception:
                pass

            self.item_resolved.emit(row_id, title, thumb_bytes)

        self.finished.emit()


class PlaylistExpandWorker(QObject):
    item_found = Signal(str, str, str, object)
    error = Signal(str)
    finished = Signal(int)

    def __init__(self, downloader, playlist_url: str, fmt: str, limit: int = 200):
        super().__init__()
        self.downloader = downloader
        self.playlist_url = playlist_url
        self.fmt = fmt
        self.limit = max(1, int(limit))

    @Slot()
    def run(self):
        try:
            info = self.downloader.get_info(self.playlist_url, allow_playlist=True)
        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit(-1)
            return

        entries = info.get("entries") if isinstance(info, dict) else None
        if not entries:
            self.finished.emit(0)
            return

        seen: set[str] = set()
        count = 0
        for entry in entries:
            if count >= self.limit:
                break
            if not isinstance(entry, dict):
                continue

            webpage = entry.get("webpage_url")
            if not webpage:
                eid = entry.get("id")
                if eid:
                    webpage = f"https://www.youtube.com/watch?v={eid}"

            if not webpage or webpage in seen:
                continue

            seen.add(webpage)
            title = _display_title(entry, webpage)
            thumb_bytes = _fetch_thumbnail_bytes(_best_thumbnail_url(entry))
            self.item_found.emit(self.fmt, webpage, title, thumb_bytes)
            count += 1

        self.finished.emit(count)


class DownloadWorker(QObject):
    log_event = Signal(object)
    progress = Signal(int)
    status_key = Signal(str)
    finished = Signal()
    item_update = Signal(str, str, int, str, str)

    def __init__(self, downloader, items, fmt, quality):
        super().__init__()
        self.downloader = downloader
        self.items = list(items)
        self.fmt = fmt
        self.quality = quality

        self._current_row_id = ""
        self._current_title = ""
        self._current_output = ""

    def hook(self, data):
        status = data.get("status")

        if status == "downloading":
            total = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
            downloaded = data.get("downloaded_bytes") or 0
            if total:
                pct = int((downloaded / total) * 100)
                pct = max(0, min(100, pct))
                self.progress.emit(pct)

                if self._current_row_id:
                    self.item_update.emit(
                        self._current_row_id,
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
        self.status_key.emit("downloading")
        self.progress.emit(0)

        total_items = len(self.items)
        self.log_event.emit({"key": "starting_batch", "args": {"count": total_items}})

        for index, (row_id, url) in enumerate(self.items, start=1):
            self._current_row_id = row_id
            self._current_title = ""
            self._current_output = ""
            self.item_update.emit(row_id, "downloading", 0, "", "")

            self.log_event.emit(
                {"key": "item_downloading", "args": {"i": index, "total": total_items, "url": url}}
            )

            try:
                info = self.downloader.get_info(url)
                title = _display_title(info, url)
                uploader = info.get("uploader") or info.get("channel") or ""
                duration = info.get("duration")
                thumbnail = _best_thumbnail_url(info)
                nice = f"{title}" + (f" - {uploader}" if uploader else "")

                self._current_title = title
                self.log_event.emit({"key": "now_downloading", "args": {"title": nice}})
                self.log_event.emit({
                    "key": "current_item_meta",
                    "args": {
                        "title": title,
                        "uploader": uploader,
                        "duration": duration,
                        "thumbnail": thumbnail,
                        "url": url,
                        "index": index,
                        "total": total_items,
                    },
                })

                self.item_update.emit(row_id, "downloading", 0, title, "")

                result = self.downloader.download(
                    url,
                    format_type=self.fmt,
                    quality=self.quality,
                    progress_callback=self.hook,
                )

                out_file = ""
                if isinstance(result, dict):
                    out_file = result.get("filepath") or ""

                if out_file:
                    self._current_output = out_file

                self.item_update.emit(row_id, "done", 100, title, self._current_output)
                self.log_event.emit({"key": "done", "args": {}})

            except Exception as e:
                self.item_update.emit(row_id, "error", 0, self._current_title or url, "")
                self.log_event.emit({"key": "error", "args": {"error": str(e)}})

        self.progress.emit(100)
        self.status_key.emit("idle")
        self.log_event.emit({"key": "all_done", "args": {}})
        self.finished.emit()
