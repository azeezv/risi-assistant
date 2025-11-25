import asyncio
import os
import numpy as np
from deepgram import AsyncDeepgramClient
from deepgram.core.events import EventType
from deepgram.extensions.types.sockets import ListenV2SocketClientResponse

class DeepGramSTT():
    def __init__(self):
        self.client = AsyncDeepgramClient(api_key=os.getenv("DEEPGRAM_API_KEY"))
        self.connection = None
        self.loop = None

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
        print("Received message:", msg)
        if hasattr(msg, "transcript") and msg.transcript: # type: ignore
            print("🗣️", msg.transcript) # type: ignore

    async def _send_audio(self, chunk):
        if self.connection:
            await self.connection._send(chunk)

    def process_audio_chunk(self, chunk):
        pcm16 = (chunk * 32767).astype(np.int16).tobytes()
        # Use the captured loop to schedule the coroutine
        if self.loop:
            self.loop.call_soon_threadsafe(asyncio.create_task, self._send_audio(pcm16))