# app/ui/now_downloading.py
"""Now Downloading card — shows metadata of the item currently being downloaded."""

from __future__ import annotations

from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtGui import QPixmap, QFont, QPainter, QLinearGradient, QColor
from PySide6.QtCore import Qt, QSize
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from typing import Callable


class NowDownloadingCard(QFrame):
    """Displays cover art, title, artist, duration, and URL of the current download."""

    COVER_SIZE = 90

    def __init__(self, t_fn: Callable[[str], str], parent=None):
        super().__init__(parent)
        self.setObjectName("NowDownloadingCard")
        self._t = t_fn
        self._nam = QNetworkAccessManager(self)
        self._nam.finished.connect(self._on_thumb_loaded)

        self._build()
        self.clear()

    # ---- public API ----

    def set_t(self, t_fn: Callable[[str], str]):
        """Update translation function on language change."""
        self._t = t_fn
        self._section_label.setText(self._t("now_downloading_title"))
        if not self._has_item:
            self._placeholder.setText(self._t("nd_no_item"))

    def update_meta(
        self,
        title: str = "",
        uploader: str = "",
        duration: int | None = None,
        thumbnail: str = "",
        url: str = "",
        index: int = 0,
        total: int = 0,
    ):
        """Update the card with metadata from the current download item."""
        self._has_item = True
        self._placeholder.hide()
        self._info_frame.show()

        self._lbl_title.setText(title or self._t("nd_unknown"))
        self._lbl_artist.setText(uploader or self._t("nd_unknown"))

        if duration and isinstance(duration, (int, float)) and duration > 0:
            m, s = divmod(int(duration), 60)
            self._lbl_duration.setText(f"{m}:{s:02d}")
            self._lbl_duration.show()
        else:
            self._lbl_duration.hide()

        self._lbl_url.setText(url or "")
        self._lbl_url.setToolTip(url or "")

        if index and total:
            self._lbl_badge.setText(self._t("nd_playlist_of").format(index=index, total=total))
            self._lbl_badge.show()
        else:
            self._lbl_badge.hide()

        # Load thumbnail async
        if thumbnail:
            req = QNetworkRequest(thumbnail)
            self._nam.get(req)
        else:
            self._set_placeholder_cover()

    def clear(self):
        """Reset card to idle state."""
        self._has_item = False
        self._info_frame.hide()
        self._placeholder.setText(self._t("nd_no_item"))
        self._placeholder.show()
        self._set_placeholder_cover()

    # ---- internal ----

    def _build(self):
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(8)

        self._section_label = QLabel(self._t("now_downloading_title"))
        self._section_label.setObjectName("NDCardLabel")
        main_lay.addWidget(self._section_label)

        body = QHBoxLayout()
        body.setSpacing(14)

        # Cover art
        self._cover = QLabel()
        self._cover.setFixedSize(self.COVER_SIZE, self.COVER_SIZE)
        self._cover.setObjectName("NDCoverPlaceholder")
        self._cover.setAlignment(Qt.AlignCenter)
        self._cover.setScaledContents(True)
        body.addWidget(self._cover)

        # Info column
        self._info_frame = QFrame()
        info_lay = QVBoxLayout(self._info_frame)
        info_lay.setContentsMargins(0, 2, 0, 2)
        info_lay.setSpacing(3)

        self._lbl_title = QLabel()
        self._lbl_title.setObjectName("NDTitle")
        self._lbl_title.setWordWrap(True)
        info_lay.addWidget(self._lbl_title)

        self._lbl_artist = QLabel()
        self._lbl_artist.setObjectName("NDArtist")
        info_lay.addWidget(self._lbl_artist)

        self._lbl_duration = QLabel()
        self._lbl_duration.setObjectName("NDDuration")
        info_lay.addWidget(self._lbl_duration)

        self._lbl_url = QLabel()
        self._lbl_url.setObjectName("NDURL")
        self._lbl_url.setWordWrap(False)
        info_lay.addWidget(self._lbl_url)

        self._lbl_badge = QLabel()
        self._lbl_badge.setObjectName("NDBadge")
        info_lay.addWidget(self._lbl_badge)

        info_lay.addStretch(1)

        body.addWidget(self._info_frame, 1)
        main_lay.addLayout(body)

        # Placeholder for idle state
        self._placeholder = QLabel(self._t("nd_no_item"))
        self._placeholder.setObjectName("NDPlaceholder")
        self._placeholder.setAlignment(Qt.AlignCenter)
        main_lay.addWidget(self._placeholder)

    def _set_placeholder_cover(self):
        """Draw a gradient placeholder for the cover area."""
        px = QPixmap(self.COVER_SIZE, self.COVER_SIZE)
        px.fill(QColor(0, 0, 0, 0))
        p = QPainter(px)
        grad = QLinearGradient(0, 0, self.COVER_SIZE, self.COVER_SIZE)
        grad.setColorAt(0.0, QColor("#11243A"))
        grad.setColorAt(1.0, QColor("#1A1030"))
        p.setBrush(grad)
        p.setPen(QColor("#1B2A3D"))
        p.drawRoundedRect(0, 0, self.COVER_SIZE, self.COVER_SIZE, 10, 10)
        # Music note icon
        p.setPen(QColor("#2A3E56"))
        f = QFont("Segoe UI", 28)
        p.setFont(f)
        p.drawText(px.rect(), Qt.AlignCenter, "♪")
        p.end()
        self._cover.setPixmap(px)

    def _on_thumb_loaded(self, reply: QNetworkReply):
        """Handle async thumbnail download."""
        if reply.error() != QNetworkReply.NoError:
            self._set_placeholder_cover()
            reply.deleteLater()
            return

        data = reply.readAll()
        px = QPixmap()
        if px.loadFromData(data):
            scaled = px.scaled(
                QSize(self.COVER_SIZE, self.COVER_SIZE),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation,
            )
            # Crop center
            if scaled.width() > self.COVER_SIZE or scaled.height() > self.COVER_SIZE:
                x = (scaled.width() - self.COVER_SIZE) // 2
                y = (scaled.height() - self.COVER_SIZE) // 2
                scaled = scaled.copy(x, y, self.COVER_SIZE, self.COVER_SIZE)
            self._cover.setPixmap(scaled)
        else:
            self._set_placeholder_cover()

        reply.deleteLater()
