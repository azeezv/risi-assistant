FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    wget curl build-essential \
    portaudio19-dev libportaudio2 libsndfile1 ffmpeg \
    # The Bridge Libraries
    pulseaudio-utils alsa-utils libasound2-plugins \
    && rm -rf /var/lib/apt/lists/*

# Redirects Python (ALSA) to the Pulse Socket
RUN echo "pcm.default type pulse\nctl.default type pulse" > /etc/asound.conf

RUN pip install --no-cache-dir \
    sounddevice soundfile scipy numpy python-dotenv deepgram-sdk PyQt6

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
WORKDIR /app
CMD ["/bin/bash"]