from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QFont
from PyQt6.QtWidgets import QWidget, QSizePolicy


class TextDisplay(QWidget):
    def __init__(self, parent=None, background=QColor(15, 15, 30)):
        super().__init__(parent)
        self.text = ""
        self.background = background
        self.font_color = QColor(220, 220, 230)

        self.setMinimumHeight(50)
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Preferred)

    def append_word(self, word: str):
        """Add text gradually (word-by-word)."""
        if self.text:
            self.text += " " + word
        else:
            self.text = word
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        # background
        p.fillRect(self.rect(), self.background)

        # text
        p.setPen(self.font_color)
        p.setFont(QFont("Segoe UI", 12))

        margin = 10
        rect = self.rect().adjusted(margin, margin, -margin, -margin)
        p.drawText(rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap, self.text)
