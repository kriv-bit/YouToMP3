def main_qss() -> str:
    return """
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

        #H1 {
            font-size: 18px;
            font-weight: 800;
        }
        #H2 {
            color: #9AA4B2;
        }

        #LangLabel { color: #9AA4B2; }
        #LangCombo {
            min-width: 140px;
        }

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

        #Chip {
            background: #0B111A;
            border: 1px solid #1B2A3D;
            padding: 10px 12px;
            border-radius: 12px;
            color: #9AA4B2;
        }

        #TextArea, #ConsoleArea {
            background: #070B12;
            border: 1px solid #1B2A3D;
            border-radius: 14px;
            padding: 12px;
            color: #E6EDF3;
            font-family: Consolas;
            font-size: 12px;
        }

        /* Scrollbar (makes it feel premium) */
        QScrollBar:vertical {
            background: #0B111A;
            width: 12px;
            margin: 2px;
            border-radius: 6px;
        }
        QScrollBar::handle:vertical {
            background: #1B2A3D;
            min-height: 24px;
            border-radius: 6px;
        }
        QScrollBar::handle:vertical:hover {
            background: #2B3E56;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }

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

        #Status {
            font-weight: 900;
            font-size: 13px;
            color: #34D399;
        }
        /* Queue table: white card for contrast */
        #QueueTable {
            background: #FFFFFF;
            color: #0A0F16;
            border: 1px solid #1B2A3D;
            border-radius: 14px;
            gridline-color: #E6EAF0;
            selection-background-color: #D6ECFF;
            selection-color: #0A0F16;
            font-size: 12px;
        }

        #QueueTable::item {
            padding: 6px 8px;
        }

        #QueueTable::item:selected {
            background: #D6ECFF;
            color: #0A0F16;
        }

        /* Header */
        #QueueTable QHeaderView::section {
            background: #EAF4FF;
            color: #0A0F16;
            padding: 8px;
            border: none;
            border-bottom: 1px solid #D6E1EE;
            font-weight: 900;
        }

        /* Corner button */
        #QueueTable QTableCornerButton::section {
            background: #EAF4FF;
            border: none;
            border-bottom: 1px solid #D6E1EE;
        }

        /* Make table scrollbars match your theme */
        #QueueTable QScrollBar:vertical {
            background: #F3F6FA;
            width: 12px;
            margin: 2px;
            border-radius: 6px;
        }
        #QueueTable QScrollBar::handle:vertical {
            background: #C9D6E6;
            min-height: 24px;
            border-radius: 6px;
        }
        #QueueTable QScrollBar::handle:vertical:hover {
            background: #AFC0D6;
        }
        #QueueTable QScrollBar::add-line:vertical,
        #QueueTable QScrollBar::sub-line:vertical {
            height: 0px;
}
        """
