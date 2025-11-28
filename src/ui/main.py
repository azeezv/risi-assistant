from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QColor

from src.lib.async_qt import AsyncQtThread
from src.stt.deepgram_stt import DeepGramSTT
from src.ui.text_display import TextDisplay
from src.ui.voice_visualizer import VoiceVisualizer
from src.lib.mic import MicThread
from src.agents.router.engine import RouterAgent
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
        
        # --- RECORD BTN ---
        self.toggle_btn = QPushButton("Start Mic")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.toggled.connect(self.toggle_mic)

        layout.addWidget(self.visualizer)
        layout.addWidget(self.text_display)
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
        self.stt_thread = AsyncQtThread(self.stt_service.start())

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
        # font color for consistency.
        self.current_instruction = text
        self.text_display.set_text(text, QColor(220, 220, 230))

    def on_silence_detected(self):
        """Called when user stops speaking for > 2 seconds. Send instruction to LLM."""
        if self.current_instruction.strip():
            # Pause mic to prevent AI response from being picked up
            self.stop_mic()
            
            print(f"🎯 Instruction ready for LLM: {self.current_instruction}")
            self.send_to_llm(self.current_instruction)
            # Reset for next instruction
            self.current_instruction = ""

    def send_to_llm(self, instruction: str):
        """Process the instruction with an LLM and auto-restart mic after TTS finishes."""
        print(f"Sending to LLM: {instruction}")
        # Update UI with processing status
        self.text_display.set_text(f"Processing: {instruction}...", QColor(200, 200, 255))
        
        # Add user message to history
        self.conversation_history.add_user_message(instruction)
        
        # Pass conversation history and instruction to router
        router = RouterAgent()
        response = router.run(instruction, history=self.conversation_history.get_messages())
        
        # Add assistant response to history (if available)
        if response:
            self.conversation_history.add_assistant_message(response)
        
        # Auto-restart mic after LLM/TTS completes
        self.start_mic()


        