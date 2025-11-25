import asyncio
import os
import numpy as np
from deepgram import AsyncDeepgramClient
from deepgram.core.events import EventType
from deepgram.extensions.types.sockets import ListenV2SocketClientResponse

from typing import Any, Optional

class DeepGramSTT():
    def __init__(self, emitter: Optional[Any] = None):
        """emitter: a QObject-like with a `transcript` pyqtSignal(str) attribute.
        The emitter should live in the Qt main thread so emitting from the
        async thread will queue the signal correctly into the GUI thread.
        """
        self.client = AsyncDeepgramClient(api_key=os.getenv("DEEPGRAM_API_KEY"))
        self.connection = None
        self.loop = None
        self.emitter = emitter

    async def start(self):
        # Capture the loop from the main thread
        self.loop = asyncio.get_running_loop()

        async with self.client.listen.v2.connect(
            model="flux-general-en",
            encoding="linear16",
            sample_rate="16000"
        ) as connection:
            self.connection = connection

            self.connection.on(EventType.MESSAGE, self.on_transcript)
            self.connection.on(EventType.OPEN, lambda _: print("🔌 Deepgram connected"))
            self.connection.on(EventType.CLOSE, lambda _: print("❌ Deepgram closed"))
            self.connection.on(EventType.ERROR, lambda e: print("Error:", e))

            # Start listening background task
            listen_task = asyncio.create_task(self.connection.start_listening())

            await listen_task

    def on_transcript(self, msg: ListenV2SocketClientResponse):
        # msg may be a pydantic model with attributes like `transcript`, `words`,
        # and `end_of_turn_confidence`. Safely extract `transcript`.
        transcript = None
        if hasattr(msg, "transcript"):
            transcript = getattr(msg, "transcript")
        elif isinstance(msg, dict):
            transcript = msg.get("transcript")

        if transcript:
            print("🗣️", transcript)
            # If an emitter was provided (a QObject with a pyqtSignal), emit it.
            try:
                if self.emitter is not None and hasattr(self.emitter, "transcript"):
                    # emit from async thread; Qt will queue to main thread
                    self.emitter.transcript.emit(transcript)
            except Exception:
                # Don't let UI emission errors break STT loop; just log.
                print("Failed to emit transcript to emitter")

    async def _send_audio(self, chunk):
        if self.connection:
            # Use the public send_media helper which will route binary audio
            # to the websocket correctly.
            await self.connection.send_media(chunk)

    def process_audio_chunk(self, chunk):
        pcm16 = (chunk * 32767).astype(np.int16).tobytes()
        # Use the captured loop to schedule the coroutine
        if self.loop:
            self.loop.call_soon_threadsafe(asyncio.create_task, self._send_audio(pcm16))