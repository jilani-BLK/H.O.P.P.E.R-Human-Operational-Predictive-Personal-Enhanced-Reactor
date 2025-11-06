# Voice Authentication Service Dockerfile

FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    git \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
RUN pip install --no-cache-dir \
    speechbrain==0.5.16 \
    torchaudio==2.1.0 \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    python-multipart==0.0.6 \
    numpy==1.24.3

# Copy service code
COPY src/voice/auth_voice_server.py /app/server.py

# Create profiles directory
RUN mkdir -p /app/profiles

EXPOSE 5007

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "5007"]
