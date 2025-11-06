FROM python:3.11-slim

WORKDIR /app

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copie des requirements
COPY src/orchestrator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie de la structure complète nécessaire
COPY src/orchestrator/ ./
COPY src/filesystem/ ../filesystem/
COPY src/__init__.py ../

# Exposition du port CORRECT (5050, pas 5000)
EXPOSE 5050

# Variable d'environnement pour Python
ENV PYTHONPATH=/app/..

# Commande de démarrage
# Phase 1: main_phase1.py (commandes système uniquement)
# Phase 2: main_phase2.py (commandes système + conversations LLM)
# Phase 3+: main.py (version complète avec workflows)
CMD ["python", "main_phase2.py"]
