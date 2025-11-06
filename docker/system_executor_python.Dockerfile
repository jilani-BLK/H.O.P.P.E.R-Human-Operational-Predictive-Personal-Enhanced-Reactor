FROM python:3.11-slim

WORKDIR /app

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copie des requirements
COPY requirements.txt .
RUN pip install --no-cache-dir fastapi uvicorn pydantic pyyaml loguru

# Copie du code
COPY src/system_executor/server.py .
COPY config/command_whitelist.yaml /app/config/

# Exposition du port
EXPOSE 5002

# Variables d'environnement
ENV SYSTEM_EXECUTOR_PORT=5002
ENV PYTHONUNBUFFERED=1

# Démarrage du serveur
CMD ["python", "server.py"]
