# app/ui/style.py
"""Centralised QSS stylesheet for the entire application."""


def main_qss() -> str:
    return """
        /* ═══════ Global ═══════ */
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

        /* ═══════ Branding ═══════ */
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

        /* ═══════ Headings ═══════ */
        #H1 {
            font-size: 18px;
            font-weight: 800;
        }
        #H2 {
            color: #9AA4B2;
        }

        #LangLabel { color: #9AA4B2; }
        #LangCombo { min-width: 140px; }

        /* ═══════ Combo boxes ═══════ */
        QComboBox {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #0B1422, stop:1 #070C14);
            border: 1px solid #22344C;
            border-left: 3px solid #00D4FF;
            padding: 10px 14px;
            border-radius: 14px;
            color: #E6EDF3;
            font-size: 13px;
            font-weight: 600;
            min-height: 44px;
        }
        QComboBox:hover { border-color: #2E4866; }

        QComboBox::drop-down {
            border: none;
            width: 44px;
            background: #0E1622;
            border-top-right-radius: 14px;
            border-bottom-right-radius: 14px;
        }
        QComboBox QAbstractItemView {
            background: #0A1018;
            border: 1px solid #22344C;
            selection-background-color: #11324B;
            color: #E6EDF3;
            outline: 0;
            padding: 8px;
        }

        /* ═══════ Chip ═══════ */
        #Chip {
            background: #0B111A;
            border: 1px solid #1B2A3D;
            padding: 10px 12px;
            border-radius: 12px;
            color: #9AA4B2;
        }

        /* ═══════ Text / Console areas ═══════ */
        #TextArea, #ConsoleArea {
            background: #070B12;
            border: 1px solid #1B2A3D;
            border-radius: 14px;
            padding: 12px;
            color: #E6EDF3;
            font-family: Consolas;
            font-size: 12px;
        }

        /* ═══════ Scrollbars (global premium) ═══════ */
        QScrollBar:vertical {
            background: #0B111A;
            width: 10px;
            margin: 2px;
            border-radius: 5px;
        }
        QScrollBar::handle:vertical {
            background: #1B2A3D;
            min-height: 24px;
            border-radius: 5px;
        }
        QScrollBar::handle:vertical:hover {
            background: #2B3E56;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        QScrollBar:horizontal {
            background: #0B111A;
            height: 10px;
            margin: 2px;
            border-radius: 5px;
        }
        QScrollBar::handle:horizontal {
            background: #1B2A3D;
            min-width: 24px;
            border-radius: 5px;
        }
        QScrollBar::handle:horizontal:hover {
            background: #2B3E56;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
        }

        /* ═══════ Progress bar ═══════ */
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

        #NowLabel { color:#9AA4B2; font-size:12px; }

        /* ═══════ Primary button ═══════ */
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

        /* ═══════ Secondary button ═══════ */
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

        /* ═══════ Status label ═══════ */
        #Status {
            font-weight: 900;
            font-size: 13px;
            color: #34D399;
        }

        /* ═══════ Queue table: dark premium ═══════ */
        #QueueTable {
            background: #0C1420;
            alternate-background-color: #101B28;
            color: #D0D8E4;
            border: 1px solid #1B2A3D;
            border-radius: 14px;
            gridline-color: #1B2A3D;
            selection-background-color: #162A42;
            selection-color: #E6EDF3;
            font-size: 12px;
        }

        #QueueTable::item {
            padding: 6px 10px;
            border-bottom: 1px solid #141E2C;
        }

        #QueueTable::item:hover {
            background: #152030;
        }

        #QueueTable::item:selected {
            background: #162A42;
            color: #E6EDF3;
        }

        /* Header */
        #QueueTable QHeaderView::section {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #111D2D, stop:1 #0D1824);
            color: #8899AA;
            padding: 10px 8px;
            border: none;
            border-bottom: 2px solid #1B2A3D;
            font-weight: 800;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        /* Corner button */
        #QueueTable QTableCornerButton::section {
            background: #111D2D;
            border: none;
            border-bottom: 2px solid #1B2A3D;
        }

        /* Table scrollbars */
        #QueueTable QScrollBar:vertical {
            background: #0C1420;
            width: 10px;
            margin: 2px;
            border-radius: 5px;
        }
        #QueueTable QScrollBar::handle:vertical {
            background: #1B2A3D;
            min-height: 24px;
            border-radius: 5px;
        }
        #QueueTable QScrollBar::handle:vertical:hover {
            background: #2B3E56;
        }
        #QueueTable QScrollBar::add-line:vertical,
        #QueueTable QScrollBar::sub-line:vertical {
            height: 0px;
        }

        /* ═══════ Now Downloading Card ═══════ */
        #NowDownloadingCard {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #0C1825, stop:1 #101422);
            border: 1px solid #1B2A3D;
            border-radius: 16px;
            padding: 14px;
        }

        #NowDownloadingCard #NDTitle {
            font-size: 14px;
            font-weight: 800;
            color: #E6EDF3;
        }
        #NowDownloadingCard #NDArtist {
            font-size: 12px;
            color: #9AA4B2;
        }
        #NowDownloadingCard #NDDuration {
            font-size: 12px;
            color: #00D4FF;
            font-weight: 700;
        }
        #NowDownloadingCard #NDURL {
            font-size: 11px;
            color: #6B7A8D;
        }
        #NowDownloadingCard #NDBadge {
            font-size: 11px;
            color: #A855F7;
            font-weight: 700;
        }
        #NowDownloadingCard #NDCardLabel {
            font-size: 13px;
            font-weight: 800;
            color: #8899AA;
        }
        #NDPlaceholder {
            color: #4A5568;
            font-size: 13px;
            font-style: italic;
        }
        #NDCoverPlaceholder {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #11243A, stop:1 #1A1030);
            border: 1px solid #1B2A3D;
            border-radius: 10px;
        }

        /* ═══════ Dialog styling ═══════ */
        #AppDialog {
            background: #0E1622;
            border: 1px solid #1B2A3D;
            border-radius: 18px;
            color: #E6EDF3;
        }

        /* Dialog inputs */
        QDialog QLineEdit {
            background: #070B12;
            border: 1px solid #1B2A3D;
            border-radius: 10px;
            padding: 10px 14px;
            color: #E6EDF3;
            font-size: 13px;
            min-height: 38px;
        }
        QDialog QLineEdit:focus {
            border-color: #00D4FF;
        }

        QDialog QCheckBox {
            color: #D0D8E4;
            font-size: 13px;
            spacing: 8px;
        }
        QDialog QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border: 2px solid #22344C;
            border-radius: 4px;
            background: #070B12;
        }
        QDialog QCheckBox::indicator:checked {
            background: #00D4FF;
            border-color: #00D4FF;
        }

        QDialog QSpinBox {
            background: #070B12;
            border: 1px solid #1B2A3D;
            border-radius: 10px;
            padding: 8px 12px;
            color: #E6EDF3;
            font-size: 13px;
            min-height: 38px;
            min-width: 90px;
        }
        QDialog QSpinBox:focus {
            border-color: #00D4FF;
        }

        QDialog QLabel {
            color: #D0D8E4;
            font-size: 13px;
        }

        /* ═══════ Section label ═══════ */
        #SectionLabel {
            font-size: 12px;
            font-weight: 800;
            color: #8899AA;
            letter-spacing: 0.5px;
        }
    """
