# TTS Piper Service Dockerfile

FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
RUN pip install --no-cache-dir \
    piper-tts==1.2.0 \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0

# Download French voice model
RUN mkdir -p /app/models && \
    cd /app/models && \
    wget -q https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx && \
    wget -q https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx.json

# Copy service code
COPY src/voice/tts_server.py /app/server.py

EXPOSE 5004

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "5004"]
