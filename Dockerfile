FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    wget \
    curl \
    build-essential \
    portaudio19-dev \
    libportaudio2 \
    libportaudiocpp0 \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    sounddevice \
    soundfile \
    scipy \
    numpy \
    python-dotenv \
    deepgram-sdk

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

WORKDIR /app

CMD ["/bin/bash"]
