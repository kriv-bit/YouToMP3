"""System tray icon with quick actions and native completion toasts."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon


class AppTrayIcon(QObject):
    """Wraps a QSystemTrayIcon and exposes high-level signals for the controller."""

    show_window_requested = Signal()
    hide_window_requested = Signal()
    pause_toggle_requested = Signal()
    open_folder_requested = Signal()
    quit_requested = Signal()

    def __init__(self, icon: QIcon, t_fn: Callable[[str], str], parent: QObject | None = None):
        super().__init__(parent)
        self._t = t_fn
        self._tray = QSystemTrayIcon(icon, parent)
        self._tray.setToolTip(self._t("app_name"))

        self._menu = QMenu()
        self._action_show = QAction(self._t("tray_show"), self._menu)
        self._action_hide = QAction(self._t("tray_hide"), self._menu)
        self._action_pause = QAction(self._t("pause"), self._menu)
        self._action_open_folder = QAction(self._t("open_output_folder"), self._menu)
        self._action_quit = QAction(self._t("tray_quit"), self._menu)

        self._action_show.triggered.connect(self.show_window_requested)
        self._action_hide.triggered.connect(self.hide_window_requested)
        self._action_pause.triggered.connect(self.pause_toggle_requested)
        self._action_open_folder.triggered.connect(self.open_folder_requested)
        self._action_quit.triggered.connect(self.quit_requested)

        self._menu.addAction(self._action_show)
        self._menu.addAction(self._action_hide)
        self._menu.addSeparator()
        self._menu.addAction(self._action_pause)
        self._menu.addAction(self._action_open_folder)
        self._menu.addSeparator()
        self._menu.addAction(self._action_quit)
        self._tray.setContextMenu(self._menu)

        self._tray.activated.connect(self._on_activated)

    @property
    def is_supported(self) -> bool:
        return QSystemTrayIcon.isSystemTrayAvailable()

    def show(self):
        if self.is_supported:
            self._tray.show()

    def hide(self):
        self._tray.hide()

    def set_t(self, t_fn: Callable[[str], str]):
        self._t = t_fn
        self._action_show.setText(self._t("tray_show"))
        self._action_hide.setText(self._t("tray_hide"))
        self._action_open_folder.setText(self._t("open_output_folder"))
        self._action_quit.setText(self._t("tray_quit"))
        self.set_pause_state(paused=False)
        self._tray.setToolTip(self._t("app_name"))

    def set_pause_state(self, paused: bool):
        self._action_pause.setText(self._t("resume") if paused else self._t("pause"))

    def set_paused_visible(self, enabled: bool):
        self._action_pause.setEnabled(enabled)

    def notify(self, title: str, message: str, *, kind: str = "info", timeout_ms: int = 6000):
        if not self.is_supported:
            return
        icon_map = {
            "info": QSystemTrayIcon.Information,
            "warning": QSystemTrayIcon.Warning,
            "error": QSystemTrayIcon.Critical,
        }
        self._tray.showMessage(title, message, icon_map.get(kind, QSystemTrayIcon.Information), timeout_ms)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason):
        # Left-click (Trigger) or double-click toggles window visibility.
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.show_window_requested.emit()
