from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QColor

from src.stt.deepgram_stt import DeepGramSTT
from src.agents.router import RouterAgent

from src.lib import AsyncQtThread, MicThread, ConversationHistory
from src.ui import TextDisplay, VoiceVisualizer, ContentArea, RecordButton

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Voice Assistant")
        self.resize(500, 220)
        self.setStyleSheet("background-color: rgb(15, 15, 30);")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # --- UI COMPONENTS ---
        self.visualizer = VoiceVisualizer(self, bar_count=42)
        self.text_display = TextDisplay(self, QColor(15, 15, 30))
        self.content_area_ui = ContentArea(self, 220, 800)
        self.toggle_btn = RecordButton(
            "Start Mic", 
            self.start_mic, 
            self.stop_mic
        )

        layout.addWidget(self.visualizer, 0)
        layout.addWidget(self.text_display, 0)
        layout.addWidget(self.content_area_ui, 1)
        layout.addWidget(self.toggle_btn, 0)

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
        router = RouterAgent(self.content_area_ui.set_content_area_markdown)
        response = router.run(instruction, history=self.conversation_history.get_messages())
        
        # Add assistant response to history (if available)
        if response:
            self.conversation_history.add_assistant_message(response)
        
        # Auto-restart mic after LLM/TTS completes
        self.start_mic()

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


        