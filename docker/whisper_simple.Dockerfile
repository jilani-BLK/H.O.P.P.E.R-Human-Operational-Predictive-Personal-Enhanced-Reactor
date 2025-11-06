# Whisper STT Service - Version Simple avec openai-whisper

FROM python:3.11-slim

WORKDIR /app

# Dépendances système minimales
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies - openai-whisper (beaucoup plus simple que faster-whisper)
RUN pip install --no-cache-dir \
    openai-whisper==20231117 \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    python-multipart==0.0.6

# Copy simple server
COPY src/voice/whisper_server_simple.py /app/server.py

# Download model on build (optional - commenté pour build rapide)
# RUN python -c "import whisper; whisper.load_model('base')"

EXPOSE 5003

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "5003"]
