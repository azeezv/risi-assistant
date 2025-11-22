import asyncio

from deepgram import AsyncDeepgramClient
from deepgram.core.events import EventType
from deepgram.extensions.types.sockets import ListenV2SocketClientResponse

from lib.mic_stream import MicStream
import numpy as np
import os

async def deepgram_stream():
    client = AsyncDeepgramClient(api_key=os.getenv("DEEPGRAM_API_KEY"))

    async with client.listen.v2.connect(
        model="flux-general-en",
        encoding="linear16",
        sample_rate=16000
    ) as connection:

        ###########################################################
        # Deepgram event handler
        ###########################################################
        def on_message(msg: ListenV2SocketClientResponse):
            if hasattr(msg, "transcript") and msg.transcript:
                print("🗣️", msg.transcript)

        connection.on(EventType.MESSAGE, on_message)
        connection.on(EventType.OPEN, lambda _: print("🔌 Deepgram connected"))
        connection.on(EventType.CLOSE, lambda _: print("❌ Deepgram closed"))
        connection.on(EventType.ERROR, lambda e: print("Error:", e))

        # Start listening background task
        listen_task = asyncio.create_task(connection.start_listening())

        ###########################################################
        # This async callback receives PCM16 chunks from microphone
        ###########################################################
        async def send_audio(chunk):
            await connection._send(chunk)

        # Capture the loop from the main thread
        loop = asyncio.get_running_loop()

        def prcoss_chunks(chunk):
            pcm16 = (chunk * 32767).astype(np.int16).tobytes()
            # Use the captured loop to schedule the coroutine
            loop.call_soon_threadsafe(asyncio.create_task, send_audio(pcm16))

        ###########################################################
        # Start microphone (blocking) in thread
        ###########################################################
        mic = MicStream(on_stream_callback=prcoss_chunks, sample_rate=16000)

        await loop.run_in_executor(None, mic.start_stream)

        await listen_task