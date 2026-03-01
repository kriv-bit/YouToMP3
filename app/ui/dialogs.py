# app/ui/dialogs.py
"""Reusable dialog windows for adding songs, playlists, and batch URLs."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QCheckBox, QSpinBox,
)


class AddSongDialog(QDialog):
    """Modal dialog to add a single song URL to the queue."""

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
    """Modal dialog to add a playlist URL with expand/limit options."""

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
    """Modal dialog to paste multiple URLs (one per line)."""

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
