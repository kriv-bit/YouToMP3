from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.downloader import DownloadCancelled
from app.ui.download_manager import DownloadJob, DownloadManager


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    monkeypatch.setattr("app.ui.worker._fetch_thumbnail_bytes", lambda *_a, **_kw: None)


# -------------------------------------------------------------------- DownloadJob


class TestDownloadJob:
    def _make_job(self, downloader, *, row_id: str = "row1", url: str = "https://youtu.be/x", fmt: str = "mp3"):
        return DownloadJob(
            downloader,
            row_id=row_id,
            url=url,
            fmt=fmt,
            quality="192",
            meta={"title": "Song", "uploader": "U", "thumbnail": "t"},
        )

    def test_emits_done_on_success(self, qtbot) -> None:
        downloader = MagicMock()
        downloader.download.return_value = {"filepath": "/tmp/s.mp3", "title": "Song"}
        job = self._make_job(downloader)

        statuses: list[tuple] = []
        job.item_update.connect(lambda *a: statuses.append(a))

        with qtbot.waitSignal(job.finished, timeout=2000) as blocker:
            job.run()

        assert blocker.args == ["row1", "done"]
        assert ("row1", "done", 100, "Song", "/tmp/s.mp3") in statuses

    def test_emits_error_when_download_raises(self, qtbot) -> None:
        downloader = MagicMock()
        downloader.download.side_effect = RuntimeError("boom")
        job = self._make_job(downloader)

        with qtbot.waitSignal(job.finished, timeout=2000) as blocker:
            job.run()
        assert blocker.args == ["row1", "error"]

    def test_cancel_before_run_emits_cancelled_without_calling_download(self, qtbot) -> None:
        downloader = MagicMock()
        job = self._make_job(downloader)
        job.cancel()

        with qtbot.waitSignal(job.finished, timeout=2000) as blocker:
            job.run()
        assert blocker.args == ["row1", "cancelled"]
        downloader.download.assert_not_called()

    def test_progress_hook_raises_when_cancelled_midflight(self) -> None:
        downloader = MagicMock()
        job = self._make_job(downloader)
        job.cancel()
        with pytest.raises(DownloadCancelled):
            job.hook({"status": "downloading", "total_bytes": 100, "downloaded_bytes": 50})

    def test_emits_cancelled_when_yt_dlp_wraps_cancellation(self, qtbot) -> None:
        downloader = MagicMock()

        def fake_download(*_a, **_kw):
            # Simulate yt-dlp wrapping DownloadCancelled in a generic exception.
            raise RuntimeError("Interrupted: HTTP Error 200")

        downloader.download.side_effect = fake_download
        job = self._make_job(downloader)
        # Flip the cancel flag before the exception bubbles out.
        job.cancel()
        with qtbot.waitSignal(job.finished, timeout=2000) as blocker:
            job.run()
        assert blocker.args == ["row1", "cancelled"]

    def test_fetches_metadata_when_missing(self, qtbot) -> None:
        downloader = MagicMock()
        downloader.get_info.return_value = {
            "title": "Resolved",
            "uploader": "X",
            "thumbnail": "thumb",
        }
        downloader.download.return_value = {"filepath": "/tmp/x.mp3", "title": "Resolved"}

        job = DownloadJob(
            downloader,
            row_id="rowZ",
            url="https://youtu.be/z",
            fmt="mp3",
            quality="192",
            meta={},
        )
        with qtbot.waitSignal(job.finished, timeout=2000):
            job.run()

        downloader.get_info.assert_called_once_with("https://youtu.be/z")

    def test_propagates_artwork_warning(self, qtbot) -> None:
        downloader = MagicMock()
        downloader.download.return_value = {
            "filepath": "/tmp/a.mp3",
            "title": "A",
            "artwork_warning": "no cover",
        }
        job = self._make_job(downloader)
        log_events: list[dict] = []
        job.log_event.connect(log_events.append)
        with qtbot.waitSignal(job.finished, timeout=2000):
            job.run()
        assert any(e.get("key") == "artwork_warning" for e in log_events)

    def test_passes_sponsorblock_flag_to_downloader(self, qtbot) -> None:
        downloader = MagicMock()
        downloader.download.return_value = {"filepath": "/tmp/x.mp3", "title": "X"}
        job = DownloadJob(
            downloader,
            row_id="r",
            url="https://youtu.be/x",
            fmt="mp3",
            quality="192",
            meta={"title": "X", "uploader": "U", "thumbnail": "t"},
            sponsorblock=True,
        )
        with qtbot.waitSignal(job.finished, timeout=2000):
            job.run()
        downloader.download.assert_called_once()
        _, kwargs = downloader.download.call_args
        assert kwargs["sponsorblock"] is True
        assert kwargs["trim"] is None

    def test_extracts_trim_from_meta(self, qtbot) -> None:
        downloader = MagicMock()
        downloader.download.return_value = {"filepath": "/tmp/x.mp3", "title": "X"}
        job = DownloadJob(
            downloader,
            row_id="r",
            url="https://youtu.be/x",
            fmt="mp3",
            quality="192",
            meta={
                "title": "X",
                "uploader": "U",
                "thumbnail": "t",
                "trim_start": 30,
                "trim_end": 90,
            },
        )
        with qtbot.waitSignal(job.finished, timeout=2000):
            job.run()
        _, kwargs = downloader.download.call_args
        assert kwargs["trim"] == (30, 90)


