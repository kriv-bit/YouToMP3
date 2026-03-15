# app/ui/dialogs.py
"""Reusable dialog windows for adding songs, playlists, and batch URLs."""

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class _BaseDialog(QDialog):
    """Shared dialog scaffold with header, body, and action row."""

    def __init__(self, parent=None, t=lambda k, **kw: k):
        super().__init__(parent)
        self.setObjectName("AppDialog")
        self.t = t

    def _build_shell(self, title: str, subtitle: str) -> QVBoxLayout:
        root = QVBoxLayout(self)
        root.setSpacing(16)
        root.setContentsMargins(24, 22, 24, 22)

        self.header_panel = QWidget()
        self.header_panel.setObjectName("DialogHeader")
        header_layout = QVBoxLayout(self.header_panel)
        header_layout.setContentsMargins(0, 0, 0, 12)
        header_layout.setSpacing(4)

        self.header_title = QLabel(title)
        self.header_title.setObjectName("DialogTitle")
        header_layout.addWidget(self.header_title)

        self.header_subtitle = QLabel(subtitle)
        self.header_subtitle.setObjectName("DialogSubtitle")
        self.header_subtitle.setWordWrap(True)
        header_layout.addWidget(self.header_subtitle)

        root.addWidget(self.header_panel)

        self.body_panel = QWidget()
        self.body_panel.setObjectName("DialogBody")
        body_layout = QVBoxLayout(self.body_panel)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(12)
        root.addWidget(self.body_panel, 1)

        button_row = QHBoxLayout()
        button_row.setSpacing(10)
        button_row.addStretch(1)

        self.btn_cancel = QPushButton(self.t("cancel"))
        self.btn_cancel.setObjectName("SecondaryButton")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_add = QPushButton(self.t("add"))
        self.btn_add.setObjectName("PrimaryButton")
        self.btn_add.clicked.connect(self.accept)

        button_row.addWidget(self.btn_cancel)
        button_row.addWidget(self.btn_add)
        root.addLayout(button_row)

        return body_layout


class AddSongDialog(_BaseDialog):
    """Modal dialog to add a single song URL to the queue."""

    def __init__(self, parent=None, t=lambda k, **kw: k):
        super().__init__(parent, t=t)
        self.setWindowTitle(self.t("add_song"))
        self.resize(560, 220)

        lay = self._build_shell(self.t("add_song"), self.t("enter_url"))

        lbl = QLabel(self.t("song_url"))
        lbl.setObjectName("FormLabel")
        lay.addWidget(lbl)

        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText(self.t("enter_url"))
        lay.addWidget(self.url_edit)

    def url(self) -> str:
        return self.url_edit.text().strip()


class AddPlaylistDialog(_BaseDialog):
    """Modal dialog to add a playlist URL with expand/limit options."""

    def __init__(self, parent=None, t=lambda k, **kw: k):
        super().__init__(parent, t=t)
        self.setWindowTitle(self.t("add_playlist"))
        self.resize(640, 340)

        lay = self._build_shell(self.t("add_playlist"), self.t("enter_playlist_url"))

        lbl = QLabel(self.t("playlist_url"))
        lbl.setObjectName("FormLabel")
        lay.addWidget(lbl)

        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText(self.t("enter_playlist_url"))
        lay.addWidget(self.url_edit)

        options_panel = QWidget()
        options_panel.setObjectName("FormPanel")
        options_layout = QVBoxLayout(options_panel)
        options_layout.setContentsMargins(14, 14, 14, 14)
        options_layout.setSpacing(12)

        self.chk_expand = QCheckBox(self.t("expand_now"))
        self.chk_expand.setChecked(True)
        options_layout.addWidget(self.chk_expand)

        limit_lbl = QLabel(self.t("max_items"))
        limit_lbl.setObjectName("FormLabel")
        options_layout.addWidget(limit_lbl)

        self.spin_limit = QSpinBox()
        self.spin_limit.setRange(1, 5000)
        self.spin_limit.setValue(200)
        options_layout.addWidget(self.spin_limit)

        lay.addWidget(options_panel)

    def data(self) -> dict:
        return {
            "url": self.url_edit.text().strip(),
            "expand": self.chk_expand.isChecked(),
            "limit": int(self.spin_limit.value()),
        }


class PasteBatchDialog(_BaseDialog):
    """Modal dialog to paste multiple URLs (one per line)."""

    def __init__(self, parent=None, t=lambda k, **kw: k):
        super().__init__(parent, t=t)
        self.setWindowTitle(self.t("paste_batch"))
        self.resize(820, 500)

        lay = self._build_shell(self.t("paste_batch"), self.t("one_per_line"))

        self.text = QTextEdit()
        self.text.setObjectName("TextArea")
        self.text.setPlaceholderText("https://youtu.be/VIDEO_ID\nhttps://youtu.be/ANOTHER_ID")
        lay.addWidget(self.text, 1)

    def urls(self) -> list[str]:
        return [u.strip() for u in self.text.toPlainText().splitlines() if u.strip()]
