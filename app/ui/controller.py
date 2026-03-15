# app/ui/controller.py
"""Controller: action handlers, download orchestration, playlist expansion."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QDialog, QFileDialog, QMessageBox
from PySide6.QtCore import QThread, QUrl
from PySide6.QtGui import QDesktopServices

from app.ui.dialogs import AddSongDialog, AddPlaylistDialog, PasteBatchDialog
from app.ui.worker import DownloadWorker
from app.ui.widgets import set_elided

if TYPE_CHECKING:
    from app.ui.window import MainWindow


class MainController:
    """Mediates between MainWindow widgets and business logic.

    Holds a reference to the window to read/write widget state.
    """

    def __init__(self, win: MainWindow):
        self.win = win

    # ---- helpers ----

    def _t(self, key: str) -> str:
        return self.win._t(key)

    def _tf(self, key: str, **kwargs) -> str:
        return self.win._tf(key, **kwargs)

    def _settings_set(self, key: str, value):
        self.win._settings_set(key, value)

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
            QMessageBox.warning(self.win, self._t("error"), self._t("folder_not_found"))

    # ---- status ----

    def set_status(self, key: str):
        """Update the sidebar status label."""
        self.win.status_key = key
        if key == "downloading":
            self.win.status_value.setText(self._t("downloading"))
            self.win.status_value.setProperty("state", "downloading")
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
        self.win.queue.add_row(
            url=url, fmt=fmt, status_key="queued", pct=0,
            settings_set_fn=self._settings_set,
        )

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
            self.win.queue.add_row(
                url=url, fmt=fmt, status_key="queued", pct=0,
                settings_set_fn=self._settings_set,
            )
            return

        # Expand now
        self.win.add_log(self._t("expanding_playlist"))
        try:
            urls = self.expand_playlist_to_urls(url, limit=data.get("limit", 200))
        except Exception as e:
            QMessageBox.warning(self.win, self._t("error"), str(e))
            return

        if not urls:
            QMessageBox.warning(self.win, self._t("error"), self._t("playlist_no_items"))
            return

        for u in urls:
            self.win.queue.add_row(
                url=u, fmt=fmt, status_key="queued", pct=0,
                auto_save=False,
            )
        self.win.queue.save(self._settings_set)
        self.win.add_log(self._tf("playlist_items_added", count=len(urls)))

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
        for u in urls:
            self.win.queue.add_row(
                url=u, fmt=fmt, status_key="queued", pct=0,
                auto_save=False,
            )
        self.win.queue.save(self._settings_set)

    # ---- playlist expansion ----

    def expand_playlist_to_urls(self, playlist_url: str, limit: int = 200) -> list[str]:
        """Expand a playlist URL into a deduplicated list of watch URLs."""
        info = self.win.downloader.get_info(playlist_url)

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
        """Start downloading all queued items via a background QThread."""
        queued = self.win.queue.get_queued_rows(
            fallback_fmt=self.win.format_box.currentText(),
        )
        if not queued:
            QMessageBox.warning(self.win, self._t("no_urls_title"), self._t("no_queued_body"))
            return

        urls = [u for (_r, u, _f) in queued]
        fmt = self.win.format_box.currentText()
        q = self.win.quality_box.currentText()

        self.win.download_btn.setEnabled(False)
        self.win.download_btn.setText(self._t("downloading"))
        self.set_status("downloading")
        self.win.progress_bar.setValue(0)

        # Thread + worker
        self.win.thread = QThread()
        self.win.worker = DownloadWorker(self.win.downloader, urls, fmt, q)
        self.win.worker.moveToThread(self.win.thread)

        self.win.thread.started.connect(self.win.worker.run)
        self.win.worker.progress.connect(self.win.progress_bar.setValue)
        self.win.worker.status_key.connect(self.set_status)
        self.win.worker.log_event.connect(self.on_log_event)
        self.win.worker.item_update.connect(self.on_item_update)
        self.win.worker.finished.connect(self.win.thread.quit)
        self.win.worker.finished.connect(self.win.worker.deleteLater)
        self.win.thread.finished.connect(self.win.thread.deleteLater)
        self.win.thread.finished.connect(self.on_worker_finished)

        self.win.thread.start()

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
            self.win.now_label.setText(self._tf(key, **args))

    def on_item_update(self, row: int, status_key: str, pct: int, title: str, out_file: str):
        """Route a Worker item_update signal to the queue manager."""
        self.win.queue.update_item(
            row, status_key, pct, title, out_file,
            settings_set_fn=self._settings_set,
        )

    def on_worker_finished(self):
        """Re-enable UI after the download thread finishes."""
        self.win.download_btn.setEnabled(True)
        self.win.download_btn.setText(self._t("download"))
        self.set_status("idle")
        self.win.now_card.clear()
