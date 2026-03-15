# app/ui/style.py
"""Centralized QSS stylesheet for the application."""

APP_BG = "#0F141B"
SURFACE = "#151C24"
SURFACE_ALT = "#111820"
SURFACE_SUBTLE = "#1A2430"
BORDER = "#2A3644"
BORDER_STRONG = "#344356"
TEXT = "#E7EDF5"
TEXT_MUTED = "#9DA9B8"
TEXT_FAINT = "#7E8B9A"
ACCENT = "#5D8EF6"
ACCENT_HOVER = "#76A2FF"
SELECTION = "#253247"
SUCCESS = "#4EBB78"
WARNING = "#D9A441"
DANGER = "#D86C6C"


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

        #Sidebar, #Content, #Panel, #SubPanel, #HeaderPanel, #SidebarGroup, #NowDownloadingCard, #AppDialog {{
            background: {SURFACE};
            border: 1px solid {BORDER};
            border-radius: 14px;
        }}

        #Sidebar {{
            background: {SURFACE_ALT};
        }}

        QLabel {{
            color: {TEXT};
        }}

        #BrandTitle {{
            font-size: 24px;
            font-weight: 800;
        }}

        #BrandSub {{
            color: {TEXT_MUTED};
            font-size: 12px;
        }}

        #Divider {{
            background: {BORDER};
            margin: 4px 0 2px 0;
        }}

        #SidebarLabel, #SectionLabel {{
            color: {TEXT_MUTED};
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.5px;
        }}

        #H1 {{
            font-size: 18px;
            font-weight: 800;
            color: {TEXT};
        }}

        #H2, #LangLabel, #NowLabel {{
            color: {TEXT_MUTED};
        }}

        QComboBox, QLineEdit, QSpinBox, QTextEdit {{
            background: {SURFACE_ALT};
            border: 1px solid {BORDER};
            border-radius: 10px;
            padding: 10px 12px;
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
        }}

        QComboBox::drop-down {{
            border: none;
            width: 32px;
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
            border: 1px solid {BORDER};
            border-radius: 10px;
            padding: 10px 12px;
            color: {TEXT_MUTED};
        }}

        QPushButton {{
            background: {SURFACE_SUBTLE};
            border: 1px solid {BORDER};
            border-radius: 10px;
            color: {TEXT};
            padding: 10px 14px;
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
        }}

        #PrimaryButton {{
            background: {ACCENT};
            border-color: {ACCENT};
            color: #FFFFFF;
            min-width: 160px;
            font-weight: 700;
        }}

        #PrimaryButton:hover {{
            background: {ACCENT_HOVER};
            border-color: {ACCENT_HOVER};
        }}

        #PrimaryButton:pressed {{
            background: {ACCENT};
        }}

        #SecondaryButton {{
            background: {SURFACE_SUBTLE};
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
            background: {ACCENT};
            border-radius: 10px;
        }}

        QLabel#Status {{
            font-weight: 700;
            font-size: 13px;
        }}

        QLabel#Status[state="idle"] {{
            color: {SUCCESS};
        }}

        QLabel#Status[state="downloading"] {{
            color: {ACCENT};
        }}

        QTextEdit#TextArea {{
            font-family: Consolas;
            font-size: 12px;
        }}

        QTextEdit#ConsoleArea {{
            background: {SURFACE_ALT};
            border: 1px solid {BORDER};
            border-radius: 10px;
            padding: 10px 12px;
            color: {TEXT};
            font-family: Consolas;
            font-size: 12px;
        }}

        QTableWidget#QueueTable {{
            background: {SURFACE};
            alternate-background-color: {SURFACE_SUBTLE};
            color: {TEXT};
            border: 1px solid {BORDER};
            border-radius: 12px;
            gridline-color: {BORDER};
            selection-background-color: {SELECTION};
            selection-color: {TEXT};
            font-size: 12px;
        }}

        QTableWidget#QueueTable::item {{
            padding: 6px 10px;
            border-bottom: 1px solid {BORDER};
        }}

        QTableWidget#QueueTable::item:hover {{
            background: {SELECTION};
        }}

        QTableWidget#QueueTable QHeaderView::section {{
            background: {SURFACE_ALT};
            color: {TEXT_MUTED};
            padding: 10px 8px;
            border: none;
            border-bottom: 1px solid {BORDER};
            font-weight: 700;
            font-size: 11px;
        }}

        QTableWidget#QueueTable QTableCornerButton::section {{
            background: {SURFACE_ALT};
            border: none;
            border-bottom: 1px solid {BORDER};
        }}

        #NowDownloadingCard {{
            background: {SURFACE_SUBTLE};
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
            color: {ACCENT};
            font-weight: 700;
        }}

        #NDCoverPlaceholder {{
            background: {SURFACE_ALT};
            border: 1px solid {BORDER};
            border-radius: 10px;
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
