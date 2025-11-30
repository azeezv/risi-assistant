from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QPushButton

class RecordButton(QPushButton):
    def __init__(
            self, 
            placeholder_text: str, 
            start_mic_callback, 
            stop_mic_callback
        ):
        super().__init__(placeholder_text)
        
        # Callbacks
        self.start_mic = start_mic_callback
        self.stop_mic = stop_mic_callback

        # Configuration
        self.setCheckable(True)
        self.toggled.connect(self.handle_toggle)

        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def handle_toggle(self, checked):
        if checked:
            
            self.setText("Stop Mic")
            
            # self.setStyleSheet("background-color: #ff4444; color: white;") 
            if self.start_mic:
                self.start_mic()
        else:
            
            self.setText("Start Mic")
            
            self.setStyleSheet("") 
            if self.stop_mic:
                self.stop_mic()