class TestDownloadJobProgressHook:
    def _job(self) -> DownloadJob:
        return DownloadJob(
            MagicMock(),
            row_id="r",
            url="https://youtu.be/x",
            fmt="mp3",
            quality="192",
            meta={"title": "T"},
        )

    def test_emits_clamped_percentage(self) -> None:
        job = self._job()
        emitted: list[int] = []
        job.progress.connect(emitted.append)

        job.hook({"status": "downloading", "total_bytes": 100, "downloaded_bytes": 50})
        assert emitted == [50]
        job.hook({"status": "downloading", "total_bytes": 100, "downloaded_bytes": 150})
        assert emitted[-1] == 100

    def test_ignores_without_total(self) -> None:
        job = self._job()
        emitted: list[int] = []
        job.progress.connect(emitted.append)
        job.hook({"status": "downloading", "downloaded_bytes": 50})
        assert emitted == []

    def test_records_output_on_finished(self) -> None:
        job = self._job()
        events: list[dict] = []
        job.log_event.connect(events.append)
        job.hook({"status": "finished", "filename": "/tmp/out.mp3"})
        assert events and events[0]["key"] == "post_processing"
        assert job._current_output == "/tmp/out.mp3"


# ----------------------------------------------------------------- DownloadManager


@pytest.fixture
def fast_downloader():
    """A downloader mock whose download() returns instantly."""
    d = MagicMock()
    d.download.return_value = {"filepath": "/tmp/x.mp3", "title": "Song"}
    return d


def _wait_for_finish(qtbot, manager: DownloadManager, timeout_ms: int = 3000):
    with qtbot.waitSignal(manager.finished, timeout=timeout_ms):
        pass


class TestDownloadManagerLifecycle:
    def test_empty_start_finishes_immediately(self, qtbot, fast_downloader) -> None:
        m = DownloadManager(fast_downloader)
        with qtbot.waitSignal(m.finished, timeout=2000):
            m.start([], "mp3", "192")
        assert not m.is_running

    def test_single_item_completes(self, qtbot, fast_downloader) -> None:
        m = DownloadManager(fast_downloader)
        item = ("r1", "https://youtu.be/a", "mp3", {"title": "T", "uploader": "U", "thumbnail": "th"})
        results: list[tuple[str, str]] = []
        m.job_finished.connect(lambda rid, status: results.append((rid, status)))

        with qtbot.waitSignal(m.finished, timeout=3000):
            m.start([item], "mp3", "192")

        assert results == [("r1", "done")]
        assert not m.is_running
        fast_downloader.download.assert_called_once()

    def test_multiple_items_all_complete(self, qtbot, fast_downloader) -> None:
        m = DownloadManager(fast_downloader)
        items = [
            (f"r{i}", f"https://youtu.be/v{i}", "mp3", {"title": f"T{i}", "uploader": "U", "thumbnail": "th"})
            for i in range(4)
        ]
        results: list[str] = []
        m.job_finished.connect(lambda rid, status: results.append(rid))
        with qtbot.waitSignal(m.finished, timeout=4000):
            m.start(items, "mp3", "192")
        assert sorted(results) == ["r0", "r1", "r2", "r3"]


