FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    wget curl build-essential \
    portaudio19-dev libportaudio2 libsndfile1 ffmpeg \
    # The Bridge Libraries
    pulseaudio-utils alsa-utils libasound2-plugins \
    # PyQt6 / Qt-required libs
    libegl1 \
    libgl1 \
    libglu1-mesa \
    libglx0 \
    libxrender1 \
    libxkbcommon0 \
    libxkbcommon-x11-0 \
    libfontconfig1 \
    libfreetype6 \
    libx11-xcb1 \
    libxcb1 \
    libxcb-cursor0 \
    libxcb-util1 \
    libxcb-render0 \
    libxcb-glx0 \
    libxcb-keysyms1 \
    libxcb-image0 \
    libxcb-icccm4 \
    libxcb-composite0 \
    libxcb-shm0 \
    libxcb-xfixes0 \
    libxcb-shape0 \
    libxcb-randr0 \
    libxcb-xinerama0 \
    && rm -rf /var/lib/apt/lists/*


# Redirects Python (ALSA) to the Pulse Socket
RUN echo "pcm.default type pulse\nctl.default type pulse" > /etc/asound.conf

RUN pip install --no-cache-dir \
    sounddevice soundfile scipy numpy python-dotenv deepgram-sdk PyQt6

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
WORKDIR /app
CMD ["/bin/bash"]