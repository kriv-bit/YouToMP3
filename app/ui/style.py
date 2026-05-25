# app/ui/style.py
"""Centralized, theme-aware QSS stylesheet for the application."""

from PySide6.QtGui import QColor

# ---------------------------------------------------------------------------
# Palettes
# ---------------------------------------------------------------------------

DARK = {
    "APP_BG": "#0E131A",
    "SURFACE": "#161C24",
    "SURFACE_ALT": "#121821",
    "SURFACE_ELEVATED": "#1A2430",
    "SURFACE_ACCENT": "#1A2233",
    "PANEL_EDGE": "#263140",
    "BORDER": "#2B3645",
    "BORDER_STRONG": "#3B4A5E",
    "TEXT": "#E7EDF5",
    "TEXT_MUTED": "#A0ACBA",
    "TEXT_FAINT": "#7C8898",
    "ACCENT": "#5E8BEE",
    "ACCENT_HOVER": "#76A0F5",
    "ACCENT_SOFT": "#233552",
    "ACCENT_SOFT_ALT": "#1E2B41",
    "SELECTION": "#243449",
    "SUCCESS": "#4DBA79",
    "SUCCESS_SOFT": "#16271F",
    "WARNING": "#D2A34A",
    "WARNING_SOFT": "#2A2417",
    "DANGER": "#D86D6D",
    "DANGER_SOFT": "#2A1C1C",
}

LIGHT = {
    "APP_BG": "#F3F5F8",
    "SURFACE": "#FFFFFF",
    "SURFACE_ALT": "#F7F9FC",
    "SURFACE_ELEVATED": "#F0F3F7",
    "SURFACE_ACCENT": "#E8EDF4",
    "PANEL_EDGE": "#D8DEE6",
    "BORDER": "#D0D7E0",
    "BORDER_STRONG": "#B0BCC9",
    "TEXT": "#1F2937",
    "TEXT_MUTED": "#5E6B7A",
    "TEXT_FAINT": "#8E9AAB",
    "ACCENT": "#3B6DD8",
    "ACCENT_HOVER": "#2A5CC5",
    "ACCENT_SOFT": "#D6E3FA",
    "ACCENT_SOFT_ALT": "#E8EEFD",
    "SELECTION": "#C9D6F0",
    "SUCCESS": "#2E9D5E",
    "SUCCESS_SOFT": "#E4F5EB",
    "WARNING": "#C28A2A",
    "WARNING_SOFT": "#F5F0E0",
    "DANGER": "#C94242",
    "DANGER_SOFT": "#FBEAEA",
}


def _pal(theme: str) -> dict[str, str]:
    return LIGHT if theme == "light" else DARK


def status_colors(theme: str) -> dict[str, tuple[QColor, QColor]]:
    """Foreground and background QColors for queue status cells."""
    if theme == "light":
        return {
            "queued": (QColor("#5E6B7A"), QColor("#F0F3F7")),
            "downloading": (QColor("#B07D1A"), QColor("#F5F0E0")),
            "done": (QColor("#2E9D5E"), QColor("#E4F5EB")),
            "error": (QColor("#C94242"), QColor("#FBEAEA")),
            "cancelled": (QColor("#8E9AAB"), QColor("#EEF1F5")),
        }
    return {
        "queued": (QColor("#9DA9B8"), QColor("#18222D")),
        "downloading": (QColor("#D9A441"), QColor("#282316")),
        "done": (QColor("#4EBB78"), QColor("#18251C")),
        "error": (QColor("#D86C6C"), QColor("#281B1B")),
        "cancelled": (QColor("#7E8B9A"), QColor("#1A2028")),
    }


def queue_placeholder_colors(theme: str) -> tuple[str, str, str]:
    """Pen, brush, triangle colors for the queue placeholder icon."""
    if theme == "light":
        return ("#B0BCC9", "#E8EDF4", "#7E8B9A")
    return ("#3B4A5E", "#18222D", "#7C8898")


def nd_placeholder_colors(theme: str) -> tuple[str, str, str, str]:
    """Pen, grad_start, grad_end, note_color for the Now Downloading placeholder cover."""
    if theme == "light":
        return ("#D8DEE6", "#E8EDF4", "#F0F3F7", "#7E8B9A")
    return ("#344356", "#1F2C3B", "#14202C", "#7E8B9A")


