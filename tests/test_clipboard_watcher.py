from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.ui.clipboard_watcher import (
    ClipboardWatcher,
    extract_youtube_urls,
    is_youtube_url,
)


class TestIsYoutubeUrl:
    @pytest.mark.parametrize(
        "url",
        [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "http://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://music.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com/playlist?list=PLABC",
            "https://www.youtube.com/shorts/abc123",
        ],
    )
    def test_recognises_canonical_youtube_urls(self, url: str) -> None:
        assert is_youtube_url(url) is True

    @pytest.mark.parametrize(
        "candidate",
        [
            "",
            "   ",
            "not a url",
            "https://vimeo.com/12345",
            "https://example.com",
            "youtube.com/watch?v=abc",  # missing scheme
            "https://www.youtube.com/watch?v=abc some trailing text",
        ],
    )
    def test_rejects_non_matches(self, candidate: str) -> None:
        assert is_youtube_url(candidate) is False

    def test_handles_whitespace_padding(self) -> None:
        assert is_youtube_url("   https://youtu.be/abc   ") is True


class TestExtractYoutubeUrls:
    def test_extracts_from_arbitrary_text(self) -> None:
        text = "check this https://youtu.be/abc and also https://www.youtube.com/watch?v=xyz cool"
        assert extract_youtube_urls(text) == [
            "https://youtu.be/abc",
            "https://www.youtube.com/watch?v=xyz",
        ]

    def test_deduplicates_preserving_order(self) -> None:
        text = "https://youtu.be/a https://youtu.be/b https://youtu.be/a"
        assert extract_youtube_urls(text) == ["https://youtu.be/a", "https://youtu.be/b"]

    def test_strips_trailing_punctuation(self) -> None:
        text = "url is https://youtu.be/abc, ok?"
        assert extract_youtube_urls(text) == ["https://youtu.be/abc"]

    def test_returns_empty_for_no_matches(self) -> None:
        assert extract_youtube_urls("nothing here") == []
        assert extract_youtube_urls("") == []


class _FakeClipboard:
    """Stand-in for QClipboard that lets tests trigger dataChanged manually."""

    def __init__(self):
        self._text = ""
        self._callbacks: list = []

    def text(self) -> str:
        return self._text

    def setText(self, value: str) -> None:
        self._text = value
        for cb in self._callbacks:
            cb()

    @property
    def dataChanged(self):
        # Quack like a Signal: tests call .connect(cb).
        clip = self

        class _Signal:
            def connect(self, cb):
                clip._callbacks.append(cb)

        return _Signal()


class TestClipboardWatcher:
    def test_emits_on_first_youtube_url(self) -> None:
        clip = _FakeClipboard()
        watcher = ClipboardWatcher(clip)  # type: ignore[arg-type]
        sink = MagicMock()
        watcher.youtube_url_detected.connect(sink)

        clip.setText("https://youtu.be/abc")
        sink.assert_called_once_with("https://youtu.be/abc")

    def test_does_not_re_emit_same_url(self) -> None:
        clip = _FakeClipboard()
        watcher = ClipboardWatcher(clip)  # type: ignore[arg-type]
        sink = MagicMock()
        watcher.youtube_url_detected.connect(sink)

        clip.setText("https://youtu.be/abc")
        clip.setText("https://youtu.be/abc")
        assert sink.call_count == 1

    def test_emits_again_after_different_url(self) -> None:
        clip = _FakeClipboard()
        watcher = ClipboardWatcher(clip)  # type: ignore[arg-type]
        sink = MagicMock()
        watcher.youtube_url_detected.connect(sink)

        clip.setText("https://youtu.be/a")
        clip.setText("https://youtu.be/b")
        assert sink.call_count == 2

    def test_skips_non_youtube_text(self) -> None:
        clip = _FakeClipboard()
        watcher = ClipboardWatcher(clip)  # type: ignore[arg-type]
        sink = MagicMock()
        watcher.youtube_url_detected.connect(sink)

        clip.setText("hello world")
        clip.setText("https://vimeo.com/12345")
        sink.assert_not_called()

    def test_respects_in_queue_callback(self) -> None:
        clip = _FakeClipboard()
        in_queue = MagicMock(return_value=True)
        watcher = ClipboardWatcher(clip, is_in_queue=in_queue)  # type: ignore[arg-type]
        sink = MagicMock()
        watcher.youtube_url_detected.connect(sink)

        clip.setText("https://youtu.be/already-there")
        sink.assert_not_called()
        in_queue.assert_called_once_with("https://youtu.be/already-there")

    def test_set_enabled_silences_emissions(self) -> None:
        clip = _FakeClipboard()
        watcher = ClipboardWatcher(clip)  # type: ignore[arg-type]
        sink = MagicMock()
        watcher.youtube_url_detected.connect(sink)

        watcher.set_enabled(False)
        clip.setText("https://youtu.be/abc")
        sink.assert_not_called()

        watcher.set_enabled(True)
        clip.setText("https://youtu.be/xyz")
        sink.assert_called_once_with("https://youtu.be/xyz")

    def test_reset_allows_re_emission(self) -> None:
        clip = _FakeClipboard()
        watcher = ClipboardWatcher(clip)  # type: ignore[arg-type]
        sink = MagicMock()
        watcher.youtube_url_detected.connect(sink)

        clip.setText("https://youtu.be/abc")
        watcher.reset()
        clip.setText("https://youtu.be/abc")
        assert sink.call_count == 2
