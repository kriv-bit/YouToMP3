from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.ui.worker import PlaylistExpandWorker, QueueMetadataWorker


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    """Block real HTTP fetches from helper functions across these tests."""
    monkeypatch.setattr("app.ui.worker._fetch_thumbnail_bytes", lambda *_a, **_kw: None)


class TestQueueMetadataWorker:
    def test_emits_resolved_for_each_job(self, qtbot) -> None:
        downloader = MagicMock()
        downloader.get_info.side_effect = [
            {"title": "First Song", "uploader": "Artist A", "thumbnail": "x.jpg"},
            {"title": "Second Song", "uploader": "Artist B", "thumbnail": "y.jpg"},
        ]
        worker = QueueMetadataWorker(downloader, [("row1", "url1"), ("row2", "url2")])

        resolved: list[tuple[str, str, dict]] = []
        worker.item_resolved.connect(lambda row, title, payload: resolved.append((row, title, payload)))

        with qtbot.waitSignal(worker.finished, timeout=2000):
            worker.run()

        assert [r[0] for r in resolved] == ["row1", "row2"]
        assert resolved[0][1] == "First Song"
        assert resolved[1][1] == "Second Song"
        assert resolved[0][2]["uploader"] == "Artist A"

    def test_emits_fallback_payload_when_get_info_fails(self, qtbot) -> None:
        downloader = MagicMock()
        downloader.get_info.side_effect = RuntimeError("network")
        worker = QueueMetadataWorker(downloader, [("rowX", "https://youtu.be/x")])

        resolved: list[tuple[str, str, dict]] = []
        worker.item_resolved.connect(lambda r, t, p: resolved.append((r, t, p)))

        with qtbot.waitSignal(worker.finished, timeout=2000):
            worker.run()

        assert len(resolved) == 1
        row, title, payload = resolved[0]
        assert row == "rowX"
        assert title == "https://youtu.be/x"
        assert payload["uploader"] == ""
        assert payload["thumbnail"] == ""


class TestPlaylistExpandWorker:
    def test_emits_item_for_each_entry(self, qtbot) -> None:
        downloader = MagicMock()
        downloader.get_info.return_value = {
            "entries": [
                {"id": "abc", "title": "Track 1", "uploader": "U"},
                {"id": "def", "title": "Track 2", "uploader": "U"},
            ]
        }
        worker = PlaylistExpandWorker(downloader, "https://list", fmt="mp3")

        found: list[tuple[str, str, str, dict]] = []
        worker.item_found.connect(lambda fmt, url, title, meta: found.append((fmt, url, title, meta)))

        with qtbot.waitSignal(worker.finished, timeout=2000) as blocker:
            worker.run()

        assert blocker.args == [2]
        assert len(found) == 2
        assert found[0][0] == "mp3"
        assert "abc" in found[0][1]
        assert found[0][2] == "Track 1"

    def test_uses_webpage_url_when_present(self, qtbot) -> None:
        downloader = MagicMock()
        downloader.get_info.return_value = {
            "entries": [
                {"webpage_url": "https://example.com/v1", "title": "T1"},
            ]
        }
        worker = PlaylistExpandWorker(downloader, "https://list", fmt="m4a")

        found = []
        worker.item_found.connect(lambda fmt, url, title, meta: found.append((fmt, url, title, meta)))
        with qtbot.waitSignal(worker.finished, timeout=2000):
            worker.run()

        assert found[0][1] == "https://example.com/v1"

    def test_deduplicates_entries(self, qtbot) -> None:
        downloader = MagicMock()
        downloader.get_info.return_value = {
            "entries": [
                {"id": "abc", "title": "Track 1"},
                {"id": "abc", "title": "Duplicate"},
                {"id": "xyz", "title": "Track 2"},
            ]
        }
        worker = PlaylistExpandWorker(downloader, "https://list", fmt="mp3")
        found = []
        worker.item_found.connect(lambda *a: found.append(a))

        with qtbot.waitSignal(worker.finished, timeout=2000) as blocker:
            worker.run()

        assert blocker.args == [2]
        assert len(found) == 2

    def test_respects_limit(self, qtbot) -> None:
        downloader = MagicMock()
        downloader.get_info.return_value = {
            "entries": [{"id": f"v{i}", "title": f"T{i}"} for i in range(10)]
        }
        worker = PlaylistExpandWorker(downloader, "https://list", fmt="mp3", limit=3)
        found = []
        worker.item_found.connect(lambda *a: found.append(a))

        with qtbot.waitSignal(worker.finished, timeout=2000) as blocker:
            worker.run()
        assert blocker.args == [3]
        assert len(found) == 3

    def test_emits_error_when_get_info_raises(self, qtbot) -> None:
        downloader = MagicMock()
        downloader.get_info.side_effect = RuntimeError("playlist exploded")
        worker = PlaylistExpandWorker(downloader, "https://list", fmt="mp3")

        errors = []
        worker.error.connect(lambda msg: errors.append(msg))
        with qtbot.waitSignal(worker.finished, timeout=2000) as blocker:
            worker.run()
        assert blocker.args == [-1]
        assert errors == ["playlist exploded"]

    def test_emits_zero_when_no_entries(self, qtbot) -> None:
        downloader = MagicMock()
        downloader.get_info.return_value = {"entries": []}
        worker = PlaylistExpandWorker(downloader, "https://list", fmt="mp3")
        with qtbot.waitSignal(worker.finished, timeout=2000) as blocker:
            worker.run()
        assert blocker.args == [0]
