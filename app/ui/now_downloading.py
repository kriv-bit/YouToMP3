# app/ui/now_downloading.py
"""Now Downloading card: metadata summary for the active item."""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QSize, Qt, QUrl
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout


class NowDownloadingCard(QFrame):
    """Displays cover art, title, artist, duration, and URL of the current download."""

    COVER_SIZE = 92

    def __init__(self, t_fn: Callable[[str], str], parent=None):
        super().__init__(parent)
        self.setObjectName("NowDownloadingCard")
        self._t = t_fn
        self._nam = QNetworkAccessManager(self)
        self._nam.finished.connect(self._on_thumb_loaded)

        self._build()
        self.clear()

    def set_t(self, t_fn: Callable[[str], str]):
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
        self._has_item = True
        self._live_tag.show()
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

        if thumbnail:
            self._nam.get(QNetworkRequest(QUrl(thumbnail)))
        else:
            self._set_placeholder_cover()

    def clear(self):
        self._has_item = False
        self._live_tag.hide()
        self._info_frame.hide()
        self._placeholder.setText(self._t("nd_no_item"))
        self._placeholder.show()
        self._set_placeholder_cover()

    def _build(self):
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(14, 14, 14, 14)
        main_lay.setSpacing(12)

        header = QHBoxLayout()
        header.setSpacing(8)

        self._section_label = QLabel(self._t("now_downloading_title"))
        self._section_label.setObjectName("NDCardLabel")
        header.addWidget(self._section_label)
        header.addStretch(1)

        self._live_tag = QLabel("LIVE")
        self._live_tag.setObjectName("NDLiveTag")
        header.addWidget(self._live_tag)
        main_lay.addLayout(header)

        body = QHBoxLayout()
        body.setSpacing(14)

        self._cover = QLabel()
        self._cover.setFixedSize(self.COVER_SIZE, self.COVER_SIZE)
        self._cover.setObjectName("NDCoverPlaceholder")
        self._cover.setAlignment(Qt.AlignCenter)
        self._cover.setScaledContents(True)
        body.addWidget(self._cover)

        self._info_frame = QFrame()
        self._info_frame.setObjectName("NDInfoFrame")
        info_lay = QVBoxLayout(self._info_frame)
        info_lay.setContentsMargins(0, 0, 0, 0)
        info_lay.setSpacing(4)

        self._lbl_title = QLabel()
        self._lbl_title.setObjectName("NDTitle")
        self._lbl_title.setWordWrap(True)
        info_lay.addWidget(self._lbl_title)

        self._lbl_artist = QLabel()
        self._lbl_artist.setObjectName("NDArtist")
        self._lbl_artist.setWordWrap(True)
        info_lay.addWidget(self._lbl_artist)

        meta_row = QHBoxLayout()
        meta_row.setSpacing(8)

        self._lbl_duration = QLabel()
        self._lbl_duration.setObjectName("NDDuration")
        meta_row.addWidget(self._lbl_duration)

        self._lbl_badge = QLabel()
        self._lbl_badge.setObjectName("NDBadge")
        meta_row.addWidget(self._lbl_badge)
        meta_row.addStretch(1)
        info_lay.addLayout(meta_row)

        self._lbl_url = QLabel()
        self._lbl_url.setObjectName("NDURL")
        self._lbl_url.setWordWrap(False)
        info_lay.addWidget(self._lbl_url)

        body.addWidget(self._info_frame, 1)
        main_lay.addLayout(body)

        self._placeholder = QLabel(self._t("nd_no_item"))
        self._placeholder.setObjectName("NDPlaceholder")
        self._placeholder.setAlignment(Qt.AlignCenter)
        main_lay.addWidget(self._placeholder)

    def _set_placeholder_cover(self):
        px = QPixmap(self.COVER_SIZE, self.COVER_SIZE)
        px.fill(QColor(0, 0, 0, 0))
        painter = QPainter(px)
        grad = QLinearGradient(0, 0, self.COVER_SIZE, self.COVER_SIZE)
        grad.setColorAt(0.0, QColor("#1F2C3B"))
        grad.setColorAt(1.0, QColor("#14202C"))
        painter.setBrush(grad)
        painter.setPen(QColor("#344356"))
        painter.drawRoundedRect(0, 0, self.COVER_SIZE - 1, self.COVER_SIZE - 1, 12, 12)
        painter.setPen(QColor("#7E8B9A"))
        painter.setFont(QFont("Segoe UI Symbol", 26))
        painter.drawText(px.rect(), Qt.AlignCenter, "\u266a")
        painter.end()
        self._cover.setPixmap(px)

    def _on_thumb_loaded(self, reply: QNetworkReply):
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
            if scaled.width() > self.COVER_SIZE or scaled.height() > self.COVER_SIZE:
                x = (scaled.width() - self.COVER_SIZE) // 2
                y = (scaled.height() - self.COVER_SIZE) // 2
                scaled = scaled.copy(x, y, self.COVER_SIZE, self.COVER_SIZE)
            self._cover.setPixmap(scaled)
        else:
            self._set_placeholder_cover()

        reply.deleteLater()
