# app/ui/style.py
"""Centralized QSS stylesheet for the application."""

APP_BG = "#0E131A"
SURFACE = "#161C24"
SURFACE_ALT = "#121821"
SURFACE_ELEVATED = "#1A2430"
SURFACE_ACCENT = "#1A2233"
PANEL_EDGE = "#263140"
BORDER = "#2B3645"
BORDER_STRONG = "#3B4A5E"
TEXT = "#E7EDF5"
TEXT_MUTED = "#A0ACBA"
TEXT_FAINT = "#7C8898"
ACCENT = "#5E8BEE"
ACCENT_HOVER = "#76A0F5"
ACCENT_SOFT = "#233552"
ACCENT_SOFT_ALT = "#1E2B41"
SELECTION = "#243449"
SUCCESS = "#4DBA79"
SUCCESS_SOFT = "#16271F"
WARNING = "#D2A34A"
WARNING_SOFT = "#2A2417"
DANGER = "#D86D6D"
DANGER_SOFT = "#2A1C1C"


def main_qss() -> str:
    return f"""
        QMainWindow {{
            background: {APP_BG};
            color: {TEXT};
        }}

        QWidget {{
            color: {TEXT};
            font-size: 12px;
        }}

        QToolTip {{
            background: {SURFACE_ALT};
            color: {TEXT};
            border: 1px solid {BORDER};
            padding: 6px 8px;
        }}

        #Sidebar, #Content, #Panel, #SubPanel, #HeaderPanel, #NowDownloadingCard, #AppDialog {{
            background: {SURFACE};
            border: 1px solid {BORDER};
            border-radius: 14px;
        }}

        #Sidebar {{
            background: {SURFACE_ALT};
            border-color: {PANEL_EDGE};
        }}

        #SidebarHero {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {SURFACE_ACCENT}, stop:1 {SURFACE_ALT});
            border: 1px solid {PANEL_EDGE};
            border-radius: 12px;
        }}

        #HeaderPanel {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {SURFACE_ACCENT}, stop:1 {SURFACE});
            border-color: {PANEL_EDGE};
        }}

        #SubPanel, #InlinePanel, #FormPanel {{
            background: {SURFACE_ELEVATED};
            border: 1px solid {BORDER};
            border-radius: 12px;
        }}

        #SidebarGroup, #ActionBar {{
            background: transparent;
            border: none;
        }}

        QLabel {{
            color: {TEXT};
        }}

        #SidebarEyebrow, #HeaderEyebrow, #CompactEyebrow {{
            color: {ACCENT_HOVER};
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1.2px;
        }}

        #BrandTitle {{
            font-size: 25px;
            font-weight: 800;
            color: {TEXT};
        }}

        #BrandSub {{
            color: {TEXT_MUTED};
            font-size: 12px;
            line-height: 1.4;
        }}

        #PanelTitle, #DialogTitle {{
            font-size: 15px;
            font-weight: 800;
            color: {TEXT};
        }}

        #PanelSubtitle, #DialogSubtitle, #CompactSubtitle {{
            color: {TEXT_MUTED};
            font-size: 11px;
        }}

        #CompactTitle, #ToolbarLabel {{
            color: {TEXT};
            font-size: 12px;
            font-weight: 700;
        }}

        #SidebarLabel, #SectionLabel, #FormLabel {{
            color: {TEXT_MUTED};
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.4px;
        }}

        #H1 {{
            font-size: 19px;
            font-weight: 800;
            color: {TEXT};
        }}

        #H2, #LangLabel, #NowLabel {{
            color: {TEXT_MUTED};
        }}

        #NowLabel {{
            padding-left: 4px;
        }}

        #Divider {{
            background: {BORDER};
            margin: 4px 0 2px 0;
        }}

        QComboBox, QLineEdit, QSpinBox, QTextEdit {{
            background: {SURFACE_ALT};
            border: 1px solid {BORDER};
            border-radius: 10px;
            padding: 9px 11px;
            color: {TEXT};
            selection-background-color: {SELECTION};
            selection-color: {TEXT};
            min-height: 18px;
        }}

        QComboBox:hover, QLineEdit:hover, QSpinBox:hover, QTextEdit:hover {{
            border-color: {BORDER_STRONG};
        }}

        QComboBox:focus, QLineEdit:focus, QSpinBox:focus, QTextEdit:focus {{
            border: 1px solid {ACCENT};
            background: {SURFACE};
        }}

        QComboBox::drop-down, QSpinBox::up-button, QSpinBox::down-button {{
            border: none;
            width: 28px;
        }}

        QComboBox QAbstractItemView {{
            background: {SURFACE};
            border: 1px solid {BORDER};
            selection-background-color: {SELECTION};
            selection-color: {TEXT};
            outline: 0;
        }}

        #Chip {{
            background: {SURFACE_ALT};
            border: 1px solid {PANEL_EDGE};
            border-radius: 10px;
            padding: 9px 11px;
            color: {TEXT_MUTED};
        }}

        QPushButton {{
            background: {SURFACE_ELEVATED};
            border: 1px solid {BORDER};
            border-radius: 10px;
            color: {TEXT};
            padding: 9px 14px;
            min-height: 18px;
            font-size: 12px;
            font-weight: 600;
        }}

        QPushButton:hover {{
            border-color: {BORDER_STRONG};
            background: {SURFACE};
        }}

        QPushButton:pressed {{
            background: {SURFACE_ALT};
        }}

        QPushButton:disabled {{
            color: {TEXT_FAINT};
            background: {SURFACE_ALT};
            border-color: {BORDER};
        }}

        #PrimaryButton {{
            background: {ACCENT};
            border-color: {ACCENT_HOVER};
            color: #FFFFFF;
            min-width: 156px;
            font-weight: 700;
        }}

        #PrimaryButton:hover {{
            background: {ACCENT_HOVER};
            border-color: {ACCENT_HOVER};
        }}

        #PrimaryButton:disabled {{
            background: {SURFACE_ELEVATED};
            border-color: {BORDER};
            color: {TEXT_FAINT};
        }}

        #SecondaryButton {{
            background: {SURFACE_ELEVATED};
            border-color: {BORDER};
            color: {TEXT};
        }}

        #SecondaryButton:hover {{
            background: {SURFACE};
        }}

        QProgressBar#Progress {{
            background: {SURFACE_ALT};
            border: 1px solid {BORDER};
            border-radius: 10px;
            text-align: center;
            color: {TEXT_MUTED};
            min-height: 16px;
        }}

        QProgressBar#Progress::chunk {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {ACCENT}, stop:1 {ACCENT_HOVER});
            border-radius: 10px;
        }}

        QLabel#Status {{
            font-weight: 700;
            font-size: 13px;
            padding: 6px 10px;
            border-radius: 10px;
        }}

        QLabel#Status[state="idle"] {{
            color: {SUCCESS};
            background: {SUCCESS_SOFT};
            border: 1px solid rgba(77,186,121,0.22);
        }}

        QLabel#Status[state="downloading"] {{
            color: {ACCENT_HOVER};
            background: {ACCENT_SOFT};
            border: 1px solid rgba(94,139,238,0.22);
        }}

        QTextEdit#TextArea {{
            font-family: Consolas;
            font-size: 12px;
        }}

        QTextEdit#ConsoleArea {{
            background: {SURFACE_ALT};
            border: 1px solid {PANEL_EDGE};
            border-radius: 10px;
            padding: 10px 12px;
            color: {TEXT};
            font-family: Consolas;
            font-size: 12px;
        }}

        QTableWidget#QueueTable {{
            background: {SURFACE};
            alternate-background-color: {SURFACE_ELEVATED};
            color: {TEXT};
            border: 1px solid {PANEL_EDGE};
            border-radius: 12px;
            gridline-color: {BORDER};
            selection-background-color: {SELECTION};
            selection-color: {TEXT};
            font-size: 12px;
        }}

        QTableWidget#QueueTable::item {{
            padding: 5px 10px;
            border-bottom: 1px solid {BORDER};
        }}

        QTableWidget#QueueTable::item:hover {{
            background: {ACCENT_SOFT_ALT};
        }}

        QTableWidget#QueueTable QHeaderView::section {{
            background: {SURFACE_ELEVATED};
            color: {TEXT};
            padding: 9px 8px;
            border: none;
            border-bottom: 1px solid {PANEL_EDGE};
            font-weight: 700;
            font-size: 11px;
        }}

        QTableWidget#QueueTable QTableCornerButton::section {{
            background: {SURFACE_ELEVATED};
            border: none;
            border-bottom: 1px solid {PANEL_EDGE};
        }}

        #NowDownloadingCard {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {SURFACE_ACCENT}, stop:1 {SURFACE_ELEVATED});
            border-color: {PANEL_EDGE};
        }}

        #NDLiveTag {{
            background: {WARNING_SOFT};
            color: {WARNING};
            border: 1px solid rgba(210,163,74,0.20);
            border-radius: 10px;
            padding: 1px 7px;
            font-size: 10px;
            font-weight: 700;
        }}

        #NowDownloadingCard #NDTitle {{
            font-size: 14px;
            font-weight: 700;
            color: {TEXT};
        }}

        #NowDownloadingCard #NDArtist,
        #NowDownloadingCard #NDURL,
        #NDPlaceholder,
        #NowDownloadingCard #NDCardLabel {{
            color: {TEXT_MUTED};
        }}

        #NowDownloadingCard #NDDuration {{
            color: {WARNING};
            font-weight: 700;
        }}

        #NowDownloadingCard #NDBadge {{
            color: {ACCENT_HOVER};
            font-weight: 700;
        }}

        #NDCoverPlaceholder {{
            background: {SURFACE_ALT};
            border: 1px solid {BORDER};
            border-radius: 10px;
        }}

        #DialogHeader {{
            border-bottom: 1px solid {BORDER};
        }}

        QDialog QLabel {{
            color: {TEXT};
            font-size: 12px;
        }}

        QDialog QCheckBox {{
            color: {TEXT};
            spacing: 8px;
        }}

        QDialog QCheckBox::indicator {{
            width: 16px;
            height: 16px;
            border: 1px solid {BORDER_STRONG};
            border-radius: 4px;
            background: {SURFACE_ALT};
        }}

        QDialog QCheckBox::indicator:checked {{
            background: {ACCENT};
            border-color: {ACCENT};
        }}

        QSplitter::handle {{
            background: {APP_BG};
            width: 8px;
        }}

        QSplitter::handle:hover {{
            background: {BORDER_STRONG};
        }}

        QToolButton#RowDeleteButton {{
            background: transparent;
            border: none;
            color: {TEXT_FAINT};
            font-size: 13px;
            font-weight: 700;
            padding: 0px;
        }}

        QToolButton#RowDeleteButton:hover {{
            color: {DANGER};
        }}

        QToolButton#RowDeleteButton:disabled {{
            color: {TEXT_FAINT};
        }}

        QScrollBar:vertical {{
            background: {SURFACE_ALT};
            width: 10px;
            margin: 2px;
            border-radius: 5px;
        }}

        QScrollBar::handle:vertical {{
            background: {BORDER_STRONG};
            min-height: 24px;
            border-radius: 5px;
        }}

        QScrollBar::handle:vertical:hover {{
            background: {TEXT_FAINT};
        }}

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}

        QScrollBar:horizontal {{
            background: {SURFACE_ALT};
            height: 10px;
            margin: 2px;
            border-radius: 5px;
        }}

        QScrollBar::handle:horizontal {{
            background: {BORDER_STRONG};
            min-width: 24px;
            border-radius: 5px;
        }}

        QScrollBar::handle:horizontal:hover {{
            background: {TEXT_FAINT};
        }}

        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}

        QDialog {{
            background: {SURFACE};
        }}
    """
