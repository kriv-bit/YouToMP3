from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFontMetrics
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QLabel


def add_shadow(widget, color_hex="#00D4FF", blur=22, x=0, y=6, alpha=70):
    eff = QGraphicsDropShadowEffect()
    c = QColor(color_hex)
    c.setAlpha(alpha)
    eff.setColor(c)
    eff.setBlurRadius(blur)
    eff.setOffset(x, y)
    widget.setGraphicsEffect(eff)

def set_elided(label: QLabel, text: str, min_width=240, padding=10):
    fm = QFontMetrics(label.font())
    w = label.width() - padding
    if w <= 10:
        w = min_width
    label.setText(fm.elidedText(text, Qt.ElideLeft, w))
