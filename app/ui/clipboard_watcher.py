"""Clipboard watcher that detects YouTube URLs and emits a one-shot signal.

The watcher debounces against the previously suggested URL (so the same string
re-copied doesn't keep firing) and against an external "is in queue" callback
so we don't pester the user about URLs already enqueued.
"""

from __future__ import annotations

import re
from collections.abc import Callable

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtGui import QClipboard

# Matches youtube.com, m.youtube.com, music.youtube.com, youtu.be (with or without scheme).
_YT_URL_RE = re.compile(
    r"https?://(?:www\.|m\.|music\.)?(?:youtube\.com|youtu\.be)/\S+",
    re.IGNORECASE,
)


def is_youtube_url(candidate: str) -> bool:
    """Return True when ``candidate`` is a single YouTube URL (no trailing junk)."""
    if not candidate:
        return False
    text = candidate.strip()
    if " " in text or "\n" in text:
        return False
    match = _YT_URL_RE.fullmatch(text)
    return match is not None


def extract_youtube_urls(text: str) -> list[str]:
    """Pull every YouTube URL out of an arbitrary blob of text, preserving order."""
    if not text:
        return []
    seen: set[str] = set()
    out: list[str] = []
    for match in _YT_URL_RE.finditer(text):
        url = match.group(0).rstrip(".,;)]}>'\"")
        if url not in seen:
            seen.add(url)
            out.append(url)
    return out


class ClipboardWatcher(QObject):
    """Emits :pyattr:`youtube_url_detected` when a fresh YT URL hits the clipboard."""

    youtube_url_detected = Signal(str)

    def __init__(
        self,
        clipboard: QClipboard,
        *,
        is_in_queue: Callable[[str], bool] | None = None,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self._clipboard = clipboard
        self._is_in_queue = is_in_queue
        self._last_seen: str | None = None
        self._enabled = True
        self._clipboard.dataChanged.connect(self._on_clipboard_changed)

    def set_enabled(self, enabled: bool):
        self._enabled = bool(enabled)

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    def reset(self):
        """Forget the last seen URL — useful for tests or after a clear."""
        self._last_seen = None

    @Slot()
    def _on_clipboard_changed(self):
        if not self._enabled:
            return
        try:
            text = self._clipboard.text() or ""
        except RuntimeError:
            return
        self._handle_text(text)

    def _handle_text(self, text: str):
        candidate = text.strip()
        if not is_youtube_url(candidate):
            return
        if candidate == self._last_seen:
            return
        if self._is_in_queue and self._is_in_queue(candidate):
            return
        self._last_seen = candidate
        self.youtube_url_detected.emit(candidate)
