from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.ui.worker import DownloadWorker, PlaylistExpandWorker, QueueMetadataWorker


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


class TestDownloadWorker:
    def _items(self, count: int = 1) -> list[tuple[str, str, str, dict]]:
        return [
            (
                f"row{i}",
                f"https://youtu.be/v{i}",
                "mp3",
                {"title": f"Song {i}", "uploader": "U", "thumbnail": "thumb"},
            )
            for i in range(count)
        ]

    def test_emits_completion_for_successful_run(self, qtbot) -> None:
        downloader = MagicMock()
        downloader.download.return_value = {"filepath": "/tmp/song.mp3", "title": "Song"}
        worker = DownloadWorker(downloader, self._items(2), fmt="mp3", quality="192")

        statuses: list[str] = []
        worker.status_key.connect(statuses.append)
        item_updates: list[tuple] = []
        worker.item_update.connect(lambda *a: item_updates.append(a))

        with qtbot.waitSignal(worker.finished, timeout=2000):
            worker.run()

        assert "downloading" in statuses
        assert statuses[-1] == "idle"
        done_rows = [u for u in item_updates if u[1] == "done"]
        assert len(done_rows) == 2

    def test_marks_item_as_error_when_download_raises(self, qtbot) -> None:
        downloader = MagicMock()
        downloader.download.side_effect = RuntimeError("boom")
        worker = DownloadWorker(downloader, self._items(1), fmt="mp3", quality="192")

        item_updates: list[tuple] = []
        worker.item_update.connect(lambda *a: item_updates.append(a))
        log_events: list[dict] = []
        worker.log_event.connect(log_events.append)

        with qtbot.waitSignal(worker.finished, timeout=2000):
            worker.run()

        statuses = {u[1] for u in item_updates}
        assert "error" in statuses
        assert any(e.get("key") == "error" for e in log_events)

    def test_fetches_metadata_when_missing(self, qtbot) -> None:
        downloader = MagicMock()
        downloader.get_info.return_value = {
            "title": "Resolved",
            "uploader": "X",
            "thumbnail": "t.jpg",
        }
        downloader.download.return_value = {"filepath": "/tmp/y.mp3", "title": "Resolved"}

        # item with empty meta → should trigger get_info
        items = [("rowZ", "https://youtu.be/z", "mp3", {})]
        worker = DownloadWorker(downloader, items, fmt="mp3", quality="192")
        with qtbot.waitSignal(worker.finished, timeout=2000):
            worker.run()

        downloader.get_info.assert_called_once_with("https://youtu.be/z")

    def test_propagates_artwork_warning_to_log(self, qtbot) -> None:
        downloader = MagicMock()
        downloader.download.return_value = {
            "filepath": "/tmp/s.mp3",
            "title": "S",
            "artwork_warning": "no thumb",
        }
        worker = DownloadWorker(downloader, self._items(1), fmt="mp3", quality="192")
        log_events: list[dict] = []
        worker.log_event.connect(log_events.append)
        with qtbot.waitSignal(worker.finished, timeout=2000):
            worker.run()
        assert any(e.get("key") == "artwork_warning" for e in log_events)


class TestDownloadWorkerProgressHook:
    def test_emits_progress_percentage(self, qtbot) -> None:
        downloader = MagicMock()
        worker = DownloadWorker(downloader, [], fmt="mp3", quality="192")
        worker._current_row_id = "rowA"
        worker._current_title = "Title"

        progress: list[int] = []
        worker.progress.connect(progress.append)

        worker.hook({"status": "downloading", "total_bytes": 100, "downloaded_bytes": 50})
        assert progress == [50]

        worker.hook({"status": "downloading", "total_bytes": 100, "downloaded_bytes": 150})
        assert progress[-1] == 100  # clamped

    def test_ignores_progress_without_total(self) -> None:
        downloader = MagicMock()
        worker = DownloadWorker(downloader, [], fmt="mp3", quality="192")
        emitted: list[int] = []
        worker.progress.connect(emitted.append)
        worker.hook({"status": "downloading", "downloaded_bytes": 50})
        assert emitted == []

    def test_post_processing_event_on_finished(self) -> None:
        downloader = MagicMock()
        worker = DownloadWorker(downloader, [], fmt="mp3", quality="192")
        events: list[dict] = []
        worker.log_event.connect(events.append)
        worker.hook({"status": "finished", "filename": "/tmp/out.mp3"})
        assert events and events[0]["key"] == "post_processing"
        assert worker._current_output == "/tmp/out.mp3"
