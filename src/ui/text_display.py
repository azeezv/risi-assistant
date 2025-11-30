from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QFont
from PyQt6.QtWidgets import QWidget, QSizePolicy, QScrollArea


class TextCanvas(QWidget):
    def __init__(self, background, font_color):
        super().__init__()
        self.text = ""
        self.background = background
        self.font_color = font_color

        self.setFixedHeight(50)
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Fixed)

    def set_text(self, text):
        self.text = text
        self.update()

    def append_word(self, word):
        self.text += (" " if self.text else "") + word
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        p.fillRect(self.rect(), self.background)

        p.setPen(self.font_color)
        p.setFont(QFont("Segoe UI", 12))

        margin = 10
        rect = self.rect().adjusted(margin, margin, -margin, -margin)

        # Draw text
        flags = (Qt.AlignmentFlag.AlignLeft |
                 Qt.AlignmentFlag.AlignTop |
                 Qt.TextFlag.TextWordWrap)
        p.drawText(rect, flags, self.text)

        # AUTO-RESIZE CANVAS TO FIT TEXT
        fm = p.fontMetrics()
        text_height = fm.boundingRect(rect, flags, self.text).height()

        self.setMinimumHeight(text_height + 20)


class TextDisplay(QScrollArea):
    """Fully scrollable text widget with custom painting."""
    def __init__(self, parent=None, background):
        super().__init__(parent)

        self.background = background
        self.font_color = QColor(220, 220, 230)

        # inner paint widget
        self.canvas = TextCanvas(self.background, self.font_color)

        self.setWidget(self.canvas)
        self.setWidgetResizable(True)

        # scrollbar policies
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def append_word(self, word: str):
        if self.canvas.text:
            self.canvas.text += " " + word
        else:
            self.canvas.text = word

        self.canvas.update()
        self.ensure_visible()
    
    def set_text(self, text: str, color: QColor):

        self.font_color = color
        self.canvas.font_color = color

        self.canvas.set_text(text)
        
        self.canvas.update()
        self.ensure_visible()

    def ensure_visible(self):
        bar = self.verticalScrollBar()
        if bar:
            bar.setValue(bar.maximum())
