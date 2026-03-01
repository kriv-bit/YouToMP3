# app/ui/window.py
"""Main window — thin shell: construction, layout, i18n binding, and wiring."""

import os

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QLabel, QComboBox, QProgressBar, QFrame,
    QTableWidget, QHeaderView, QAbstractItemView, QSplitter,
)
from PySide6.QtGui import QFont, QIcon, Qt

from app.downloader import MediaDownloader
from app.ui.i18n import TRANSLATIONS
from app.ui.widgets import add_shadow, set_elided
from app.ui.style import main_qss
from app.ui.settings import AppSettings
from app.ui.queue_manager import QueueManager
from app.ui.controller import MainController
from app.ui.now_downloading import NowDownloadingCard


class MainWindow(QMainWindow):
    """Top-level application window.

    Layout (content area):
    - Top bar: H1/H2 + language toggle
    - Progress bar + Download button
    - Two-column body:
      - Left: action buttons + Now Downloading card + console
      - Right: queue table (priority space)
    """

    # ---- lifecycle ----

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
        self.setMinimumSize(1120, 720)

        app_font = QFont("Segoe UI Variable", 10)
        if not app_font.exactMatch():
            app_font = QFont("Segoe UI", 10)
        self.setFont(app_font)

        self._i18n_bindings = []  # list of (widget, key, attr)

        self.build_ui()
        self.apply_style()

        # Controller & queue manager (created after build_ui so widgets exist)
        self.queue = QueueManager(self.queue_table, t_fn=self._t)
        self.ctrl = MainController(self)

        self.apply_language(self.lang)
        self.settings.restore_geometry(self)
        self.queue.load(self._settings_get)

        self.add_log(self._t("ready"))

    def closeEvent(self, event):
        self.queue.save(self._settings_set)
        self.settings.save_geometry(self)
        super().closeEvent(event)

    # ---- i18n helpers ----

    def _t(self, key: str) -> str:
        """Translate *key* using the current language."""
        return TRANSLATIONS.get(self.lang, TRANSLATIONS["en"]).get(key, key)

    def _tf(self, key: str, **kwargs) -> str:
        """Translate *key* and format with *kwargs*."""
        template = self._t(key)
        try:
            return template.format(**kwargs)
        except Exception:
            return template

    def _bind_text(self, widget, key: str):
        """Register a widget for automatic text update on language change."""
        self._i18n_bindings.append((widget, key, "text"))

    def apply_language(self, lang: str):
        """Switch UI language and refresh all bound widgets."""
        self.lang = "es" if lang == "es" else "en"
        self.settings.set_language(self.lang)
        self.setWindowTitle(self._t("app_name"))

        # Update all bound labels/buttons
        for w, key, attr in self._i18n_bindings:
            if attr == "text":
                w.setText(self._t(key))

        # Update queue manager translation
        self.queue.set_t(self._t)
        self.queue.refresh_headers()

        # Update now downloading card translation
        self.now_card.set_t(self._t)

        # Update dynamic fields
        self.status_value.setText(self._t("idle") if self.status_key == "idle" else self._t("downloading"))
        self.lang_label.setText(self._t("language"))

        if self.download_btn.isEnabled():
            self.download_btn.setText(self._t("download"))
        else:
            self.download_btn.setText(self._t("downloading"))

    # ---- settings convenience ----

    def _settings_get(self, key: str, default=None):
        s = getattr(self.settings, "qs", self.settings)
        return s.value(key, default)

    def _settings_set(self, key: str, value):
        s = getattr(self.settings, "qs", self.settings)
        s.setValue(key, value)

    # ---- UI construction ----

    def build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)

        main = QHBoxLayout(root)
        main.setContentsMargins(18, 18, 18, 18)
        main.setSpacing(14)

        self._build_sidebar()
        self._build_content()

        main.addWidget(self.sidebar)
        main.addWidget(self.content, 1)

        # Shadows
        add_shadow(self.sidebar, color_hex="#0EA5E9", blur=28, x=0, y=10, alpha=35)
        add_shadow(self.content, color_hex="#A855F7", blur=28, x=0, y=10, alpha=25)
        add_shadow(self.download_btn, color_hex="#FB7185", blur=30, x=0, y=10, alpha=45)

        # Load lang selection into combo
        idx = 0 if self.lang == "en" else 1
        self.lang_combo.setCurrentIndex(idx)

    # ---- sidebar ----

    def _build_sidebar(self):
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
        self.folder_btn.clicked.connect(lambda: self.ctrl.select_folder())
        s.addWidget(self.folder_btn)

        self.open_folder_btn = QPushButton()
        self._bind_text(self.open_folder_btn, "open_output_folder")
        self.open_folder_btn.setObjectName("SecondaryButton")
        self.open_folder_btn.clicked.connect(lambda: self.ctrl.open_output_folder())
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

    # ---- content panel ----

    def _build_content(self):
        self.content = QFrame()
        self.content.setObjectName("Content")
        c = QVBoxLayout(self.content)
        c.setSpacing(12)
        c.setContentsMargins(18, 16, 18, 16)

        # ── Top bar (title + language toggle) ──
        top = QHBoxLayout()
        left = QVBoxLayout()
        left.setSpacing(2)

        self.h1 = QLabel()
        self.h1.setObjectName("H1")
        self._bind_text(self.h1, "paste_urls")

        self.h2 = QLabel()
        self.h2.setObjectName("H2")
        self._bind_text(self.h2, "one_per_line")

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
        self.lang_combo.currentIndexChanged.connect(self._on_lang_change)
        lang_box.addWidget(self.lang_combo)

        top.addLayout(lang_box)
        c.addLayout(top)

        # ── Progress bar + Download button ──
        actions = QHBoxLayout()
        actions.setSpacing(12)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setObjectName("Progress")
        actions.addWidget(self.progress_bar, 1)

        self.download_btn = QPushButton()
        self.download_btn.setObjectName("PrimaryButton")
        self.download_btn.clicked.connect(lambda: self.ctrl.start_download())
        actions.addWidget(self.download_btn)

        c.addLayout(actions)

        self.now_label = QLabel("")
        self.now_label.setObjectName("NowLabel")
        c.addWidget(self.now_label)

        # ══ Two-column body ══
        body_splitter = QSplitter(Qt.Horizontal)
        body_splitter.setChildrenCollapsible(False)

        # ── LEFT COLUMN: action buttons + card + console ──
        left_panel = QFrame()
        left_lay = QVBoxLayout(left_panel)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(10)

        # Action buttons
        action_row = QHBoxLayout()
        action_row.setSpacing(8)

        self.btn_add_song = QPushButton()
        self._bind_text(self.btn_add_song, "add_song")
        self.btn_add_song.setObjectName("SecondaryButton")
        self.btn_add_song.clicked.connect(lambda: self.ctrl.open_add_song_dialog())

        self.btn_add_playlist = QPushButton()
        self._bind_text(self.btn_add_playlist, "add_playlist")
        self.btn_add_playlist.setObjectName("SecondaryButton")
        self.btn_add_playlist.clicked.connect(lambda: self.ctrl.open_add_playlist_dialog())

        self.btn_paste_batch = QPushButton()
        self._bind_text(self.btn_paste_batch, "paste_batch")
        self.btn_paste_batch.setObjectName("SecondaryButton")
        self.btn_paste_batch.clicked.connect(lambda: self.ctrl.open_paste_batch_dialog())

        action_row.addWidget(self.btn_add_song)
        action_row.addWidget(self.btn_add_playlist)
        action_row.addWidget(self.btn_paste_batch)
        left_lay.addLayout(action_row)

        # Now Downloading card
        self.now_card = NowDownloadingCard(t_fn=self._t, parent=self)
        left_lay.addWidget(self.now_card)

        # Console log
        console_label = QLabel()
        console_label.setObjectName("SectionLabel")
        self._bind_text(console_label, "console")
        left_lay.addWidget(console_label)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setObjectName("ConsoleArea")
        left_lay.addWidget(self.log_box, 1)

        body_splitter.addWidget(left_panel)

        # ── RIGHT COLUMN: queue table ──
        right_panel = QFrame()
        right_lay = QVBoxLayout(right_panel)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(6)

        queue_bar = QHBoxLayout()
        self.queue_label = QLabel()
        self.queue_label.setObjectName("SectionLabel")
        self._bind_text(self.queue_label, "queue")
        queue_bar.addWidget(self.queue_label)
        queue_bar.addStretch(2)

        self.expand_queue_btn = QPushButton(self._t("expand_table"))
        self.expand_queue_btn.setObjectName("SecondaryButton")
        self.expand_queue_btn.clicked.connect(lambda: self.queue.open_modal(self))
        queue_bar.addWidget(self.expand_queue_btn)

        right_lay.addLayout(queue_bar)

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
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)           # title
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)           # url
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # format
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # status
        hdr.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # progress
        hdr.setSectionResizeMode(5, QHeaderView.Stretch)           # output

        self.queue_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.queue_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.queue_table.setAlternatingRowColors(True)
        self.queue_table.verticalHeader().setVisible(False)
        self.queue_table.setShowGrid(False)

        right_lay.addWidget(self.queue_table, 1)

        body_splitter.addWidget(right_panel)

        # Give right column (table) more space: ~40% left, ~60% right
        body_splitter.setSizes([380, 560])
        body_splitter.setStretchFactor(0, 2)
        body_splitter.setStretchFactor(1, 3)

        c.addWidget(body_splitter, 1)

    # ---- style ----

    def apply_style(self):
        self.setStyleSheet(main_qss())

    # ---- small utilities ----

    def resizeEvent(self, event):
        super().resizeEvent(event)
        set_elided(self.folder_chip, self.output_folder)

    def _on_lang_change(self):
        lang = self.lang_combo.currentData()
        self.apply_language(lang)

    def add_log(self, text: str):
        """Append a line to the console area."""
        self.log_box.append(text)