class TestDownloadManagerConcurrency:
    def test_set_concurrency_is_clamped(self, fast_downloader) -> None:
        m = DownloadManager(fast_downloader)
        m.set_concurrency(0)
        assert m.concurrency == 1
        m.set_concurrency(10)
        assert m.concurrency == 4
        m.set_concurrency(3)
        assert m.concurrency == 3

    def test_set_concurrency_handles_garbage(self, fast_downloader) -> None:
        m = DownloadManager(fast_downloader)
        m.set_concurrency("not-a-number")  # type: ignore[arg-type]
        assert m.concurrency == 1


class TestDownloadManagerCancel:
    def test_cancels_pending_item_before_it_runs(self, qtbot, fast_downloader) -> None:
        m = DownloadManager(fast_downloader)
        m.set_concurrency(1)
        items = [
            ("r1", "https://a", "mp3", {"title": "T1", "uploader": "U", "thumbnail": "th"}),
            ("r2", "https://b", "mp3", {"title": "T2", "uploader": "U", "thumbnail": "th"}),
        ]

        statuses: dict[str, str] = {}

        def on_item(row_id, status, *_):
            statuses[row_id] = status

        m.item_update.connect(on_item)

        # Cancel r2 before starting so it should be processed in the pending list.
        # We start, then immediately cancel before the thread schedules r2.
        # To keep this deterministic, set concurrency=1: r1 runs first, r2 still pending.
        m.start(items, "mp3", "192")
        m.cancel_item("r2")
        with qtbot.waitSignal(m.finished, timeout=4000):
            pass

        assert statuses.get("r2") == "cancelled"

    def test_cancel_all_marks_pending_as_cancelled(self, qtbot, fast_downloader) -> None:
        m = DownloadManager(fast_downloader)
        m.set_concurrency(1)
        items = [
            ("r1", "https://a", "mp3", {"title": "T1", "uploader": "U", "thumbnail": "th"}),
            ("r2", "https://b", "mp3", {"title": "T2", "uploader": "U", "thumbnail": "th"}),
            ("r3", "https://c", "mp3", {"title": "T3", "uploader": "U", "thumbnail": "th"}),
        ]
        statuses: dict[str, str] = {}
        m.item_update.connect(lambda rid, status, *_: statuses.update({rid: status}))

        m.start(items, "mp3", "192")
        m.cancel_all()
        with qtbot.waitSignal(m.finished, timeout=4000):
            pass
        # Pending items should be cancelled; r1 may already have started so it could be done or cancelled.
        assert statuses["r2"] == "cancelled"
        assert statuses["r3"] == "cancelled"
        assert statuses["r1"] in ("done", "cancelled")


class TestDownloadManagerPause:
    def test_pause_emits_paused_status(self, qtbot, fast_downloader) -> None:
        m = DownloadManager(fast_downloader)
        statuses: list[str] = []
        m.status_key.connect(statuses.append)
        m.start([], "mp3", "192")  # immediate finish
        m._running_anything = True  # force as if running
        m.pause()
        assert "paused" in statuses

    def test_pause_when_not_running_is_noop(self, fast_downloader) -> None:
        m = DownloadManager(fast_downloader)
        statuses: list[str] = []
        m.status_key.connect(statuses.append)
        m.pause()
        assert statuses == []

    def test_resume_when_not_paused_is_noop(self, fast_downloader) -> None:
        m = DownloadManager(fast_downloader)
        m._running_anything = True
        statuses: list[str] = []
        m.status_key.connect(statuses.append)
        m.resume()
        assert statuses == []


class TestDownloadManagerProgress:
    def test_progress_emits_zero_with_no_items(self, qtbot, fast_downloader) -> None:
        m = DownloadManager(fast_downloader)
        progress: list[int] = []
        m.progress.connect(progress.append)
        with qtbot.waitSignal(m.finished, timeout=2000):
            m.start([], "mp3", "192")
        # progress(0) on start, then 0 on wrap_up (since total=0)
        assert progress[0] == 0

    def test_progress_reaches_100_after_completion(self, qtbot, fast_downloader) -> None:
        m = DownloadManager(fast_downloader)
        progress: list[int] = []
        m.progress.connect(progress.append)
        item = ("r1", "https://a", "mp3", {"title": "T", "uploader": "U", "thumbnail": "th"})
        with qtbot.waitSignal(m.finished, timeout=3000):
            m.start([item], "mp3", "192")
        assert progress[-1] == 100
