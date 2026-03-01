# app/ui/window.py
import os
import json
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QLabel, QFileDialog, QComboBox, QProgressBar, QMessageBox, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QSplitter,
    QDialog, QLineEdit, QCheckBox, QSpinBox
)
from PySide6.QtCore import QThread, QUrl
from PySide6.QtGui import QFont, QIcon, QDesktopServices, Qt

from app.downloader import MediaDownloader
from app.ui.worker import DownloadWorker
from app.ui.i18n import TRANSLATIONS
from app.ui.widgets import add_shadow, set_elided
from app.ui.style import main_qss
from app.ui.settings import AppSettings


# ----------------- Dialogs -----------------

class AddSongDialog(QDialog):
    def __init__(self, parent=None, t=lambda k, **kw: k):
        super().__init__(parent)
        self.t = t
        self.setWindowTitle(self.t("add_song"))
        self.resize(560, 170)

        lay = QVBoxLayout(self)

        lay.addWidget(QLabel(self.t("song_url")))
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText(self.t("enter_url"))
        lay.addWidget(self.url_edit)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        self.btn_cancel = QPushButton(self.t("cancel"))
        self.btn_add = QPushButton(self.t("add"))
        self.btn_add.setObjectName("PrimaryButton")
        self.btn_cancel.setObjectName("SecondaryButton")
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_add.clicked.connect(self.accept)
        btn_row.addWidget(self.btn_cancel)
        btn_row.addWidget(self.btn_add)
        lay.addLayout(btn_row)

    def url(self) -> str:
        return self.url_edit.text().strip()


class AddPlaylistDialog(QDialog):
    def __init__(self, parent=None, t=lambda k, **kw: k):
        super().__init__(parent)
        self.t = t
        self.setWindowTitle(self.t("add_playlist"))
        self.resize(620, 240)

        lay = QVBoxLayout(self)

        lay.addWidget(QLabel(self.t("playlist_url")))
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText(self.t("enter_playlist_url"))
        lay.addWidget(self.url_edit)

        self.chk_expand = QCheckBox(self.t("expand_now"))
        self.chk_expand.setChecked(True)
        lay.addWidget(self.chk_expand)

        limit_row = QHBoxLayout()
        limit_row.addWidget(QLabel(self.t("max_items")))
        self.spin_limit = QSpinBox()
        self.spin_limit.setRange(1, 5000)
        self.spin_limit.setValue(200)
        limit_row.addWidget(self.spin_limit)
        limit_row.addStretch(1)
        lay.addLayout(limit_row)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        self.btn_cancel = QPushButton(self.t("cancel"))
        self.btn_add = QPushButton(self.t("add"))
        self.btn_add.setObjectName("PrimaryButton")
        self.btn_cancel.setObjectName("SecondaryButton")
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_add.clicked.connect(self.accept)
        btn_row.addWidget(self.btn_cancel)
        btn_row.addWidget(self.btn_add)
        lay.addLayout(btn_row)

    def data(self) -> dict:
        return {
            "url": self.url_edit.text().strip(),
            "expand": self.chk_expand.isChecked(),
            "limit": int(self.spin_limit.value()),
        }


