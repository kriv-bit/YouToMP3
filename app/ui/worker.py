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
        with urlopen(req, timeout=4) as resp:
            return resp.read(4 * 1024 * 1024)
    except Exception:
        return None


def _display_title(info: dict, fallback: str) -> str:
    if not isinstance(info, dict):
        return fallback
    title = str(info.get("title") or "").strip()
    return title or fallback


def _metadata_payload(info: dict, fallback: str, thumbnail_data: bytes | None = None) -> dict:
    thumbnail = _best_thumbnail_url(info)
    return {
        "title": _display_title(info, fallback),
        "uploader": info.get("uploader") or info.get("channel") or "",
        "duration": info.get("duration"),
        "thumbnail": thumbnail,
        "thumbnail_data": thumbnail_data,
    }


def _needs_metadata(meta: dict) -> bool:
    return not meta.get("title") or not meta.get("thumbnail") or not meta.get("uploader")


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
                thumb_url = _best_thumbnail_url(info)
                thumb_bytes = _fetch_thumbnail_bytes(thumb_url)
                title = _display_title(info, url)
                payload = _metadata_payload(info, url, thumb_bytes)
            except Exception:
                payload = {
                    "title": title,
                    "uploader": "",
                    "duration": None,
                    "thumbnail": "",
                    "thumbnail_data": thumb_bytes,
                }

            self.item_resolved.emit(row_id, title, payload)

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
            thumb_url = _best_thumbnail_url(entry)
            thumb_bytes = _fetch_thumbnail_bytes(thumb_url)
            payload = _metadata_payload(entry, webpage, thumb_bytes)
            self.item_found.emit(self.fmt, webpage, title, payload)
            count += 1

        self.finished.emit(count)
