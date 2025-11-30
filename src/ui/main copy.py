from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTextBrowser, QHBoxLayout
from PyQt6.QtCore import QObject, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor
from markdown import markdown

from src.lib.async_qt import AsyncQtThread
from src.stt.deepgram_stt import DeepGramSTT
from src.ui.text_display import TextDisplay
from src.ui.voice_visualizer import VoiceVisualizer
from src.lib.mic import MicThread
from src.agents.router import RouterAgent
from src.lib.conversation_history import ConversationHistory

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Voice Assistant")
        self.resize(500, 220)
        self.setStyleSheet("background-color: rgb(15, 15, 30);")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # --- VISUALIZER ---
        self.visualizer = VoiceVisualizer(self, bar_count=24)
        self.visualizer.setMinimumHeight(120)

        # --- TEXT LABEL BELOW VISUALIZER ---
        self.text_display = TextDisplay(self)
        self.text_display.append_word(".")

        # --- CONTENT AREA (Hidden by default) with close button ---
        content_layout = QVBoxLayout()
        content_layout.setSpacing(5)
        content_layout.setContentsMargins(5, 5, 5, 5)
        
        self.content_area = QTextBrowser(self)
        self.content_area.setOpenExternalLinks(True)
        self.content_area.setVisible(False)
        
        close_btn = QPushButton("✕ Close")
        close_btn.setMaximumWidth(80)
        close_btn.setFixedHeight(25)
        close_btn.clicked.connect(self.hide_content_area)
        
        # Layout: content area + close button (right-aligned)
        content_header = QHBoxLayout()
        content_header.addStretch()
        content_header.addWidget(close_btn)
        
        content_layout.addLayout(content_header)
        content_layout.addWidget(self.content_area)
        
        # Create a container widget for content with layout
        content_container = QWidget()
        content_container.setLayout(content_layout)
        content_container.setVisible(False)
        self.content_container = content_container
        
        # Store initial and expanded sizes
        self.compact_height = 220
        self.expanded_height = 600
        
        # --- RECORD BTN ---
        self.toggle_btn = QPushButton("Start Mic")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.toggled.connect(self.toggle_mic)

        layout.addWidget(self.visualizer)
        layout.addWidget(self.text_display)
        layout.addWidget(self.content_container)
        layout.addWidget(self.toggle_btn)

        self.mic_thread = None

        # Track the current full instruction text for LLM processing
        self.current_instruction = ""
        
        # Initialize conversation history to maintain context
        self.conversation_history = ConversationHistory(max_exchanges=20)

        # Transcript emitter lives in the main (GUI) thread. DeepGramSTT will
        # emit `transcript` from the async thread and Qt will queue the signal
        # back to the GUI thread safely.
        class TranscriptEmitter(QObject):
            transcript = pyqtSignal(str)

        self.transcript_emitter = TranscriptEmitter()
        self.transcript_emitter.transcript.connect(self.on_transcript_received)

        self.stt_service = DeepGramSTT(emitter=self.transcript_emitter)
        # Pass the coroutine *factory* (callable) so the coroutine is created
        # inside the async thread's event loop and not before the thread starts.
        self.stt_thread = AsyncQtThread(self.stt_service.start)

    def toggle_mic(self, checked):
        if checked:
            self.toggle_btn.setText("Stop Mic")
            self.start_mic()
        else:
            self.toggle_btn.setText("Start Mic")
            self.stop_mic()

    def start_mic(self):
        self.mic_thread = MicThread(noise_floor=0.0095, sensitivity=40, silence_duration_sec=1.0)
        
        # Reset instruction state
        self.current_instruction = ""
        
        # connect signals
        assert self.mic_thread.worker is not None
        self.mic_thread.worker.volume_signal.connect(self.process_volume)
        self.mic_thread.worker.voice_signal.connect(self.stt_service.process_audio_chunk)
        self.mic_thread.worker.silence_signal.connect(self.on_silence_detected)
        
        self.mic_thread.start()
        self.stt_thread.start()

    def stop_mic(self):
        assert self.mic_thread is not None
        self.mic_thread.stop()
        self.mic_thread = None
        
        # stop visualizer
        self.visualizer.setActive(False)

    def process_volume(self, vol):
        self.visualizer.setActive(vol > 0.01)

    def on_transcript_received(self, text: str):
        # Update the TextDisplay with the transcript. Use the configured
        self.current_instruction = text
        self.text_display.set_text(text, QColor(220, 220, 230))

    def on_silence_detected(self):
        """Called when user stops speaking for > 1 seconds. Send instruction to LLM."""
        if self.current_instruction.strip():
            # Pause mic to prevent AI response from being picked up
            self.stop_mic()
            
            print(f"🎯 Instruction ready for LLM: {self.current_instruction}")
            self.send_to_router_agent(self.current_instruction)
            # Reset for next instruction
            self.current_instruction = ""

    def send_to_router_agent(self, instruction: str):
        """Process the instruction with an LLM and auto-restart mic after TTS finishes."""
        print(f"Sending to LLM: {instruction}")
        # Update UI with processing status
        self.text_display.set_text(f"Processing: {instruction}...", QColor(200, 200, 255))
        
        # Add user message to history
        self.conversation_history.add_user_message(instruction)
        
        # Pass conversation history and instruction to router
        # Pass the UI callback so router can update content area when reasoning returns display_content
        router = RouterAgent(ui_callback=self.set_content_area_markdown)
        response = router.run(instruction, history=self.conversation_history.get_messages())
        
        # Add assistant response to history (if available)
        if response:
            self.conversation_history.add_assistant_message(response)
        
        # Auto-restart mic after LLM/TTS completes
        self.start_mic()

    def set_content_area_markdown(self, md_text: str):
        """Set the content area text using markdown formatting and animate expand."""
        html = markdown(md_text, extensions=['fenced_code', 'tables'])
        self.content_area.setHtml(html)
        self.animate_expand()

    def animate_expand(self):
        """Smoothly expand window to show content area."""
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300)  # 300ms animation
        
        # Start from current geometry, expand height
        current_geom = self.geometry()
        self.animation.setStartValue(current_geom)
        
        expanded_geom = current_geom.adjusted(0, 0, 0, self.expanded_height - self.compact_height)
        self.animation.setEndValue(expanded_geom)
        
        self.content_container.setVisible(True)
        self.animation.start()

    def hide_content_area(self):
        """Smoothly collapse window back to compact size."""
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300)  # 300ms animation
        
        # Start from current geometry, collapse height
        current_geom = self.geometry()
        self.animation.setStartValue(current_geom)
        
        collapsed_geom = current_geom.adjusted(0, 0, 0, -(current_geom.height() - self.compact_height))
        self.animation.setEndValue(collapsed_geom)
        
        # Hide content container after animation completes
        self.animation.finished.connect(lambda: self.content_container.setVisible(False))
        self.animation.start()

    def closeEvent(self, event):
        """Ensure background threads and async loops are stopped on window close."""
        try:
            if self.mic_thread is not None:
                self.stop_mic()
        except Exception:
            pass

        try:
            if hasattr(self, 'stt_thread') and self.stt_thread is not None:
                self.stt_thread.stop()
        except Exception:
            pass

        super().closeEvent(event)


        