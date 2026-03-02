# app/ui/queue_manager.py
"""Manages the queue table: add/update rows, persistence via QSettings, expand modal."""

from __future__ import annotations

import json
from typing import Callable

from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QDialog, QVBoxLayout,
)
from PySide6.QtGui import Qt, QColor


# Status → (foreground, background)
STATUS_COLORS = {
    "queued":      (QColor("#8899AA"), QColor("#131D2A")),
    "downloading": (QColor("#F59E0B"), QColor("#1E1A0D")),
    "done":        (QColor("#34D399"), QColor("#0D1E16")),
    "error":       (QColor("#F87171"), QColor("#1E0D0D")),
    "cancelled":   (QColor("#6B7280"), QColor("#151515")),
}


class QueueManager:
    """Encapsulates all operations on the downloads queue table.

    Args:
        table: The QTableWidget created by the window.
        t_fn:  Translation callable ``t(key) -> str``.
    """

    def __init__(self, table: QTableWidget, t_fn: Callable[[str], str]):
        self._table = table
        self._t = t_fn

    # ---- public: update translation callable when language changes ----

    def set_t(self, t_fn: Callable[[str], str]):
        """Replace the translation function (called on language switch)."""
        self._t = t_fn

    def refresh_headers(self):
        """Re-apply translated column headers."""
        self._table.setHorizontalHeaderLabels([
            self._t("col_title"),
            self._t("col_url"),
            self._t("col_format"),
            self._t("col_status"),
            self._t("col_progress"),
            self._t("col_output"),
        ])

    # ---- row operations ----

    def add_row(
        self,
        url: str,
        fmt: str,
        title: str = "",
        status_key: str = "queued",
        pct: int = 0,
        out_file: str = "",
        *,
        auto_save: bool = True,
        settings_set_fn: Callable | None = None,
    ):
        """Insert a new row at the bottom of the queue."""
        row = self._table.rowCount()
        self._table.insertRow(row)

        self._table.setItem(row, 0, QTableWidgetItem(title))     # Title
        self._table.setItem(row, 1, QTableWidgetItem(url))       # URL
        self._table.setItem(row, 2, QTableWidgetItem(fmt))       # Format
        self._table.setItem(row, 5, QTableWidgetItem(out_file))  # Output

        # Set tooltips for long-text columns
        self._table.item(row, 0).setToolTip(title)
        self._table.item(row, 1).setToolTip(url)
        self._table.item(row, 5).setToolTip(out_file)

        self._set_status_cell(row, status_key)
        self._set_progress_cell(row, pct)

        if auto_save and settings_set_fn:
            self.save(settings_set_fn)

    def build(self, urls: list[str], fmt: str, settings_set_fn: Callable | None = None):
        """(legacy) Reset table and rebuild from a list of URLs."""
        self._table.setRowCount(0)
        for url in urls:
            self.add_row(url=url, fmt=fmt, status_key="queued", pct=0, auto_save=False)
        if settings_set_fn:
            self.save(settings_set_fn)

    def get_queued_rows(self, fallback_fmt: str = "mp3") -> list[tuple[int, str, str]]:
        """Return ``[(row_index, url, format)]`` for items with status ``'queued'``."""
        out: list[tuple[int, str, str]] = []
        for r in range(self._table.rowCount()):
            status_item = self._table.item(r, 3)
            status_key = status_item.data(Qt.UserRole) if status_item else "queued"
            if status_key != "queued":
                continue
            url = self._table.item(r, 1).text() if self._table.item(r, 1) else ""
            fmt = self._table.item(r, 2).text() if self._table.item(r, 2) else fallback_fmt
            if url.strip():
                out.append((r, url.strip(), fmt))
        return out

    def update_item(
        self,
        row: int,
        status_key: str,
        pct: int,
        title: str,
        out_file: str,
        settings_set_fn: Callable | None = None,
    ):
        """Update a single row from a Worker signal."""
        if title and self._table.item(row, 0):
            self._table.item(row, 0).setText(title)
            self._table.item(row, 0).setToolTip(title)

        self._set_status_cell(row, status_key)
        self._set_progress_cell(row, pct)

        if out_file and self._table.item(row, 5):
            self._table.item(row, 5).setText(out_file)
            self._table.item(row, 5).setToolTip(out_file)

        if settings_set_fn and (status_key in ("done", "error", "cancelled") or pct in (0, 100)):
            self.save(settings_set_fn)

    # ---- persistence ----

    def save(self, settings_set_fn: Callable):
        """Serialize queue rows to JSON and persist via *settings_set_fn*."""
        rows = []
        for r in range(self._table.rowCount()):
            title = self._table.item(r, 0).text() if self._table.item(r, 0) else ""
            url = self._table.item(r, 1).text() if self._table.item(r, 1) else ""
            fmt = self._table.item(r, 2).text() if self._table.item(r, 2) else ""

            status_item = self._table.item(r, 3)
            status_key = status_item.data(Qt.UserRole) if status_item else "queued"

            prog_item = self._table.item(r, 4)
            pct = prog_item.data(Qt.UserRole) if prog_item else 0

            outp = self._table.item(r, 5).text() if self._table.item(r, 5) else ""

            rows.append({
                "title": title,
                "url": url,
                "format": fmt,
                "status": status_key,
                "progress": int(pct) if pct is not None else 0,
                "output": outp,
            })

        settings_set_fn("ui/queue_history", json.dumps(rows, ensure_ascii=False))

    def load(self, settings_get_fn: Callable):
        """Restore queue rows from JSON stored in QSettings."""
        raw = settings_get_fn("ui/queue_history", "")
        if not raw:
            return
        try:
            rows = json.loads(raw)
        except Exception:
            return

        self._table.setRowCount(0)
        for x in rows:
            row = self._table.rowCount()
            self._table.insertRow(row)

            title = x.get("title", "")
            url = x.get("url", "")
            outp = x.get("output", "")

            item_title = QTableWidgetItem(title)
            item_title.setToolTip(title)
            self._table.setItem(row, 0, item_title)

            item_url = QTableWidgetItem(url)
            item_url.setToolTip(url)
            self._table.setItem(row, 1, item_url)

            self._table.setItem(row, 2, QTableWidgetItem(x.get("format", "")))

            item_out = QTableWidgetItem(outp)
            item_out.setToolTip(outp)
            self._table.setItem(row, 5, item_out)

            self._set_status_cell(row, x.get("status", "queued"))
            self._set_progress_cell(row, x.get("progress", 0))

    # ---- modal ----

    def open_modal(self, parent):
        """Open a read-only expanded view of the queue in a modal dialog."""
        dlg = QDialog(parent)
        dlg.setObjectName("AppDialog")
        dlg.setWindowTitle(self._t("downloads_queue"))
        dlg.resize(1100, 650)

        lay = QVBoxLayout(dlg)

        t = QTableWidget(self._table.rowCount(), self._table.columnCount())
        t.setObjectName("QueueTable")
        t.setHorizontalHeaderLabels([
            self._t("col_title"),
            self._t("col_url"),
            self._t("col_format"),
            self._t("col_status"),
            self._t("col_progress"),
            self._t("col_output"),
            ""  # actions column (sin texto)

        ])
        t.verticalHeader().setVisible(False)
        t.verticalHeader().setDefaultSectionSize(70)
        t.setEditTriggers(QAbstractItemView.NoEditTriggers)
        t.setSelectionBehavior(QAbstractItemView.SelectRows)
        t.setAlternatingRowColors(True)

        # Copy content (including UserRole data and colors)
        for r in range(self._table.rowCount()):
            for c in range(self._table.columnCount()):
                src = self._table.item(r, c)
                if not src:
                    continue
                dst = QTableWidgetItem(src.text())
                dst.setData(Qt.UserRole, src.data(Qt.UserRole))
                dst.setForeground(src.foreground())
                dst.setBackground(src.background())
                dst.setToolTip(src.toolTip())
                t.setItem(r, c, dst)

        hdr = t.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(5, QHeaderView.Stretch)
        # Columna actions: fija y chiquita
        hdr.setSectionResizeMode(6, QHeaderView.Fixed)
        t.setColumnWidth(6, 36)

        lay.addWidget(t)
        dlg.exec()

    # ---- internal helpers ----
    
    def _set_status_cell(self, row: int, status_key: str):
        item = self._table.item(row, 3)
        if not item:
            item = QTableWidgetItem()
            self._table.setItem(row, 3, item)
        item.setData(Qt.UserRole, status_key)

        status_map = {
            "queued": self._t("status_queued"),
            "downloading": self._t("status_downloading"),
            "done": self._t("status_done"),
            "error": self._t("status_error"),
            "cancelled": self._t("status_cancelled"),
        }
        item.setText(status_map.get(status_key, status_key))

        # Apply colors to status cell and the progress cell
        fg, bg = STATUS_COLORS.get(status_key, STATUS_COLORS["queued"])
        item.setForeground(fg)
        item.setBackground(bg)

        # Also color the progress cell
        prog_item = self._table.item(row, 4)
        if prog_item:
            prog_item.setForeground(fg)
            prog_item.setBackground(bg)

    def _set_progress_cell(self, row: int, pct: int):
        pct = max(0, min(100, int(pct)))
        item = self._table.item(row, 4)
        if not item:
            item = QTableWidgetItem()
            self._table.setItem(row, 4, item)
        item.setData(Qt.UserRole, pct)
        item.setText(f"{pct}%")

        # Apply colors matching status
        status_item = self._table.item(row, 3)
        if status_item:
            sk = status_item.data(Qt.UserRole) or "queued"
            fg, bg = STATUS_COLORS.get(sk, STATUS_COLORS["queued"])
            item.setForeground(fg)
            item.setBackground(bg)
