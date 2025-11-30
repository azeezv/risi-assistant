from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTextBrowser, QHBoxLayout
from PyQt6.QtCore import QPropertyAnimation, QRect, QEasingCurve
from markdown import markdown
from PyQt6.QtCore import Qt

class ContentArea(QWidget):
    def __init__(self, compact_height, expanded_height):
        super().__init__()
        
        # 1. Setup Data
        self.compact_height = compact_height
        self.expanded_height = expanded_height

        # 2. Setup Layouts
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(5)
        self.content_layout.setContentsMargins(10, 5, 10, 10) # Added margin for looks

        # 3. Setup Components
        self.content_area = QTextBrowser(self)
        self.content_area.setOpenExternalLinks(True)
        # Make it look clean (no border)
        self.content_area.setStyleSheet("border: none; background-color: transparent;") 
        
        self.close_btn = QPushButton("✕ Close")
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setMaximumWidth(80)
        self.close_btn.setFixedHeight(25)
        self.close_btn.clicked.connect(self.hide_content_area)
    
        self.content_header = QHBoxLayout()
        self.content_header.addStretch()
        self.content_header.addWidget(self.close_btn)

        # 4. CRITICAL FIX: Add items to the main layout
        self.content_layout.addLayout(self.content_header)
        self.content_layout.addWidget(self.content_area)

        self.setLayout(self.content_layout)
        
        # Start hidden
        self.setVisible(False)
    
    def set_content_area_markdown(self, md_text: str):
        """Set text and trigger expansion."""
        html = markdown(md_text, extensions=['fenced_code', 'tables'])
        self.content_area.setHtml(html)
        
        # Only animate if we are currently hidden
        if not self.isVisible():
            self.animate_window_height(expand=True)
            self.setVisible(True)

    def hide_content_area(self):
        """Trigger collapse."""
        self.animate_window_height(expand=False)

    def animate_window_height(self, expand: bool):
        """
        Animates the PARENT WINDOW geometry, not this widget's geometry.
        """
        # Get the main window (the top-level parent)
        main_window = self.window()
        
        # --- FIX: Safety check for Pylance ---
        if main_window is None:
            return

        self.animation = QPropertyAnimation(main_window, b"geometry")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        current_geom = main_window.geometry()
        self.animation.setStartValue(current_geom)
        
        if expand:
            target_height = self.expanded_height
        else:
            target_height = self.compact_height
            self.animation.finished.connect(lambda: self.setVisible(False))

        new_geom = QRect(
            current_geom.x(),
            current_geom.y(),
            current_geom.width(),
            target_height
        )
        
        self.animation.setEndValue(new_geom)
        self.animation.start()