class PasteBatchDialog(QDialog):
    def __init__(self, parent=None, t=lambda k, **kw: k):
        super().__init__(parent)
        self.t = t
        self.setWindowTitle(self.t("paste_batch"))
        self.resize(780, 420)

        lay = QVBoxLayout(self)

        self.text = QTextEdit()
        self.text.setObjectName("TextArea")
        self.text.setPlaceholderText("https://youtu.be/VIDEO_ID\nhttps://youtu.be/ANOTHER_ID")
        lay.addWidget(self.text, 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        self.btn_cancel = QPushButton(self.t("cancel"))
        self.btn_add = QPushButton(self.t("add"))
        self.btn_add.setObjectName("PrimaryButton")
        self.btn_cancel.setObjectName("SecondaryButton")
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_add.clicked.connect(self.accept)
        btn_row.addWidget(self.btn_cancel)
        btn_row.addWidget(self.btn_add)
        lay.addLayout(btn_row)

    def urls(self) -> list[str]:
        return [u.strip() for u in self.text.toPlainText().splitlines() if u.strip()]


# ----------------- Main Window -----------------

class MainWindow(QMainWindow):
    def closeEvent(self, event):
        self.save_queue()
        self.settings.save_geometry(self)
        super().closeEvent(event)

    def __init__(self):
        super().__init__()

        # Settings (persist language + folder)
        self.settings = AppSettings()
        self.lang = self.settings.get_language()
        self.output_folder = self.settings.get_output_folder()

        self.setWindowIcon(QIcon(os.path.join("assets", "icon.ico")))
        self.downloader = MediaDownloader(output_path=self.output_folder)

        self.thread = None
        self.worker = None

        self.setWindowTitle(TRANSLATIONS[self.lang]["app_name"])
        self.setMinimumSize(1040, 680)

        app_font = QFont("Segoe UI Variable", 10)
        if not app_font.exactMatch():
            app_font = QFont("Segoe UI", 10)
        self.setFont(app_font)

        self._i18n_bindings = []  # list of (widget, key, attr)

        self.build_ui()
        self.apply_style()
        self.apply_language(self.lang)
        self.settings.restore_geometry(self)
        self.load_queue()

        self.add_log(self._t("ready"))

    # ---------------- i18n ----------------
    def _t(self, key: str) -> str:
        return TRANSLATIONS.get(self.lang, TRANSLATIONS["en"]).get(key, key)

    def _tf(self, key: str, **kwargs) -> str:
        template = self._t(key)
        try:
            return template.format(**kwargs)
        except Exception:
            return template

    def _bind_text(self, widget, key: str):
        self._i18n_bindings.append((widget, key, "text"))

    def apply_language(self, lang: str):
        self.lang = "es" if lang == "es" else "en"
        self.settings.set_language(self.lang)
        self.setWindowTitle(self._t("app_name"))

        # Update all bound labels/buttons
        for w, key, attr in self._i18n_bindings:
            if attr == "text":
                w.setText(self._t(key))

        # Update table headers
        if hasattr(self, "queue_table"):
            self.queue_table.setHorizontalHeaderLabels([
                self._t("col_title"),
                self._t("col_url"),
                self._t("col_format"),
                self._t("col_status"),
                self._t("col_progress"),
                self._t("col_output"),
            ])

        # Update dynamic fields
        self.status_value.setText(self._t("idle") if self.status_key == "idle" else self._t("downloading"))
        self.lang_label.setText(self._t("language"))

        if self.download_btn.isEnabled():
            self.download_btn.setText(self._t("download"))
        else:
            self.download_btn.setText(self._t("downloading"))

    def _settings_get(self, key: str, default=None):
        s = getattr(self.settings, "qs", self.settings)
        return s.value(key, default)

    def _settings_set(self, key: str, value):
        s = getattr(self.settings, "qs", self.settings)
        s.setValue(key, value)

    # ---------------- UI ----------------
    def build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)

        main = QHBoxLayout(root)
        main.setContentsMargins(18, 18, 18, 18)
        main.setSpacing(14)

        # Sidebar
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(290)
        s = QVBoxLayout(self.sidebar)
        s.setSpacing(10)
        s.setContentsMargins(16, 16, 16, 16)

        self.brand = QLabel("YouToMp3")
        self.brand.setObjectName("BrandTitle")
        self.brand_sub = QLabel("Desktop Media Downloader")
        self.brand_sub.setObjectName("BrandSub")

        s.addWidget(self.brand)
        s.addWidget(self.brand_sub)

        div = QFrame()
        div.setObjectName("Divider")
        div.setFixedHeight(1)
        s.addWidget(div)

        # Format
        self.lbl_format = QLabel()
        self._bind_text(self.lbl_format, "format")
        s.addWidget(self.lbl_format)

        self.format_box = QComboBox()
        self.format_box.addItems(["mp3", "wav", "m4a"])
        s.addWidget(self.format_box)

        # Quality
        self.lbl_quality = QLabel()
        self._bind_text(self.lbl_quality, "quality")
        s.addWidget(self.lbl_quality)

        self.quality_box = QComboBox()
        self.quality_box.addItems(["320", "192", "128"])
        self.quality_box.setCurrentText("192")
        s.addWidget(self.quality_box)

        # Output
        self.lbl_output = QLabel()
        self._bind_text(self.lbl_output, "output")
        s.addWidget(self.lbl_output)

        self.folder_chip = QLabel(self.output_folder)
        self.folder_chip.setObjectName("Chip")
        self.folder_chip.setWordWrap(False)
        set_elided(self.folder_chip, self.output_folder)
        s.addWidget(self.folder_chip)

        self.folder_btn = QPushButton()
        self._bind_text(self.folder_btn, "select_folder")
        self.folder_btn.setObjectName("SecondaryButton")
        self.folder_btn.clicked.connect(self.select_folder)
        s.addWidget(self.folder_btn)

        self.open_folder_btn = QPushButton()
        self._bind_text(self.open_folder_btn, "open_output_folder")
        self.open_folder_btn.setObjectName("SecondaryButton")
        self.open_folder_btn.clicked.connect(self.open_output_folder)
        s.addWidget(self.open_folder_btn)

        # Status
        s.addSpacing(10)
        self.lbl_status = QLabel()
        self._bind_text(self.lbl_status, "status")
        s.addWidget(self.lbl_status)

        self.status_key = "idle"
        self.status_value = QLabel()
        self.status_value.setObjectName("Status")
        s.addWidget(self.status_value)

        s.addStretch(1)

        # Content
        self.content = QFrame()
        self.content.setObjectName("Content")
        c = QVBoxLayout(self.content)
        c.setSpacing(12)
        c.setContentsMargins(18, 16, 18, 16)

        # Top bar (title + language toggle)
        top = QHBoxLayout()
        left = QVBoxLayout()
        left.setSpacing(2)

        self.h1 = QLabel()
        self.h1.setObjectName("H1")
        self._bind_text(self.h1, "paste_urls")  # puedes renombrar key a "add_media" si quieres

        self.h2 = QLabel()
        self.h2.setObjectName("H2")
        self._bind_text(self.h2, "one_per_line")  # si te molesta el texto, cambia key en i18n

        left.addWidget(self.h1)
        left.addWidget(self.h2)

        top.addLayout(left, 1)

        lang_box = QHBoxLayout()
        lang_box.setSpacing(8)
        self.lang_label = QLabel()
        self.lang_label.setObjectName("LangLabel")
        lang_box.addWidget(self.lang_label)

        self.lang_combo = QComboBox()
        self.lang_combo.addItem("English", "en")
        self.lang_combo.addItem("Español", "es")
        self.lang_combo.setObjectName("LangCombo")
        self.lang_combo.currentIndexChanged.connect(self.on_lang_change)
        lang_box.addWidget(self.lang_combo)

        top.addLayout(lang_box)
        c.addLayout(top)

        # -------- Actions: Add Song / Add Playlist / Paste Batch --------
        action_row = QHBoxLayout()
        action_row.setSpacing(10)

        self.btn_add_song = QPushButton()
        self._bind_text(self.btn_add_song, "add_song")
        self.btn_add_song.setObjectName("SecondaryButton")
        self.btn_add_song.clicked.connect(self.open_add_song_dialog)

        self.btn_add_playlist = QPushButton()
        self._bind_text(self.btn_add_playlist, "add_playlist")
        self.btn_add_playlist.setObjectName("SecondaryButton")
        self.btn_add_playlist.clicked.connect(self.open_add_playlist_dialog)

        self.btn_paste_batch = QPushButton()
        self._bind_text(self.btn_paste_batch, "paste_batch")
        self.btn_paste_batch.setObjectName("SecondaryButton")
        self.btn_paste_batch.clicked.connect(self.open_paste_batch_dialog)

        action_row.addWidget(self.btn_add_song)
        action_row.addWidget(self.btn_add_playlist)
        action_row.addStretch(1)
        action_row.addWidget(self.btn_paste_batch)

        c.addLayout(action_row)

        # Actions row (progress + download)
        actions = QHBoxLayout()
        actions.setSpacing(12)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setObjectName("Progress")
        actions.addWidget(self.progress_bar, 1)

        self.download_btn = QPushButton()
        self.download_btn.setObjectName("PrimaryButton")
        self.download_btn.clicked.connect(self.start_download)
        actions.addWidget(self.download_btn)

        c.addLayout(actions)

        self.now_label = QLabel("")
        self.now_label.setObjectName("NowLabel")
        c.addWidget(self.now_label)

        # Queue Table
        self.queue_table = QTableWidget(0, 6)
        self.queue_table.setObjectName("QueueTable")
        self.queue_table.setHorizontalHeaderLabels([
            self._t("col_title"),
            self._t("col_url"),
            self._t("col_format"),
            self._t("col_status"),
            self._t("col_progress"),
            self._t("col_output"),
        ])
        hdr = self.queue_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)          # title
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)          # url
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents) # format
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents) # status
        hdr.setSectionResizeMode(4, QHeaderView.ResizeToContents) # progress
        hdr.setSectionResizeMode(5, QHeaderView.Stretch)          # output

        self.queue_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.queue_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.queue_table.setAlternatingRowColors(True)
        self.queue_table.verticalHeader().setVisible(False)
        self.queue_table.setShowGrid(True)

        queue_bar = QHBoxLayout()
        self.queue_label = QLabel(self._t("console"))
        self.queue_label.setObjectName("QueueLabel")
        queue_bar.addWidget(self.queue_label)
        queue_bar.addStretch(1)

        self.expand_queue_btn = QPushButton(self._t("expand_table"))
        self.expand_queue_btn.setObjectName("SecondaryButton")
        self.expand_queue_btn.clicked.connect(self.open_queue_modal)
        queue_bar.addWidget(self.expand_queue_btn)

        c.addLayout(queue_bar)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setObjectName("ConsoleArea")

        split = QSplitter(Qt.Vertical)
        split.setChildrenCollapsible(False)
        split.addWidget(self.queue_table)
        split.addWidget(self.log_box)
        split.setSizes([220, 260])

        c.addWidget(split, 3)

        main.addWidget(self.sidebar)
        main.addWidget(self.content, 1)

        # Nice shadows (subtle)
        add_shadow(self.sidebar, color_hex="#0EA5E9", blur=28, x=0, y=10, alpha=35)
        add_shadow(self.content, color_hex="#A855F7", blur=28, x=0, y=10, alpha=25)
        add_shadow(self.download_btn, color_hex="#FB7185", blur=30, x=0, y=10, alpha=45)

        # Load lang selection into combo
        idx = 0 if self.lang == "en" else 1
        self.lang_combo.setCurrentIndex(idx)

    def apply_style(self):
        self.setStyleSheet(main_qss())

    # ----------------- utils -----------------
    def resizeEvent(self, event):
        super().resizeEvent(event)
        set_elided(self.folder_chip, self.output_folder)

    def on_lang_change(self):
        lang = self.lang_combo.currentData()
        self.apply_language(lang)

    def add_log(self, text: str):
        self.log_box.append(text)

    # ----------------- queue helpers -----------------

    def add_queue_row(self, url: str, fmt: str, title: str = "", status_key: str = "queued", pct: int = 0, out_file: str = ""):
        row = self.queue_table.rowCount()
        self.queue_table.insertRow(row)

        self.queue_table.setItem(row, 0, QTableWidgetItem(title))   # Title
        self.queue_table.setItem(row, 1, QTableWidgetItem(url))     # URL
        self.queue_table.setItem(row, 2, QTableWidgetItem(fmt))     # Format
        self.queue_table.setItem(row, 5, QTableWidgetItem(out_file))# Output

        self._set_status_cell(row, status_key)
        self._set_progress_cell(row, pct)

        self.save_queue()

    def build_queue(self, urls: list[str], fmt: str):
        """(legacy) resetea y construye. Ahora preferimos add_queue_row()."""
        self.queue_table.setRowCount(0)
        for url in urls:
            self.add_queue_row(url=url, fmt=fmt, status_key="queued", pct=0)
        self.save_queue()

    def get_queued_rows(self) -> list[tuple[int, str, str]]:
        """Return list of (row_index, url, fmt) for queued items."""
        out = []
        for r in range(self.queue_table.rowCount()):
            status_item = self.queue_table.item(r, 3)
            status_key = status_item.data(Qt.UserRole) if status_item else "queued"
            if status_key != "queued":
                continue
            url = self.queue_table.item(r, 1).text() if self.queue_table.item(r, 1) else ""
            fmt = self.queue_table.item(r, 2).text() if self.queue_table.item(r, 2) else self.format_box.currentText()
            if url.strip():
                out.append((r, url.strip(), fmt))
        return out

    def on_item_update(self, row: int, status_key: str, pct: int, title: str, out_file: str):
        if title and self.queue_table.item(row, 0):
            self.queue_table.item(row, 0).setText(title)

        self._set_status_cell(row, status_key)
        self._set_progress_cell(row, pct)

        if out_file and self.queue_table.item(row, 5):
            self.queue_table.item(row, 5).setText(out_file)

        if status_key in ("done", "error", "cancelled") or pct in (0, 100):
            self.save_queue()

    def _set_status_cell(self, row: int, status_key: str):
        item = self.queue_table.item(row, 3)
        if not item:
            item = QTableWidgetItem()
            self.queue_table.setItem(row, 3, item)
        item.setData(Qt.UserRole, status_key)

        status_map = {
            "queued": self._t("status_queued"),
            "downloading": self._t("status_downloading"),
            "done": self._t("status_done"),
            "error": self._t("status_error"),
            "cancelled": self._t("status_cancelled"),
        }
        item.setText(status_map.get(status_key, status_key))

    def _set_progress_cell(self, row: int, pct: int):
        pct = max(0, min(100, int(pct)))
        item = self.queue_table.item(row, 4)
        if not item:
            item = QTableWidgetItem()
            self.queue_table.setItem(row, 4, item)
        item.setData(Qt.UserRole, pct)
        item.setText(f"{pct}%")

    # ----------------- persistence -----------------

    def save_queue(self):
        rows = []
        for r in range(self.queue_table.rowCount()):
            title = self.queue_table.item(r, 0).text() if self.queue_table.item(r, 0) else ""
            url = self.queue_table.item(r, 1).text() if self.queue_table.item(r, 1) else ""
            fmt = self.queue_table.item(r, 2).text() if self.queue_table.item(r, 2) else ""

            status_item = self.queue_table.item(r, 3)
            status_key = status_item.data(Qt.UserRole) if status_item else "queued"

            prog_item = self.queue_table.item(r, 4)
            pct = prog_item.data(Qt.UserRole) if prog_item else 0

            outp = self.queue_table.item(r, 5).text() if self.queue_table.item(r, 5) else ""

            rows.append({
                "title": title,
                "url": url,
                "format": fmt,
                "status": status_key,
                "progress": int(pct) if pct is not None else 0,
                "output": outp,
            })

        self._settings_set("ui/queue_history", json.dumps(rows, ensure_ascii=False))

    def load_queue(self):
        raw = self._settings_get("ui/queue_history", "")
        if not raw:
            return
        try:
            rows = json.loads(raw)
        except Exception:
            return

        self.queue_table.setRowCount(0)
        for x in rows:
            row = self.queue_table.rowCount()
            self.queue_table.insertRow(row)

            self.queue_table.setItem(row, 0, QTableWidgetItem(x.get("title", "")))
            self.queue_table.setItem(row, 1, QTableWidgetItem(x.get("url", "")))
            self.queue_table.setItem(row, 2, QTableWidgetItem(x.get("format", "")))
            self.queue_table.setItem(row, 5, QTableWidgetItem(x.get("output", "")))

            self._set_status_cell(row, x.get("status", "queued"))
            self._set_progress_cell(row, x.get("progress", 0))

    def open_queue_modal(self):
        dlg = QDialog(self)
        dlg.setWindowTitle(self._t("downloads_queue"))
        dlg.resize(1100, 650)

        lay = QVBoxLayout(dlg)

        t = QTableWidget(self.queue_table.rowCount(), self.queue_table.columnCount())
        t.setHorizontalHeaderLabels([
            self._t("col_title"),
            self._t("col_url"),
            self._t("col_format"),
            self._t("col_status"),
            self._t("col_progress"),
            self._t("col_output"),
        ])
        t.verticalHeader().setVisible(False)
        t.setEditTriggers(QAbstractItemView.NoEditTriggers)
        t.setSelectionBehavior(QAbstractItemView.SelectRows)
        t.setAlternatingRowColors(True)

        # copiar contenido (incluye UserRole)
        for r in range(self.queue_table.rowCount()):
            for c in range(self.queue_table.columnCount()):
                src = self.queue_table.item(r, c)
                if not src:
                    continue
                dst = QTableWidgetItem(src.text())
                dst.setData(Qt.UserRole, src.data(Qt.UserRole))
                t.setItem(r, c, dst)

        hdr = t.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(5, QHeaderView.Stretch)

        lay.addWidget(t)
        dlg.exec()

    # ----------------- actions -----------------

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, self._t("select_folder"))
        if folder:
            self.output_folder = folder
            self.downloader.output_path = folder
            self.settings.set_output_folder(folder)
            set_elided(self.folder_chip, folder)
            self.add_log(self._tf("output_set", folder=folder))

    def open_output_folder(self):
        folder = self.output_folder
        if folder and os.path.isdir(folder):
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder))
        else:
            QMessageBox.warning(self, self._t("error"), self._t("folder_not_found"))

    def set_status(self, key: str):
        self.status_key = key
        if key == "downloading":
            self.status_value.setText(self._t("downloading"))
            self.status_value.setStyleSheet("color:#00D4FF; font-weight:900; font-size:13px;")
        else:
            self.status_value.setText(self._t("idle"))
            self.status_value.setStyleSheet("color:#34D399; font-weight:900; font-size:13px;")

    # ----------------- dialogs hooks -----------------

    def open_add_song_dialog(self):
        dlg = AddSongDialog(self, t=self._tf)
        dlg.setStyleSheet(self.styleSheet())
        if dlg.exec() != QDialog.Accepted:
            return

        url = dlg.url()
        if not url:
            return

        fmt = self.format_box.currentText()
        self.add_queue_row(url=url, fmt=fmt, status_key="queued", pct=0)

    def open_add_playlist_dialog(self):
        dlg = AddPlaylistDialog(self, t=self._tf)
        dlg.setStyleSheet(self.styleSheet())
        if dlg.exec() != QDialog.Accepted:
            return

        data = dlg.data()
        url = data.get("url", "").strip()
        if not url:
            return

        fmt = self.format_box.currentText()

        if not data.get("expand", True):
            # Simple mode: add as a single item (later you can expand in worker)
            self.add_queue_row(url=url, fmt=fmt, status_key="queued", pct=0)
            return

        # Expand now (recommended)
        self.add_log(self._t("expanding_playlist"))
        try:
            urls = self.expand_playlist_to_urls(url, limit=data.get("limit", 200))
        except Exception as e:
            QMessageBox.warning(self, self._t("error"), str(e))
            return

        if not urls:
            QMessageBox.warning(self, self._t("error"), self._t("playlist_no_items"))
            return

        for u in urls:
            self.add_queue_row(url=u, fmt=fmt, status_key="queued", pct=0)

        self.add_log(self._tf("playlist_items_added", count=len(urls)))

    def open_paste_batch_dialog(self):
        dlg = PasteBatchDialog(self, t=self._tf)
        dlg.setStyleSheet(self.styleSheet())
        if dlg.exec() != QDialog.Accepted:
            return

        urls = dlg.urls()
        if not urls:
            return

        fmt = self.format_box.currentText()
        for u in urls:
            self.add_queue_row(url=u, fmt=fmt, status_key="queued", pct=0)

    # ----------------- playlist expansion -----------------

    def expand_playlist_to_urls(self, playlist_url: str, limit: int = 200) -> list[str]:
        """
        Expand a playlist URL into a list of watch URLs.
        Uses downloader.get_info() (yt-dlp metadata) and extracts entries.
        """
        info = self.downloader.get_info(playlist_url)

        entries = info.get("entries") if isinstance(info, dict) else None
        if not entries:
            # Some extractors return _type == 'playlist' without entries if flat extraction disabled
            # We'll just return empty so UI can show message.
            return []

        out = []
        for entry in entries:
            if not entry:
                continue
            webpage = entry.get("webpage_url") if isinstance(entry, dict) else None
            if webpage:
                out.append(webpage)
                continue
            # fallback: id -> watch URL
            eid = entry.get("id") if isinstance(entry, dict) else None
            if eid:
                out.append(f"https://www.youtube.com/watch?v={eid}")

            if len(out) >= int(limit):
                break

        # Deduplicate preserving order
        seen = set()
        deduped = []
        for u in out:
            if u not in seen:
                seen.add(u)
                deduped.append(u)
        return deduped

    # ----------------- download -----------------

    def start_download(self):
        queued = self.get_queued_rows()
        if not queued:
            QMessageBox.warning(self, self._t("no_urls_title"), self._t("no_queued_body"))
            return

        urls = [u for (_r, u, _f) in queued]
        # Si quieres soportar fmt por fila, cámbialo en el worker (por ahora usa global)
        fmt = self.format_box.currentText()
        q = self.quality_box.currentText()

        self.download_btn.setEnabled(False)
        self.download_btn.setText(self._t("downloading"))
        self.set_status("downloading")
        self.progress_bar.setValue(0)

        # Thread + worker
        self.thread = QThread()
        self.worker = DownloadWorker(self.downloader, urls, fmt, q)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.status_key.connect(self.set_status)
        self.worker.log_event.connect(self.on_log_event)
        self.worker.item_update.connect(self.on_item_update)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self.on_worker_finished)

        self.thread.start()

    def on_log_event(self, event: object):
        # event = {"key": "...", "args": {...}}
        key = event.get("key", "ready")
        args = event.get("args", {})
        self.add_log(self._tf(key, **args))
        if key == "now_downloading":
            self.now_label.setText(self._tf(key, **args))

    def on_worker_finished(self):
        self.download_btn.setEnabled(True)
        self.download_btn.setText(self._t("download"))
        self.set_status("idle")