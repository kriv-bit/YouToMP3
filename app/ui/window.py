# app/ui/window.py
"""Main window: construction, layout, i18n binding, and wiring."""

import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.downloader import MediaDownloader
from app.ui.controller import MainController
from app.ui.i18n import TRANSLATIONS
from app.ui.now_downloading import NowDownloadingCard
from app.ui.queue_manager import QueueManager
from app.ui.settings import AppSettings
from app.ui.style import main_qss
from app.ui.widgets import add_shadow, set_elided


class MainWindow(QMainWindow):
    """Top-level application window."""

    def __init__(self):
        super().__init__()

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

        self._i18n_bindings = []

        self.build_ui()
        self.apply_style()

        self.queue = QueueManager(self.queue_table, t_fn=self._t)
        self.ctrl = MainController(self)

        self.apply_language(self.lang)
        self.settings.restore_geometry(self)
        self.queue.load(self._settings_get)

        self.add_log(self._t("ready"))

    def closeEvent(self, event):
        if hasattr(self, "queue"):
            self.queue.save(self._settings_set)
        self.settings.save_geometry(self)
        super().closeEvent(event)

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

        for widget, key, attr in self._i18n_bindings:
            if attr == "text":
                widget.setText(self._t(key))

        self.lang_label.setText(self._t("language"))
        self.status_value.setText(self._t("idle") if self.status_key == "idle" else self._t("downloading"))

        if self.download_btn.isEnabled():
            self.download_btn.setText(self._t("download"))
        else:
            self.download_btn.setText(self._t("downloading"))

        if hasattr(self, "queue"):
            self.queue.set_t(self._t)
            self.queue.refresh_headers()

        if hasattr(self, "now_card"):
            self.now_card.set_t(self._t)

        if hasattr(self, "expand_queue_btn"):
            self.expand_queue_btn.setText(self._t("expand_table"))
        if hasattr(self, "clear_queue_btn"):
            self.clear_queue_btn.setText(self._t("clear_queue"))

    def _settings_get(self, key: str, default=None):
        s = getattr(self.settings, "qs", self.settings)
        return s.value(key, default)

    def _settings_set(self, key: str, value):
        s = getattr(self.settings, "qs", self.settings)
        s.setValue(key, value)

    def build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)

        main = QHBoxLayout(root)
        main.setContentsMargins(20, 20, 20, 20)
        main.setSpacing(16)

        self._build_sidebar()
        self._build_content()

        main.addWidget(self.sidebar)
        main.addWidget(self.content, 1)

        add_shadow(self.sidebar, color_hex="#000000", blur=20, x=0, y=8, alpha=50)
        add_shadow(self.content, color_hex="#000000", blur=22, x=0, y=8, alpha=35)

        idx = 0 if self.lang == "en" else 1
        self.lang_combo.blockSignals(True)
        self.lang_combo.setCurrentIndex(idx)
        self.lang_combo.blockSignals(False)

    def _build_sidebar(self):
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(292)

        layout = QVBoxLayout(self.sidebar)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        self.brand = QLabel("YouToMp3")
        self.brand.setObjectName("BrandTitle")
        self.brand_sub = QLabel("Desktop media downloader")
        self.brand_sub.setObjectName("BrandSub")
        self.brand_sub.setWordWrap(True)
        layout.addWidget(self.brand)
        layout.addWidget(self.brand_sub)

        divider = QFrame()
        divider.setObjectName("Divider")
        divider.setFixedHeight(1)
        layout.addWidget(divider)

        format_group = self._make_sidebar_group()
        format_layout = format_group.layout()

        self.lbl_format = QLabel()
        self.lbl_format.setObjectName("SidebarLabel")
        self._bind_text(self.lbl_format, "format")
        format_layout.addWidget(self.lbl_format)

        self.format_box = QComboBox()
        self.format_box.addItems(["mp3", "wav", "m4a"])
        format_layout.addWidget(self.format_box)

        self.lbl_quality = QLabel()
        self.lbl_quality.setObjectName("SidebarLabel")
        self._bind_text(self.lbl_quality, "quality")
        format_layout.addWidget(self.lbl_quality)

        self.quality_box = QComboBox()
        self.quality_box.addItems(["320", "192", "128"])
        self.quality_box.setCurrentText("192")
        format_layout.addWidget(self.quality_box)
        layout.addWidget(format_group)

        output_group = self._make_sidebar_group()
        output_layout = output_group.layout()

        self.lbl_output = QLabel()
        self.lbl_output.setObjectName("SidebarLabel")
        self._bind_text(self.lbl_output, "output")
        output_layout.addWidget(self.lbl_output)

        self.folder_chip = QLabel(self.output_folder)
        self.folder_chip.setObjectName("Chip")
        self.folder_chip.setWordWrap(False)
        set_elided(self.folder_chip, self.output_folder)
        output_layout.addWidget(self.folder_chip)

        self.folder_btn = QPushButton()
        self._bind_text(self.folder_btn, "select_folder")
        self.folder_btn.setObjectName("SecondaryButton")
        self.folder_btn.clicked.connect(lambda: self.ctrl.select_folder())
        output_layout.addWidget(self.folder_btn)

        self.open_folder_btn = QPushButton()
        self._bind_text(self.open_folder_btn, "open_output_folder")
        self.open_folder_btn.setObjectName("SecondaryButton")
        self.open_folder_btn.clicked.connect(lambda: self.ctrl.open_output_folder())
        output_layout.addWidget(self.open_folder_btn)
        layout.addWidget(output_group)

        status_group = self._make_sidebar_group()
        status_layout = status_group.layout()

        self.lbl_status = QLabel()
        self.lbl_status.setObjectName("SidebarLabel")
        self._bind_text(self.lbl_status, "status")
        status_layout.addWidget(self.lbl_status)

        self.status_key = "idle"
        self.status_value = QLabel()
        self.status_value.setObjectName("Status")
        self.status_value.setProperty("state", "idle")
        status_layout.addWidget(self.status_value)
        layout.addWidget(status_group)

        layout.addStretch(1)

    def _build_content(self):
        self.content = QFrame()
        self.content.setObjectName("Content")

        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(18, 18, 18, 18)
        content_layout.setSpacing(14)

        header_panel = QFrame()
        header_panel.setObjectName("HeaderPanel")
        header_layout = QVBoxLayout(header_panel)
        header_layout.setContentsMargins(16, 16, 16, 16)
        header_layout.setSpacing(12)

        top = QHBoxLayout()
        top.setSpacing(12)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)

        self.h1 = QLabel()
        self.h1.setObjectName("H1")
        self._bind_text(self.h1, "paste_urls")
        title_col.addWidget(self.h1)

        self.h2 = QLabel()
        self.h2.setObjectName("H2")
        self._bind_text(self.h2, "one_per_line")
        title_col.addWidget(self.h2)

        top.addLayout(title_col, 1)

        lang_box = QHBoxLayout()
        lang_box.setSpacing(8)

        self.lang_label = QLabel()
        self.lang_label.setObjectName("LangLabel")
        lang_box.addWidget(self.lang_label)

        self.lang_combo = QComboBox()
        self.lang_combo.addItem("English", "en")
        self.lang_combo.addItem("Espanol", "es")
        self.lang_combo.setObjectName("LangCombo")
        self.lang_combo.currentIndexChanged.connect(self._on_lang_change)
        lang_box.addWidget(self.lang_combo)

        top.addLayout(lang_box)
        header_layout.addLayout(top)

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

        header_layout.addLayout(actions)
        content_layout.addWidget(header_panel)

        self.now_label = QLabel("")
        self.now_label.setObjectName("NowLabel")
        content_layout.addWidget(self.now_label)

        body_splitter = QSplitter(Qt.Horizontal)
        body_splitter.setChildrenCollapsible(False)
        body_splitter.setHandleWidth(8)

        left_panel = QFrame()
        left_panel.setObjectName("Panel")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.setSpacing(12)

        action_row = QHBoxLayout()
        action_row.setSpacing(8)

        self.btn_add_song = QPushButton()
        self._bind_text(self.btn_add_song, "add_song")
        self.btn_add_song.setObjectName("SecondaryButton")
        self.btn_add_song.clicked.connect(lambda: self.ctrl.open_add_song_dialog())
        action_row.addWidget(self.btn_add_song)

        self.btn_add_playlist = QPushButton()
        self._bind_text(self.btn_add_playlist, "add_playlist")
        self.btn_add_playlist.setObjectName("SecondaryButton")
        self.btn_add_playlist.clicked.connect(lambda: self.ctrl.open_add_playlist_dialog())
        action_row.addWidget(self.btn_add_playlist)

        self.btn_paste_batch = QPushButton()
        self._bind_text(self.btn_paste_batch, "paste_batch")
        self.btn_paste_batch.setObjectName("SecondaryButton")
        self.btn_paste_batch.clicked.connect(lambda: self.ctrl.open_paste_batch_dialog())
        action_row.addWidget(self.btn_paste_batch)

        left_layout.addLayout(action_row)

        self.now_card = NowDownloadingCard(t_fn=self._t, parent=self)
        left_layout.addWidget(self.now_card)

        console_panel = QFrame()
        console_panel.setObjectName("SubPanel")
        console_layout = QVBoxLayout(console_panel)
        console_layout.setContentsMargins(14, 14, 14, 14)
        console_layout.setSpacing(8)

        console_label = QLabel()
        console_label.setObjectName("SectionLabel")
        self._bind_text(console_label, "console")
        console_layout.addWidget(console_label)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setObjectName("ConsoleArea")
        console_layout.addWidget(self.log_box, 1)

        left_layout.addWidget(console_panel, 1)
        body_splitter.addWidget(left_panel)

        right_panel = QFrame()
        right_panel.setObjectName("Panel")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(10)

        queue_bar = QHBoxLayout()
        queue_bar.setSpacing(8)

        self.queue_title = QLabel()
        self.queue_title.setObjectName("SectionLabel")
        self._bind_text(self.queue_title, "downloads_queue")
        queue_bar.addWidget(self.queue_title)
        queue_bar.addStretch(1)

        self.clear_queue_btn = QPushButton()
        self._bind_text(self.clear_queue_btn, "clear_queue")
        self.clear_queue_btn.setObjectName("SecondaryButton")
        self.clear_queue_btn.clicked.connect(self._on_clear_queue_clicked)
        queue_bar.addWidget(self.clear_queue_btn)

        self.expand_queue_btn = QPushButton()
        self._bind_text(self.expand_queue_btn, "expand_table")
        self.expand_queue_btn.setObjectName("SecondaryButton")
        self.expand_queue_btn.clicked.connect(lambda: self.queue.open_modal(self))
        queue_bar.addWidget(self.expand_queue_btn)

        right_layout.addLayout(queue_bar)

        self.queue_table = QTableWidget(0, 7)
        self.queue_table.setObjectName("QueueTable")
        self.queue_table.setHorizontalHeaderLabels([
            self._t("col_title"),
            self._t("col_url"),
            self._t("col_format"),
            self._t("col_status"),
            self._t("col_progress"),
            self._t("col_output"),
            "",
        ])
        self.queue_table.verticalHeader().setDefaultSectionSize(80)

        header = self.queue_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        header.setSectionResizeMode(6, QHeaderView.Fixed)
        self.queue_table.setColumnWidth(6, 36)

        self.queue_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.queue_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.queue_table.setAlternatingRowColors(True)
        self.queue_table.verticalHeader().setVisible(False)
        self.queue_table.setShowGrid(False)
        right_layout.addWidget(self.queue_table, 1)

        body_splitter.addWidget(right_panel)
        body_splitter.setSizes([380, 620])
        body_splitter.setStretchFactor(0, 2)
        body_splitter.setStretchFactor(1, 3)

        content_layout.addWidget(body_splitter, 1)

    def _make_sidebar_group(self):
        group = QFrame()
        group.setObjectName("SidebarGroup")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        return group

    def _on_clear_queue_clicked(self):
        if not hasattr(self, "queue"):
            return
        self.queue.clear(settings_set_fn=self._settings_set, parent=self, confirm=True)

    def apply_style(self):
        self.setStyleSheet(main_qss())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        set_elided(self.folder_chip, self.output_folder)

    def _on_lang_change(self):
        if not hasattr(self, "queue"):
            lang = self.lang_combo.currentData()
            self.lang = "es" if lang == "es" else "en"
            return
        self.apply_language(self.lang_combo.currentData())

    def add_log(self, text: str):
        self.log_box.append(text)
