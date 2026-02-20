# app/ui/window.py
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QLabel, QFileDialog, QComboBox, QProgressBar, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, QThread, QSettings
from PySide6.QtGui import QFont, QFontMetrics, QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect

from app.downloader import MediaDownloader
from app.ui.worker import DownloadWorker
from app.ui.i18n import TRANSLATIONS


def add_shadow(widget, color_hex="#00D4FF", blur=22, x=0, y=6, alpha=70):
    eff = QGraphicsDropShadowEffect()
    c = QColor(color_hex)
    c.setAlpha(alpha)
    eff.setColor(c)
    eff.setBlurRadius(blur)
    eff.setOffset(x, y)
    widget.setGraphicsEffect(eff)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Settings (persist language + folder)
        self.settings = QSettings("kriv-bit", "YouToMp3Pro")
        self.lang = self.settings.value("language", "en")

        self.output_folder = self.settings.value("output_folder", os.path.abspath("downloads"))
        self.downloader = MediaDownloader(output_path=self.output_folder)

        self.thread = None
        self.worker = None

        self.setWindowTitle(TRANSLATIONS[self.lang]["app_name"])
        self.setMinimumSize(1040, 680)

        app_font = QFont("Segoe UI", 10)
        self.setFont(app_font)

        self._i18n_bindings = []  # list of (widget, key, attr)

        self.build_ui()
        self.apply_style()
        self.apply_language(self.lang)

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
        self.settings.setValue("language", self.lang)
        self.setWindowTitle(self._t("app_name"))

        # Update all bound labels/buttons
        for w, key, attr in self._i18n_bindings:
            if attr == "text":
                w.setText(self._t(key))

        # Update dynamic fields
        self.status_value.setText(self._t("idle") if self.status_key == "idle" else self._t("downloading"))
        self.url_box.setPlaceholderText("https://youtu.be/VIDEO_ID\nhttps://youtu.be/ANOTHER_ID")
        self.lang_label.setText(self._t("language"))

        # Keep download button state text consistent
        if self.download_btn.isEnabled():
            self.download_btn.setText(self._t("download"))
        else:
            self.download_btn.setText(self._t("downloading"))

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
        self.format_box.addItems(["mp3", "mp4"])
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
        self.set_elided(self.folder_chip, self.output_folder)
        s.addWidget(self.folder_chip)

        self.folder_btn = QPushButton()
        self._bind_text(self.folder_btn, "select_folder")
        self.folder_btn.setObjectName("SecondaryButton")
        self.folder_btn.clicked.connect(self.select_folder)
        s.addWidget(self.folder_btn)

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
        self.lang_combo.currentIndexChanged.connect(self.on_lang_change)
        lang_box.addWidget(self.lang_combo)

        top.addLayout(lang_box)
        c.addLayout(top)

        # URL area
        self.url_box = QTextEdit()
        self.url_box.setObjectName("TextArea")
        c.addWidget(self.url_box, 2)

        # Actions row
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

        # Console
        self.console_label = QLabel()
        self._bind_text(self.console_label, "console")
        c.addWidget(self.console_label)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setObjectName("ConsoleArea")
        c.addWidget(self.log_box, 2)

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
        # Better contrast, less “neon cringe”, more “product”
        self.setStyleSheet("""
        QMainWindow {
            background: #0A0F16;
            color: #E6EDF3;
        }

        #Sidebar, #Content {
            background: #0E1622;
            border: 1px solid #1B2A3D;
            border-radius: 18px;
        }

        QLabel {
            color: #E6EDF3;
            font-size: 12px;
            letter-spacing: 0.2px;
        }

        #BrandTitle {
            font-size: 24px;
            font-weight: 800;
        }
        #BrandSub {
            color: #9AA4B2;
            margin-bottom: 8px;
        }

        #Divider {
            background: #1B2A3D;
            margin: 8px 0 14px 0;
        }

        #H1 {
            font-size: 18px;
            font-weight: 800;
        }
        #H2 {
            color: #9AA4B2;
        }

        #LangLabel { color: #9AA4B2; }
        #LangCombo {
            min-width: 140px;
        }

        QComboBox {
            background: #0B111A;
            border: 1px solid #1B2A3D;
            padding: 10px 12px;
            border-radius: 12px;
            color: #E6EDF3;
        }
        QComboBox:hover { border-color: #2B3E56; }
        QComboBox::drop-down {
            border: none;
            width: 26px;
        }
        QComboBox QAbstractItemView {
            background: #0B111A;
            border: 1px solid #1B2A3D;
            selection-background-color: #11324B;
            color: #E6EDF3;
            outline: 0;
        }

        #Chip {
            background: #0B111A;
            border: 1px solid #1B2A3D;
            padding: 10px 12px;
            border-radius: 12px;
            color: #9AA4B2;
        }

        #TextArea, #ConsoleArea {
            background: #070B12;
            border: 1px solid #1B2A3D;
            border-radius: 14px;
            padding: 12px;
            color: #E6EDF3;
            font-family: Consolas;
            font-size: 12px;
        }

        /* Scrollbar (makes it feel premium) */
        QScrollBar:vertical {
            background: #0B111A;
            width: 12px;
            margin: 2px;
            border-radius: 6px;
        }
        QScrollBar::handle:vertical {
            background: #1B2A3D;
            min-height: 24px;
            border-radius: 6px;
        }
        QScrollBar::handle:vertical:hover {
            background: #2B3E56;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }

        #Progress {
            background: #0B111A;
            border: 1px solid #1B2A3D;
            border-radius: 12px;
            height: 14px;
            text-align: center;
            color: #9AA4B2;
        }
        QProgressBar::chunk {
            border-radius: 12px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #00D4FF, stop:1 #A855F7
            );
        }

        #PrimaryButton {
            min-width: 170px;
            padding: 12px 16px;
            border-radius: 14px;
            color: #061018;
            font-weight: 900;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #FB7185, stop:1 #A855F7
            );
        }
        #PrimaryButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #FF8DA1, stop:1 #B784FF
            );
        }
        #PrimaryButton:disabled {
            background: #253347;
            color: #9AA4B2;
        }

        #SecondaryButton {
            padding: 12px 16px;
            border-radius: 14px;
            color: #041018;
            font-weight: 900;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #00D4FF, stop:1 #22C55E
            );
        }
        #SecondaryButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #34E7FF, stop:1 #34D399
            );
        }

        #Status {
            font-weight: 900;
            font-size: 13px;
            color: #34D399;
        }
        """)

    # ----------------- utils -----------------
    def set_elided(self, label: QLabel, text: str):
        fm = QFontMetrics(label.font())
        elided = fm.elidedText(text, Qt.ElideLeft, label.width() - 10 if label.width() > 10 else 240)
        label.setText(elided)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.set_elided(self.folder_chip, self.output_folder)

    # ----------------- actions -----------------
    def on_lang_change(self):
        lang = self.lang_combo.currentData()
        self.apply_language(lang)

    def add_log(self, text: str):
        self.log_box.append(text)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, self._t("select_folder"))
        if folder:
            self.output_folder = folder
            self.downloader.output_path = folder
            self.settings.setValue("output_folder", folder)
            self.set_elided(self.folder_chip, folder)
            self.add_log(self._tf("output_set", folder=folder))

    def set_status(self, key: str):
        self.status_key = key
        if key == "downloading":
            self.status_value.setText(self._t("downloading"))
            self.status_value.setStyleSheet("color:#00D4FF; font-weight:900; font-size:13px;")
        else:
            self.status_value.setText(self._t("idle"))
            self.status_value.setStyleSheet("color:#34D399; font-weight:900; font-size:13px;")

    def start_download(self):
        urls = [u.strip() for u in self.url_box.toPlainText().splitlines() if u.strip()]
        if not urls:
            QMessageBox.warning(self, self._t("no_urls_title"), self._t("no_urls_body"))
            return

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

    def on_worker_finished(self):
        self.download_btn.setEnabled(True)
        self.download_btn.setText(self._t("download"))
        self.set_status("idle")