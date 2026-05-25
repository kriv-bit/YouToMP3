# app/ui/controller.py
"""Controller: action handlers, download orchestration, playlist expansion."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QThread, QUrl, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QDialog, QFileDialog, QMessageBox

from app.ui.dialogs import AddPlaylistDialog, AddSongDialog, PasteBatchDialog
from app.ui.download_manager import DownloadManager
from app.ui.widgets import set_elided
from app.ui.worker import PlaylistExpandWorker, QueueMetadataWorker

if TYPE_CHECKING:
    from app.ui.window import MainWindow


class MainController(QObject):
    """Mediates between MainWindow widgets and business logic.

    Holds a reference to the window to read/write widget state.
    """

    def __init__(self, win: MainWindow):
        super().__init__(win)
        self.win = win
        if not hasattr(self.win, "background_jobs"):
            self.win.background_jobs = []

        self.download_manager = DownloadManager(self.win.downloader, parent=self)
        self.win.download_manager = self.download_manager
        self.download_manager.set_concurrency(self.win.settings.get_concurrency())
        self.win.queue.set_cancel_fn(self.cancel_item)

        self.download_manager.progress.connect(self._on_manager_progress)
        self.download_manager.status_key.connect(self.set_status)
        self.download_manager.log_event.connect(self.on_log_event)
        self.download_manager.item_update.connect(self.on_item_update)
        self.download_manager.finished.connect(self.on_worker_finished)
        self.download_manager.job_started.connect(self.on_job_started)
        self.download_manager.job_finished.connect(self.on_job_finished)

    # ---- helpers ----

    def _t(self, key: str) -> str:
        return self.win._t(key)

    def _tf(self, key: str, **kwargs) -> str:
        return self.win._tf(key, **kwargs)

    def _settings_set(self, key: str, value):
        self.win._settings_set(key, value)

    def _register_background_job(self, thread: QThread, worker: object):
        job = (thread, worker)
        self.win.background_jobs.append(job)
        return job

    def _release_background_job(self, job):
        if job in self.win.background_jobs:
            self.win.background_jobs.remove(job)

    def _set_download_active(self, active: bool):
        self.win.download_active = active
        self.win.download_btn.setEnabled(not active)
        self.win.download_btn.setText(self._t("downloading") if active else self._t("download"))
        if hasattr(self.win, "pause_btn"):
            self.win.pause_btn.setEnabled(active)
            self.win.pause_btn.setText(self._t("pause"))

    def _start_metadata_lookup(self, jobs: list[tuple[str, str]]):
        if not jobs:
            return

        thread = QThread(self.win)
        worker = QueueMetadataWorker(self.win.downloader, jobs)
        worker.moveToThread(thread)

        job = self._register_background_job(thread, worker)
        thread.started.connect(worker.run)
        worker.item_resolved.connect(self.on_queue_item_resolved)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda: self._release_background_job(job))
        thread.start()

    def _start_playlist_expansion(self, playlist_url: str, fmt: str, limit: int):
        self.win.add_log(self._t("expanding_playlist"))

        thread = QThread(self.win)
        worker = PlaylistExpandWorker(self.win.downloader, playlist_url, fmt, limit=limit)
        worker.moveToThread(thread)

        job = self._register_background_job(thread, worker)
        thread.started.connect(worker.run)
        worker.item_found.connect(self.on_playlist_item_found)
        worker.error.connect(self.on_playlist_expand_error)
        worker.finished.connect(self.on_playlist_expand_finished)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda: self._release_background_job(job))
        thread.start()

    # ---- folder actions ----

    def select_folder(self):
        """Open native folder picker and update output path."""
        folder = QFileDialog.getExistingDirectory(self.win, self._t("select_folder"))
        if folder:
            self.win.output_folder = folder
            self.win.downloader.output_path = folder
            self.win.settings.set_output_folder(folder)
            set_elided(self.win.folder_chip, folder)
            self.win.add_log(self._tf("output_set", folder=folder))

    def open_output_folder(self):
        """Open the output folder in the system file explorer."""
        folder = self.win.output_folder
        if folder and os.path.isdir(folder):
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder))
        else:
            QMessageBox.warning(self.win, self._t("error_title"), self._t("folder_not_found"))

    # ---- status ----

    @Slot(str)
    def set_status(self, key: str):
        """Update the sidebar status label."""
        self.win.status_key = key
        if key == "downloading":
            self.win.status_value.setText(self._t("downloading"))
            self.win.status_value.setProperty("state", "downloading")
        elif key == "paused":
            self.win.status_value.setText(self._t("status_paused"))
            self.win.status_value.setProperty("state", "paused")
        else:
            self.win.status_value.setText(self._t("idle"))
            self.win.status_value.setProperty("state", "idle")
        self.win.status_value.style().unpolish(self.win.status_value)
        self.win.status_value.style().polish(self.win.status_value)
        self.win.status_value.update()

    # ---- dialog actions ----

    def open_add_song_dialog(self):
        """Show the Add Song modal and enqueue the entered URL."""
        dlg = AddSongDialog(self.win, t=self._tf)
        dlg.setStyleSheet(self.win.styleSheet())
        if dlg.exec() != QDialog.Accepted:
            return

        url = dlg.url()
        if not url:
            return

        fmt = self.win.format_box.currentText()
        row_id = self.win.queue.add_row(
            url=url,
            fmt=fmt,
            title=self._t("resolving_title"),
            status_key="queued",
            pct=0,
            settings_set_fn=self._settings_set,
        )
        self._start_metadata_lookup([(row_id, url)])

    def open_add_playlist_dialog(self):
        """Show the Add Playlist modal; optionally expand to individual videos."""
        dlg = AddPlaylistDialog(self.win, t=self._tf)
        dlg.setStyleSheet(self.win.styleSheet())
        if dlg.exec() != QDialog.Accepted:
            return

        data = dlg.data()
        url = data.get("url", "").strip()
        if not url:
            return

        fmt = self.win.format_box.currentText()

        if not data.get("expand", True):
            row_id = self.win.queue.add_row(
                url=url,
                fmt=fmt,
                title=self._t("resolving_title"),
                status_key="queued",
                pct=0,
                settings_set_fn=self._settings_set,
            )
            self._start_metadata_lookup([(row_id, url)])
            return

        self._start_playlist_expansion(url, fmt, data.get("limit", 200))

    def open_paste_batch_dialog(self):
        """Show the Paste Batch modal and enqueue all entered URLs."""
        dlg = PasteBatchDialog(self.win, t=self._tf)
        dlg.setStyleSheet(self.win.styleSheet())
        if dlg.exec() != QDialog.Accepted:
            return

        urls = dlg.urls()
        if not urls:
            return

        fmt = self.win.format_box.currentText()
        jobs: list[tuple[str, str]] = []
        for u in urls:
            row_id = self.win.queue.add_row(
                url=u,
                fmt=fmt,
                title=self._t("resolving_title"),
                status_key="queued",
                pct=0,
                auto_save=False,
            )
            jobs.append((row_id, u))
        self.win.queue.save(self._settings_set)
        self._start_metadata_lookup(jobs)

    # ---- playlist expansion ----

    def expand_playlist_to_urls(self, playlist_url: str, limit: int = 200) -> list[str]:
        """Expand a playlist URL into a deduplicated list of watch URLs."""
        info = self.win.downloader.get_info(playlist_url, allow_playlist=True)

        entries = info.get("entries") if isinstance(info, dict) else None
        if not entries:
            return []

        out: list[str] = []
        for entry in entries:
            if not entry:
                continue
            webpage = entry.get("webpage_url") if isinstance(entry, dict) else None
            if webpage:
                out.append(webpage)
                continue
            eid = entry.get("id") if isinstance(entry, dict) else None
            if eid:
                out.append(f"https://www.youtube.com/watch?v={eid}")

            if len(out) >= int(limit):
                break

        # Deduplicate preserving order
        seen: set[str] = set()
        deduped: list[str] = []
        for u in out:
            if u not in seen:
                seen.add(u)
                deduped.append(u)
        return deduped

    # ---- download orchestration ----

    def start_download(self):
        """Start the download manager on all currently queued rows."""
        if self.win.download_active:
            return

        queued = self.win.queue.get_queued_rows(
            fallback_fmt=self.win.format_box.currentText(),
        )
        if not queued:
            QMessageBox.warning(self.win, self._t("no_urls_title"), self._t("no_queued_body"))
            return

        fmt = self.win.format_box.currentText()
        q = self.win.quality_box.currentText()

        self._set_download_active(True)
        self.win.progress_bar.setValue(0)
        self.win.queue.set_active_row(None)
        self.download_manager.start(queued, fmt, q)

    def toggle_pause(self):
        """Pause or resume the download queue based on current state."""
        if not self.download_manager.is_running:
            return
        if self.download_manager.is_paused:
            self.download_manager.resume()
            if hasattr(self.win, "pause_btn"):
                self.win.pause_btn.setText(self._t("pause"))
        else:
            self.download_manager.pause()
            if hasattr(self.win, "pause_btn"):
                self.win.pause_btn.setText(self._t("resume"))

    def cancel_item(self, row_id: str):
        """Cancel a single queued or running item from the queue UI."""
        if not row_id:
            return
        self.download_manager.cancel_item(row_id)

    def set_concurrency(self, n: int):
        """Persist concurrency setting and apply it to the live manager."""
        self.win.settings.set_concurrency(n)
        self.download_manager.set_concurrency(n)

    @Slot(object)
    def on_log_event(self, event: object):
        """Route a Worker log_event signal to the console, now_label, and card."""
        key = event.get("key", "ready")
        args = event.get("args", {})

        # Intercept metadata for the Now Downloading card
        if key == "current_item_meta":
            self.win.now_card.update_meta(
                title=args.get("title", ""),
                uploader=args.get("uploader", ""),
                duration=args.get("duration"),
                thumbnail=args.get("thumbnail", ""),
                url=args.get("url", ""),
                index=args.get("index", 0),
                total=args.get("total", 0),
            )
            return  # Don't log raw metadata to console

        self.win.add_log(self._tf(key, **args))
        if key == "now_downloading":
            self.win.set_now_label(self._tf(key, **args))

    @Slot(str, str, object)
    def on_queue_item_resolved(self, row_id: str, title: str, metadata: object):
        """Apply metadata results coming from a background queue lookup."""
        payload = metadata if isinstance(metadata, dict) else {}
        thumbnail_data = payload.get("thumbnail_data")
        self.win.queue.update_metadata(
            row_id,
            title=payload.get("title") or title,
            thumbnail_data=thumbnail_data if isinstance(thumbnail_data, (bytes, bytearray)) else None,
            thumbnail_url=payload.get("thumbnail") or "",
            uploader=payload.get("uploader") or "",
            duration=payload.get("duration"),
        )

    @Slot(str, str, str, object)
    def on_playlist_item_found(self, fmt: str, url: str, title: str, metadata: object):
        """Add playlist entries progressively from the expansion worker."""
        payload = metadata if isinstance(metadata, dict) else {}
        thumbnail_data = payload.get("thumbnail_data")
        row_id = self.win.queue.add_row(
            url=url,
            fmt=fmt,
            title=payload.get("title") or title or self._t("resolving_title"),
            status_key="queued",
            pct=0,
            auto_save=False,
            thumbnail_data=thumbnail_data if isinstance(thumbnail_data, (bytes, bytearray)) else None,
            thumbnail_url=payload.get("thumbnail") or "",
            uploader=payload.get("uploader") or "",
            duration=payload.get("duration"),
        )
        if not title or not thumbnail_data:
            self._start_metadata_lookup([(row_id, url)])

    @Slot(str)
    def on_playlist_expand_error(self, message: str):
        QMessageBox.warning(self.win, self._t("error_title"), message)

    @Slot(int)
    def on_playlist_expand_finished(self, count: int):
        if count < 0:
            return
        if count == 0:
            QMessageBox.warning(self.win, self._t("error_title"), self._t("playlist_no_items"))
            return
        self.win.queue.save(self._settings_set)
        self.win.add_log(self._tf("playlist_items_added", count=count))

    @Slot(int)
    def _on_manager_progress(self, value: int):
        """Forward overall progress from the manager to the progress bar."""
        self.win.progress_bar.setValue(value)

    @Slot(str)
    def on_job_started(self, row_id: str):
        """Mark the most-recently started row as active so it cannot be deleted."""
        self.win.queue.set_active_row(row_id)

    @Slot(str, str)
    def on_job_finished(self, row_id: str, final_status: str):
        """Clear the active row marker when no jobs remain in flight."""
        if self.download_manager.active_count == 0:
            self.win.queue.set_active_row(None)

    @Slot(str, str, int, str, str)
    def on_item_update(self, row_id: str, status_key: str, pct: int, title: str, out_file: str):
        """Route a Worker item_update signal to the queue manager."""
        if status_key == "downloading":
            self.win.queue.set_active_row(row_id)
        self.win.queue.update_item(
            row_id, status_key, pct, title, out_file,
            settings_set_fn=self._settings_set,
        )

    @Slot()
    def on_worker_finished(self):
        """Re-enable UI after the download manager wraps up."""
        self._set_download_active(False)
        self.set_status("idle")
        self.win.queue.set_active_row(None)
        self.win.now_card.clear()
