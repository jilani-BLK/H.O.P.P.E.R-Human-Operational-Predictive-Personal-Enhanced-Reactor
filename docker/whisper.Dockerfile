# Phase 3 - Dockerfiles

## 1. Whisper STT Service

FROM python:3.11-slim

WORKDIR /app

# System dependencies pour ffmpeg et compilation
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    ffmpeg \
    libavformat-dev \
    libavcodec-dev \
    libavdevice-dev \
    libavutil-dev \
    libavfilter-dev \
    libswscale-dev \
    libswresample-dev \
    pkg-config \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies (sans pyaudio et webrtcvad pour simplifier)
RUN pip install --no-cache-dir \
    faster-whisper==0.10.0 \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    python-multipart==0.0.6 \
    soundfile==0.12.1 \
    numpy==1.26.2

# Copy service code
COPY src/voice/whisper_server.py /app/server.py

# Download model on build (optional)
# RUN python -c "from faster_whisper import WhisperModel; WhisperModel('base', device='cpu', compute_type='int8')"

EXPOSE 5003

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "5003"]
