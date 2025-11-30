from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTextBrowser
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QColor

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
        
        # --- RECORD BTN ---
        self.toggle_btn = QPushButton("Start Mic")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.toggled.connect(self.toggle_mic)

        layout.addWidget(self.visualizer)
        layout.addWidget(self.text_display)
        # --- CONTENT AREA (Hidden by default) ---
        # Use QTextBrowser to render HTML converted from Markdown
        self.content_area = QTextBrowser(self)
        self.content_area.setOpenExternalLinks(True)
        self.content_area.setVisible(False)
        layout.addWidget(self.content_area)
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
            # The router may return a JSON string (e.g. {voice_summary, display_content})
            display_markup = None
            assistant_text = None
            try:
                if isinstance(response, str) and response.strip().startswith("{"):
                    parsed = json.loads(response)
                elif isinstance(response, dict):
                    parsed = response
                else:
                    parsed = None
            except Exception:
                parsed = None

            if isinstance(parsed, dict):
                # Prefer explicit display_content if present
                display_markup = parsed.get("display_content") or parsed.get("display")
                # For conversation history / TTS, prefer the voice_summary or a short response_text
                assistant_text = parsed.get("voice_summary") or parsed.get("response_text") or parsed.get("message")

            # Fallbacks
            if assistant_text is None:
                # if response is a plain string, use it
                if isinstance(response, str):
                    assistant_text = response
                else:
                    assistant_text = json.dumps(response)

            # Save assistant message (text summary) to history
            self.conversation_history.add_assistant_message(assistant_text)

            # If we found displayable markdown/HTML, render it
            if display_markup:
                html = self._markdown_to_html(display_markup)
                self.content_area.setHtml(html)
                self.content_area.setVisible(True)
                # Expand window to show content area
                try:
                    self.resize(500, 600)
                except Exception:
                    pass
            else:
                # If no explicit display content but the assistant_text looks like markdown, render that
                if self._looks_like_markdown(assistant_text):
                    html = self._markdown_to_html(assistant_text)
                    self.content_area.setHtml(html)
                    self.content_area.setVisible(True)
                    try:
                        self.resize(500, 600)
                    except Exception:
                        pass
        
        # Auto-restart mic after LLM/TTS completes
        self.start_mic()

    def _looks_like_markdown(self, text: str) -> bool:
        """Heuristic: returns True if text likely contains Markdown/rich content."""
        if not text or not isinstance(text, str):
            return False
        markers = ['```', '\n#', '\n##', '| ', '\n* ', '```']
        for m in markers:
            if m in text:
                return True
        # If it contains multiple newlines and punctuation typical of markdown
        if text.count('\n') > 3 and any(ch in text for ch in ['```', '#', '*', '`', '|']):
            return True
        return False

    def _markdown_to_html(self, md_text: str) -> str:
        """Convert Markdown to HTML. Use `markdown` package if available, otherwise fallback to simple conversion."""
        try:
            import markdown
            html = markdown.markdown(md_text, extensions=['fenced_code', 'tables'])
            return html
        except Exception:
            # Fallback: escape basic HTML and convert newlines to <br>
            import html as _html
            escaped = _html.escape(md_text)
            return '<pre style="white-space:pre-wrap;">' + escaped + '</pre>'

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


        