FROM python:3.11-slim

WORKDIR /app

# Installation des dépendances système pour macOS apps
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Installation des dépendances Python
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    requests \
    aiohttp \
    httpx \
    python-dotenv \
    pydantic \
    sqlalchemy \
    python-multipart \
    loguru \
    psutil

# Copie du code source avec structure de package
COPY src/connectors/ /app/

# Créer __init__.py vide pour le module parent si imports relatifs
RUN touch /app/__init__.py

# Exposition du port
EXPOSE 5006

# Commande de démarrage
CMD ["python", "server.py"]
