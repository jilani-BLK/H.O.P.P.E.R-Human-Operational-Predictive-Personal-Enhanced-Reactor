FROM python:3.11-slim

WORKDIR /app

# Installation des packages Python essentiels seulement (Phase 1 - mode simulation)
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    pydantic \
    numpy \
    loguru \
    python-multipart

# Copie du code source
COPY src/auth/ .

# Exposition du port
EXPOSE 5005

# Commande de démarrage
CMD ["python", "server.py"]
