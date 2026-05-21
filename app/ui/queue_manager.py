"""Manages the queue table: add/update rows, persistence via QSettings, expand modal."""

from __future__ import annotations

import json
from typing import Callable
from uuid import uuid4

from pathlib import Path

from PySide6.QtCore import QPoint, Qt, QSize
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap, QPolygon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHeaderView,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
)


STATUS_COLORS = {
    "queued": (QColor("#9DA9B8"), QColor("#18222D")),
    "downloading": (QColor("#D9A441"), QColor("#282316")),
    "done": (QColor("#4EBB78"), QColor("#18251C")),
    "error": (QColor("#D86C6C"), QColor("#281B1B")),
    "cancelled": (QColor("#7E8B9A"), QColor("#1A2028")),
}

ROW_ID_ROLE = int(Qt.UserRole) + 10
OUTPUT_ROLE = int(Qt.UserRole) + 11
THUMBNAIL_URL_ROLE = int(Qt.UserRole) + 12
UPLOADER_ROLE = int(Qt.UserRole) + 13
DURATION_ROLE = int(Qt.UserRole) + 14


class QueueManager:
    """Encapsulates all operations on the downloads queue table."""

    def __init__(self, table: QTableWidget, t_fn: Callable[[str], str]):
        self._table = table
        self._t = t_fn
        self._can_modify_fn: Callable[[], bool] | None = None
        self._settings_set_fn: Callable | None = None
        self._active_row_id: str | None = None
        self._placeholder_icon = self._build_placeholder_icon()

    def set_t(self, t_fn: Callable[[str], str]):
        self._t = t_fn
        self.refresh_headers()
        self.refresh_action_buttons()
        for row in range(self._table.rowCount()):
            item = self._table.item(row, 5)
            if item:
                item.setToolTip(self._output_tooltip(self._output_path_for_row(row)))

    def set_can_modify_fn(self, fn: Callable[[], bool] | None):
        self._can_modify_fn = fn

    def set_settings_set_fn(self, fn: Callable | None):
        self._settings_set_fn = fn

    def refresh_headers(self):
        self._table.setHorizontalHeaderLabels(
            [
                self._t("col_title"),
                self._t("col_url"),
                self._t("col_format"),
                self._t("col_status"),
                self._t("col_progress"),
                self._t("col_cover"),
                "",
            ]
        )

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
        thumbnail_data: bytes | None = None,
        thumbnail_url: str = "",
        uploader: str = "",
        duration: int | None = None,
        row_id: str | None = None,
    ) -> str:
        if settings_set_fn:
            self._settings_set_fn = settings_set_fn

        row_id = row_id or uuid4().hex
        row = self._table.rowCount()
        self._table.insertRow(row)

        self._set_title_cell(
            row,
            title,
            row_id,
            thumbnail_url=thumbnail_url,
            uploader=uploader,
            duration=duration,
        )
        self._set_text_cell(row, 1, url, row_id)
        self._set_text_cell(row, 2, fmt, row_id)
        self._set_thumbnail_cell(
            row,
            row_id=row_id,
            thumbnail_data=thumbnail_data,
            out_file=out_file,
        )

        self._set_status_cell(row, status_key)
        self._set_progress_cell(row, pct)
        self._add_delete_button(row, row_id)

        if auto_save and self._settings_set_fn:
            self.save(self._settings_set_fn)

        return row_id

    def build(self, urls: list[str], fmt: str, settings_set_fn: Callable | None = None):
        if settings_set_fn:
            self._settings_set_fn = settings_set_fn

        self._table.setRowCount(0)
        for url in urls:
            self.add_row(url=url, fmt=fmt, status_key="queued", pct=0, auto_save=False)
        if self._settings_set_fn:
            self.save(self._settings_set_fn)

    def get_queued_rows(self, fallback_fmt: str = "mp3") -> list[tuple[str, str, str, dict]]:
        out: list[tuple[str, str, str, dict]] = []
        for row in range(self._table.rowCount()):
            status_item = self._table.item(row, 3)
            status_key = status_item.data(Qt.UserRole) if status_item else "queued"
            if status_key != "queued":
                continue

            url = self._table.item(row, 1).text() if self._table.item(row, 1) else ""
            fmt = self._table.item(row, 2).text() if self._table.item(row, 2) else fallback_fmt
            row_id = self._row_id_for_row(row)
            if row_id and url.strip():
                out.append((row_id, url.strip(), fmt, self._metadata_for_row(row)))
        return out

    def update_item(
        self,
        row_id: str,
        status_key: str,
        pct: int,
        title: str,
        out_file: str,
        settings_set_fn: Callable | None = None,
    ):
        if settings_set_fn:
            self._settings_set_fn = settings_set_fn

        row = self.find_row(row_id)
        if row < 0:
            return

        if title:
            self._set_title_cell(row, title, row_id)

        self._set_status_cell(row, status_key)
        self._set_progress_cell(row, pct)

        if out_file:
            self._set_thumbnail_cell(row, row_id=row_id, out_file=out_file)

        self._add_delete_button(row, row_id)

        if self._settings_set_fn and (status_key in ("done", "error", "cancelled") or pct in (0, 100)):
            self.save(self._settings_set_fn)

    def update_metadata(
        self,
        row_id: str,
        *,
        title: str = "",
        thumbnail_data: bytes | None = None,
        thumbnail_url: str = "",
        uploader: str = "",
        duration: int | None = None,
        settings_set_fn: Callable | None = None,
    ):
        if settings_set_fn:
            self._settings_set_fn = settings_set_fn

        row = self.find_row(row_id)
        if row < 0:
            return

        if title:
            self._set_title_cell(
                row,
                title,
                row_id,
                thumbnail_url=thumbnail_url,
                uploader=uploader,
                duration=duration,
            )
        if thumbnail_data:
            self._set_thumbnail_cell(row, row_id=row_id, thumbnail_data=thumbnail_data)

        if self._settings_set_fn:
            self.save(self._settings_set_fn)

    def set_active_row(self, row_id: str | None):
        self._active_row_id = row_id
        self.refresh_action_buttons()

    def refresh_action_buttons(self):
        for row in range(self._table.rowCount()):
            btn = self._table.cellWidget(row, 6)
            if isinstance(btn, QToolButton):
                is_active = self._row_id_for_row(row) == self._active_row_id
                btn.setEnabled(not is_active)
                btn.setToolTip(
                    self._t("delete_active_item") if is_active else self._t("delete_row")
                )

    def find_row(self, row_id: str) -> int:
        if not row_id:
            return -1

        for row in range(self._table.rowCount()):
            if self._row_id_for_row(row) == row_id:
                return row
        return -1

    def save(self, settings_set_fn: Callable):
        self._settings_set_fn = settings_set_fn

        rows = []
        for row in range(self._table.rowCount()):
            title = self._table.item(row, 0).text() if self._table.item(row, 0) else ""
            url = self._table.item(row, 1).text() if self._table.item(row, 1) else ""
            fmt = self._table.item(row, 2).text() if self._table.item(row, 2) else ""
            row_id = self._row_id_for_row(row)
            meta = self._metadata_for_row(row)

            status_item = self._table.item(row, 3)
            status_key = status_item.data(Qt.UserRole) if status_item else "queued"

            prog_item = self._table.item(row, 4)
            pct = prog_item.data(Qt.UserRole) if prog_item else 0

            rows.append(
                {
                    "row_id": row_id,
                    "title": title,
                    "url": url,
                    "format": fmt,
                    "status": status_key,
                    "progress": int(pct) if pct is not None else 0,
                    "output": self._output_path_for_row(row),
                    "thumbnail": meta.get("thumbnail", ""),
                    "uploader": meta.get("uploader", ""),
                    "duration": meta.get("duration"),
                }
            )

        settings_set_fn("ui/queue_history", json.dumps(rows, ensure_ascii=False))

    def load(self, settings_get_fn: Callable):
        raw = settings_get_fn("ui/queue_history", "")
        if not raw:
            return

        try:
            rows = json.loads(raw)
        except Exception:
            return

        self._table.setRowCount(0)
        for item in rows:
            self.add_row(
                url=item.get("url", ""),
                fmt=item.get("format", ""),
                title=item.get("title", ""),
                status_key=item.get("status", "queued"),
                pct=item.get("progress", 0),
                out_file=item.get("output", ""),
                auto_save=False,
                thumbnail_url=item.get("thumbnail", ""),
                uploader=item.get("uploader", ""),
                duration=item.get("duration"),
                row_id=item.get("row_id") or None,
            )

    def open_modal(self, parent):
        dlg = QDialog(parent)
        dlg.setObjectName("AppDialog")
        dlg.setWindowTitle(self._t("downloads_queue"))
        dlg.resize(1100, 650)

        lay = QVBoxLayout(dlg)

        table = QTableWidget(self._table.rowCount(), self._table.columnCount())
        table.setObjectName("QueueTable")
        table.setHorizontalHeaderLabels(
            [
                self._t("col_title"),
                self._t("col_url"),
                self._t("col_format"),
                self._t("col_status"),
                self._t("col_progress"),
                self._t("col_cover"),
                "",
            ]
        )
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(70)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setAlternatingRowColors(True)
        table.setIconSize(self._table.iconSize())

        for row in range(self._table.rowCount()):
            for col in range(self._table.columnCount()):
                src = self._table.item(row, col)
                if col == 6:
                    row_id = self._row_id_for_row(row)
                    btn = self._make_delete_button(table, row_id)
                    btn.clicked.connect(lambda _checked=False, b=btn, t=table: self._delete_modal_row(b, t, dlg))
                    is_active = row_id == self._active_row_id
                    btn.setEnabled(not is_active)
                    btn.setToolTip(
                        self._t("delete_active_item") if is_active else self._t("delete_row")
                    )
                    table.setCellWidget(row, col, btn)
                    continue
                if not src:
                    continue
                dst = QTableWidgetItem(src.text())
                dst.setData(Qt.UserRole, src.data(Qt.UserRole))
                dst.setData(ROW_ID_ROLE, src.data(ROW_ID_ROLE))
                dst.setData(OUTPUT_ROLE, src.data(OUTPUT_ROLE))
                dst.setData(THUMBNAIL_URL_ROLE, src.data(THUMBNAIL_URL_ROLE))
                dst.setData(UPLOADER_ROLE, src.data(UPLOADER_ROLE))
                dst.setData(DURATION_ROLE, src.data(DURATION_ROLE))
                dst.setForeground(src.foreground())
                dst.setBackground(src.background())
                dst.setToolTip(src.toolTip())
                dst.setIcon(src.icon())
                dst.setTextAlignment(src.textAlignment())
                table.setItem(row, col, dst)

        hdr = table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(5, QHeaderView.Fixed)
        hdr.setSectionResizeMode(6, QHeaderView.Fixed)
        table.setColumnWidth(5, self._table.columnWidth(5))
        table.setColumnWidth(6, 36)

        lay.addWidget(table)
        dlg.exec()

    def clear(self, *, settings_set_fn: Callable | None = None, parent=None, confirm: bool = True):
        if self._table.rowCount() == 0:
            return

        if parent is not None and getattr(parent, "status_key", "idle") == "downloading":
            QMessageBox.warning(parent, self._t("error_title"), self._t("cannot_edit_while_downloading"))
            return

        if confirm and parent is not None:
            res = QMessageBox.question(
                parent,
                self._t("confirm"),
                self._t("clear_queue_confirm"),
                QMessageBox.Yes | QMessageBox.No,
            )
            if res != QMessageBox.Yes:
                return

        self._table.setRowCount(0)
        self._active_row_id = None
        if settings_set_fn:
            self.save(settings_set_fn)

    def _row_id_for_row(self, row: int) -> str:
        item = self._table.item(row, 0)
        return item.data(ROW_ID_ROLE) if item else ""

    def _metadata_for_row(self, row: int) -> dict:
        item = self._table.item(row, 0)
        if not item:
            return {}
        return {
            "title": item.text(),
            "thumbnail": item.data(THUMBNAIL_URL_ROLE) or "",
            "uploader": item.data(UPLOADER_ROLE) or "",
            "duration": item.data(DURATION_ROLE),
        }

    def _output_path_for_row(self, row: int) -> str:
        item = self._table.item(row, 5)
        if not item:
            return ""
        return item.data(OUTPUT_ROLE) or ""

    def _set_text_cell(self, row: int, col: int, text: str, row_id: str):
        item = self._table.item(row, col)
        if not item:
            item = QTableWidgetItem()
            self._table.setItem(row, col, item)
        item.setData(ROW_ID_ROLE, row_id)
        item.setText(text)
        item.setToolTip(text)

    def _set_title_cell(
        self,
        row: int,
        title: str,
        row_id: str,
        *,
        thumbnail_url: str = "",
        uploader: str = "",
        duration: int | None = None,
    ):
        self._set_text_cell(row, 0, title, row_id)
        item = self._table.item(row, 0)
        if not item:
            return
        if thumbnail_url:
            item.setData(THUMBNAIL_URL_ROLE, thumbnail_url)
        if uploader:
            item.setData(UPLOADER_ROLE, uploader)
        if duration:
            item.setData(DURATION_ROLE, int(duration))

    def _add_delete_button(self, row: int, row_id: str):
        btn = self._table.cellWidget(row, 6)
        if not isinstance(btn, QToolButton):
            btn = self._make_delete_button(self._table, row_id)
            btn.clicked.connect(lambda: self._delete_row_from_button(btn))
            self._table.setCellWidget(row, 6, btn)

        btn.setProperty("row_id", row_id)
        self.refresh_action_buttons()

    def _make_delete_button(self, parent, row_id: str) -> QToolButton:
        btn = QToolButton(parent)
        btn.setText("x")
        btn.setObjectName("RowDeleteButton")
        btn.setProperty("row_id", row_id)
        return btn

    def _delete_row_from_button(self, btn: QToolButton):
        row_id = btn.property("row_id")
        if not row_id:
            return
        self.delete_row(row_id, parent=self._table)

    def _delete_modal_row(self, btn: QToolButton, table: QTableWidget, parent) -> None:
        row_id = btn.property("row_id")
        if not row_id:
            return

        point = btn.mapTo(table.viewport(), QPoint(0, 0))
        idx = table.indexAt(point)
        if not idx.isValid():
            return

        if self.delete_row(row_id, parent=parent):
            table.removeRow(idx.row())

    def delete_row(self, row_id: str, parent=None) -> bool:
        if row_id and row_id == self._active_row_id:
            QMessageBox.warning(parent or self._table, self._t("error_title"), self._t("delete_active_item"))
            return False

        if self._can_modify_fn and not self._can_modify_fn():
            QMessageBox.warning(parent or self._table, self._t("error_title"), self._t("cannot_edit_while_downloading"))
            return False

        row = self.find_row(row_id)
        if row < 0:
            return False

        self._table.removeRow(row)

        if self._settings_set_fn:
            self.save(self._settings_set_fn)
        return True

    def _set_status_cell(self, row: int, status_key: str):
        item = self._table.item(row, 3)
        if not item:
            item = QTableWidgetItem()
            self._table.setItem(row, 3, item)
        item.setData(Qt.UserRole, status_key)
        item.setData(ROW_ID_ROLE, self._row_id_for_row(row))

        status_map = {
            "queued": self._t("status_queued"),
            "downloading": self._t("status_downloading"),
            "done": self._t("status_done"),
            "error": self._t("status_error"),
            "cancelled": self._t("status_cancelled"),
        }
        item.setText(status_map.get(status_key, status_key))

        fg, bg = STATUS_COLORS.get(status_key, STATUS_COLORS["queued"])
        item.setForeground(fg)
        item.setBackground(bg)

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
        item.setData(ROW_ID_ROLE, self._row_id_for_row(row))
        item.setText(f"{pct}%")

        status_item = self._table.item(row, 3)
        if status_item:
            status_key = status_item.data(Qt.UserRole) or "queued"
            fg, bg = STATUS_COLORS.get(status_key, STATUS_COLORS["queued"])
            item.setForeground(fg)
            item.setBackground(bg)

    def _set_thumbnail_cell(
        self,
        row: int,
        *,
        row_id: str | None = None,
        thumbnail_data: bytes | None = None,
        out_file: str | None = None,
        tooltip: str | None = None,
    ):
        item = self._table.item(row, 5)
        if not item:
            item = QTableWidgetItem()
            item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row, 5, item)

        current_row_id = row_id or self._row_id_for_row(row)
        current_output = out_file if out_file is not None else self._output_path_for_row(row)

        item.setData(ROW_ID_ROLE, current_row_id)
        item.setData(OUTPUT_ROLE, current_output)
        item.setText("")
        item.setToolTip(tooltip or self._output_tooltip(current_output))

        icon = item.icon()
        if icon.isNull():
            icon = self._placeholder_icon
        embedded_cover = None if thumbnail_data else self._cover_data_from_output(current_output)
        cover_data = thumbnail_data or embedded_cover
        if cover_data:
            pixmap = QPixmap()
            if pixmap.loadFromData(cover_data):
                scaled = pixmap.scaled(
                    QSize(72, 40),
                    Qt.KeepAspectRatioByExpanding,
                    Qt.SmoothTransformation,
                )
                if scaled.width() > 72 or scaled.height() > 40:
                    x = max(0, (scaled.width() - 72) // 2)
                    y = max(0, (scaled.height() - 40) // 2)
                    scaled = scaled.copy(x, y, 72, 40)
                icon = QIcon(scaled)
        item.setIcon(icon)

    def _output_tooltip(self, out_file: str) -> str:
        if not out_file:
            return self._t("cover_tooltip_pending")
        try:
            return self._t("cover_embedded").format(path=out_file)
        except Exception:
            return out_file

    def _build_placeholder_icon(self) -> QIcon:
        pixmap = QPixmap(72, 40)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(QColor("#3B4A5E"))
        painter.setBrush(QColor("#18222D"))
        painter.drawRoundedRect(0, 0, 71, 39, 8, 8)
        painter.setBrush(QColor("#7C8898"))
        painter.setPen(Qt.NoPen)
        painter.drawPolygon(QPolygon([QPoint(29, 12), QPoint(29, 28), QPoint(45, 20)]))
        painter.end()
        return QIcon(pixmap)

    def _cover_data_from_output(self, out_file: str | None) -> bytes | None:
        if not out_file:
            return None

        path = Path(out_file)
        if not path.exists():
            return None

        suffix = path.suffix.lower()
        try:
            if suffix == ".mp3":
                from mutagen.id3 import ID3

                tags = ID3(path)
                covers = tags.getall("APIC")
                return bytes(covers[0].data) if covers else None

            if suffix == ".m4a":
                from mutagen.mp4 import MP4

                tags = MP4(path)
                covers = tags.tags.get("covr") if tags.tags else None
                return bytes(covers[0]) if covers else None
        except Exception:
            return None

        return None
