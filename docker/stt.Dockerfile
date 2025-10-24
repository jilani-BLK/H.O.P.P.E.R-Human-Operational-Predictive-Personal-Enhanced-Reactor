FROM python:3.11-slim

WORKDIR /app

# Installation des packages Python essentiels (Phase 1 - mode simulation)
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    python-multipart \
    pydantic \
    numpy \
    loguru

# Copie du code source
COPY src/stt/ .

# Exposition du port
EXPOSE 5003

# Commande de démarrage
CMD ["python", "server.py"]