def main_qss(theme: str = "dark") -> str:
    c = _pal(theme)
    return f"""
        QMainWindow {{
            background: {c['APP_BG']};
            color: {c['TEXT']};
        }}

        QWidget {{
            color: {c['TEXT']};
            font-size: 12px;
        }}

        QToolTip {{
            background: {c['SURFACE_ALT']};
            color: {c['TEXT']};
            border: 1px solid {c['BORDER']};
            padding: 6px 8px;
        }}

        #Sidebar, #Content, #Panel, #SubPanel, #HeaderPanel, #NowDownloadingCard, #AppDialog {{
            background: {c['SURFACE']};
            border: 1px solid {c['BORDER']};
            border-radius: 14px;
        }}

        #Sidebar {{
            background: {c['SURFACE_ALT']};
            border-color: {c['PANEL_EDGE']};
        }}

        #SidebarHero {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {c['SURFACE_ACCENT']}, stop:1 {c['SURFACE_ALT']});
            border: 1px solid {c['PANEL_EDGE']};
            border-radius: 12px;
        }}

        #HeaderPanel {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {c['SURFACE_ACCENT']}, stop:1 {c['SURFACE']});
            border-color: {c['PANEL_EDGE']};
        }}

        #SubPanel, #InlinePanel, #FormPanel {{
            background: {c['SURFACE_ELEVATED']};
            border: 1px solid {c['BORDER']};
            border-radius: 12px;
        }}

        #SidebarGroup, #ActionBar {{
            background: transparent;
            border: none;
        }}

        QLabel {{
            color: {c['TEXT']};
        }}

        #SidebarEyebrow, #HeaderEyebrow, #CompactEyebrow {{
            color: {c['ACCENT_HOVER']};
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1.2px;
        }}

        #BrandTitle {{
            font-size: 25px;
            font-weight: 800;
            color: {c['TEXT']};
        }}

        #BrandSub {{
            color: {c['TEXT_MUTED']};
            font-size: 12px;
            line-height: 1.4;
        }}

        #PanelTitle, #DialogTitle {{
            font-size: 15px;
            font-weight: 800;
            color: {c['TEXT']};
        }}

        #PanelSubtitle, #DialogSubtitle, #CompactSubtitle {{
            color: {c['TEXT_MUTED']};
            font-size: 11px;
        }}

        #CompactTitle, #ToolbarLabel {{
            color: {c['TEXT']};
            font-size: 12px;
            font-weight: 700;
        }}

        #SidebarLabel, #SectionLabel, #FormLabel {{
            color: {c['TEXT_MUTED']};
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.4px;
        }}

        #H1 {{
            font-size: 19px;
            font-weight: 800;
            color: {c['TEXT']};
        }}

        #H2, #LangLabel, #ThemeLabel, #NowLabel {{
            color: {c['TEXT_MUTED']};
        }}

        #NowLabel {{
            padding-left: 4px;
        }}

        #Divider {{
            background: {c['BORDER']};
            margin: 4px 0 2px 0;
        }}

        QComboBox, QLineEdit, QSpinBox, QTextEdit {{
            background: {c['SURFACE_ALT']};
            border: 1px solid {c['BORDER']};
            border-radius: 10px;
            padding: 9px 11px;
            color: {c['TEXT']};
            selection-background-color: {c['SELECTION']};
            selection-color: {c['TEXT']};
            min-height: 18px;
        }}

        QComboBox:hover, QLineEdit:hover, QSpinBox:hover, QTextEdit:hover {{
            border-color: {c['BORDER_STRONG']};
        }}

        QComboBox:focus, QLineEdit:focus, QSpinBox:focus, QTextEdit:focus {{
            border: 1px solid {c['ACCENT']};
            background: {c['SURFACE']};
        }}

        QComboBox::drop-down, QSpinBox::up-button, QSpinBox::down-button {{
            border: none;
            width: 28px;
        }}

        QComboBox QAbstractItemView {{
            background: {c['SURFACE']};
            border: 1px solid {c['BORDER']};
            selection-background-color: {c['SELECTION']};
            selection-color: {c['TEXT']};
            outline: 0;
        }}

        #Chip {{
            background: {c['SURFACE_ALT']};
            border: 1px solid {c['PANEL_EDGE']};
            border-radius: 10px;
            padding: 9px 11px;
            color: {c['TEXT_MUTED']};
        }}

        QPushButton {{
            background: {c['SURFACE_ELEVATED']};
            border: 1px solid {c['BORDER']};
            border-radius: 10px;
            color: {c['TEXT']};
            padding: 9px 14px;
            min-height: 18px;
            font-size: 12px;
            font-weight: 600;
        }}

        QPushButton:hover {{
            border-color: {c['BORDER_STRONG']};
            background: {c['SURFACE']};
        }}

        QPushButton:pressed {{
            background: {c['SURFACE_ALT']};
        }}

        QPushButton:disabled {{
            color: {c['TEXT_FAINT']};
            background: {c['SURFACE_ALT']};
            border-color: {c['BORDER']};
        }}

        #PrimaryButton {{
            background: {c['ACCENT']};
            border-color: {c['ACCENT_HOVER']};
            color: #FFFFFF;
            min-width: 156px;
            font-weight: 700;
        }}

        #PrimaryButton:hover {{
            background: {c['ACCENT_HOVER']};
            border-color: {c['ACCENT_HOVER']};
        }}

        #PrimaryButton:disabled {{
            background: {c['SURFACE_ELEVATED']};
            border-color: {c['BORDER']};
            color: {c['TEXT_FAINT']};
        }}

        #SecondaryButton {{
            background: {c['SURFACE_ELEVATED']};
            border-color: {c['BORDER']};
            color: {c['TEXT']};
        }}

        #SecondaryButton:hover {{
            background: {c['SURFACE']};
        }}

        #DangerButton {{
            background: {c['SURFACE_ELEVATED']};
            border-color: rgba(201,66,66,0.35);
            color: {c['DANGER']};
        }}

        #DangerButton:hover {{
            background: {c['DANGER_SOFT']};
            border-color: {c['DANGER']};
        }}

        QProgressBar#Progress {{
            background: {c['SURFACE_ALT']};
            border: 1px solid {c['BORDER']};
            border-radius: 10px;
            text-align: center;
            color: {c['TEXT_MUTED']};
            min-height: 16px;
        }}

        QProgressBar#Progress::chunk {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {c['ACCENT']}, stop:1 {c['ACCENT_HOVER']});
            border-radius: 10px;
        }}

        QLabel#Status {{
            font-weight: 700;
            font-size: 13px;
            padding: 6px 10px;
            border-radius: 10px;
        }}

        QLabel#Status[state="idle"] {{
            color: {c['SUCCESS']};
            background: {c['SUCCESS_SOFT']};
            border: 1px solid rgba(46,157,94,0.22);
        }}

        QLabel#Status[state="downloading"] {{
            color: {c['ACCENT_HOVER']};
            background: {c['ACCENT_SOFT']};
            border: 1px solid rgba(59,109,216,0.22);
        }}

        QTextEdit#TextArea {{
            font-family: Consolas;
            font-size: 12px;
        }}

        QTextEdit#ConsoleArea {{
            background: {c['SURFACE_ALT']};
            border: 1px solid {c['PANEL_EDGE']};
            border-radius: 10px;
            padding: 10px 12px;
            color: {c['TEXT']};
            font-family: Consolas;
            font-size: 12px;
        }}

        QTableWidget#QueueTable {{
            background: {c['SURFACE']};
            alternate-background-color: {c['SURFACE_ELEVATED']};
            color: {c['TEXT']};
            border: 1px solid {c['PANEL_EDGE']};
            border-radius: 12px;
            gridline-color: {c['BORDER']};
            selection-background-color: {c['SELECTION']};
            selection-color: {c['TEXT']};
            font-size: 12px;
        }}

        QTableWidget#QueueTable::item {{
            padding: 5px 10px;
            border-bottom: 1px solid {c['BORDER']};
        }}

        QTableWidget#QueueTable::item:hover {{
            background: {c['ACCENT_SOFT_ALT']};
        }}

        QTableWidget#QueueTable QHeaderView::section {{
            background: {c['SURFACE_ELEVATED']};
            color: {c['TEXT']};
            padding: 9px 8px;
            border: none;
            border-bottom: 1px solid {c['PANEL_EDGE']};
            font-weight: 700;
            font-size: 11px;
        }}

        QTableWidget#QueueTable QTableCornerButton::section {{
            background: {c['SURFACE_ELEVATED']};
            border: none;
            border-bottom: 1px solid {c['PANEL_EDGE']};
        }}

        #NowDownloadingCard {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {c['SURFACE_ACCENT']}, stop:1 {c['SURFACE_ELEVATED']});
            border-color: {c['PANEL_EDGE']};
        }}

        #NDLiveTag {{
            background: {c['WARNING_SOFT']};
            color: {c['WARNING']};
            border: 1px solid rgba(194,138,42,0.20);
            border-radius: 10px;
            padding: 1px 7px;
            font-size: 10px;
            font-weight: 700;
        }}

        #NowDownloadingCard #NDTitle {{
            font-size: 14px;
            font-weight: 700;
            color: {c['TEXT']};
        }}

        #NowDownloadingCard #NDArtist,
        #NowDownloadingCard #NDURL,
        #NDPlaceholder,
        #NowDownloadingCard #NDCardLabel {{
            color: {c['TEXT_MUTED']};
        }}

        #NowDownloadingCard #NDDuration {{
            color: {c['WARNING']};
            font-weight: 700;
        }}

        #NowDownloadingCard #NDBadge {{
            color: {c['ACCENT_HOVER']};
            font-weight: 700;
        }}

        #NDCoverPlaceholder {{
            background: {c['SURFACE_ALT']};
            border: 1px solid {c['BORDER']};
            border-radius: 10px;
        }}

        #DialogHeader {{
            border-bottom: 1px solid {c['BORDER']};
        }}

        QDialog QLabel {{
            color: {c['TEXT']};
            font-size: 12px;
        }}

        QDialog QCheckBox {{
            color: {c['TEXT']};
            spacing: 8px;
        }}

        QDialog QCheckBox::indicator {{
            width: 16px;
            height: 16px;
            border: 1px solid {c['BORDER_STRONG']};
            border-radius: 4px;
            background: {c['SURFACE_ALT']};
        }}

        QDialog QCheckBox::indicator:checked {{
            background: {c['ACCENT']};
            border-color: {c['ACCENT']};
        }}

        QSplitter::handle {{
            background: {c['APP_BG']};
            width: 8px;
        }}

        QSplitter::handle:hover {{
            background: {c['BORDER_STRONG']};
        }}

        QToolButton#RowDeleteButton {{
            background: transparent;
            border: none;
            color: {c['TEXT_FAINT']};
            font-size: 13px;
            font-weight: 700;
            padding: 0px;
        }}

        QToolButton#RowDeleteButton:hover {{
            color: {c['DANGER']};
        }}

        QToolButton#RowDeleteButton:disabled {{
            color: {c['TEXT_FAINT']};
        }}

        QToolButton#RowCancelButton {{
            background: transparent;
            border: none;
            color: {c['DANGER']};
            font-size: 13px;
            font-weight: 700;
            padding: 0px;
        }}

        QToolButton#RowCancelButton:hover {{
            color: {c['DANGER']};
            background: rgba(255, 80, 80, 28);
            border-radius: 4px;
        }}

        QScrollBar:vertical {{
            background: {c['SURFACE_ALT']};
            width: 10px;
            margin: 2px;
            border-radius: 5px;
        }}

        QScrollBar::handle:vertical {{
            background: {c['BORDER_STRONG']};
            min-height: 24px;
            border-radius: 5px;
        }}

        QScrollBar::handle:vertical:hover {{
            background: {c['TEXT_FAINT']};
        }}

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}

        QScrollBar:horizontal {{
            background: {c['SURFACE_ALT']};
            height: 10px;
            margin: 2px;
            border-radius: 5px;
        }}

        QScrollBar::handle:horizontal {{
            background: {c['BORDER_STRONG']};
            min-width: 24px;
            border-radius: 5px;
        }}

        QScrollBar::handle:horizontal:hover {{
            background: {c['TEXT_FAINT']};
        }}

        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}

        QDialog {{
            background: {c['SURFACE']};
        }}
    """
