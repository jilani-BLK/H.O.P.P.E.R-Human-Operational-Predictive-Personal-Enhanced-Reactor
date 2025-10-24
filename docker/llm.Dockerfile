FROM python:3.11-slim

WORKDIR /app

# Installation des dépendances système pour compilation C++
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Installation de llama.cpp et ses bindings Python
RUN pip install --no-cache-dir \
    llama-cpp-python \
    fastapi \
    uvicorn \
    pydantic \
    numpy \
    sentence-transformers \
    faiss-cpu \
    loguru \
    pyyaml \
    httpx

# Copie du code source
COPY src/llm_engine/ .

# Exposition du port
EXPOSE 5001

# Commande de démarrage
CMD ["python", "server.py"]
