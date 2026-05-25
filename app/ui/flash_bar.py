"""A lightweight in-window toast banner for non-modal prompts."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QToolButton


class FlashBar(QFrame):
    """A horizontal banner with a message, an Accept button and a dismiss button.

    Auto-hides after a configurable timeout. Intended to be embedded inside the
    main window layout — no fancy positioning, no platform-native popups.
    """

    accepted = Signal(str)
    dismissed = Signal()

    def __init__(self, t_fn: Callable[[str], str], parent=None, timeout_ms: int = 12_000):
        super().__init__(parent)
        self.setObjectName("FlashBar")
        self._t = t_fn
        self._payload = ""
        self._timeout_ms = timeout_ms

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 10, 10)
        layout.setSpacing(10)

        self.icon_label = QLabel("📎")
        self.icon_label.setObjectName("FlashBarIcon")
        layout.addWidget(self.icon_label)

        self.message = QLabel("")
        self.message.setObjectName("FlashBarMessage")
        self.message.setWordWrap(False)
        self.message.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.message, 1)

        self.accept_btn = QPushButton()
        self.accept_btn.setObjectName("FlashBarAccept")
        self.accept_btn.clicked.connect(self._on_accept)
        layout.addWidget(self.accept_btn)

        self.dismiss_btn = QToolButton()
        self.dismiss_btn.setText("✕")
        self.dismiss_btn.setObjectName("FlashBarDismiss")
        self.dismiss_btn.clicked.connect(self.dismiss)
        layout.addWidget(self.dismiss_btn)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.dismiss)

        self.set_t(t_fn)
        self.hide()

    def set_t(self, t_fn: Callable[[str], str]):
        self._t = t_fn
        self.accept_btn.setText(self._t("add"))
        self.dismiss_btn.setToolTip(self._t("dismiss"))

    def show_url_prompt(self, url: str, body_template_key: str = "clipboard_detected"):
        """Display the banner asking the user to enqueue ``url``."""
        if not url:
            return
        self._payload = url
        try:
            message = self._t(body_template_key).format(url=self._shorten(url))
        except Exception:
            message = url
        self.message.setText(message)
        self.message.setToolTip(url)
        self.show()
        self._timer.start(self._timeout_ms)

    def dismiss(self):
        self._timer.stop()
        self._payload = ""
        self.message.setText("")
        self.hide()
        self.dismissed.emit()

    def _on_accept(self):
        payload = self._payload
        self.dismiss()
        if payload:
            self.accepted.emit(payload)

    @staticmethod
    def _shorten(url: str, limit: int = 70) -> str:
        if len(url) <= limit:
            return url
        return url[: limit - 1] + "…"
