FROM gcc:12-bullseye

WORKDIR /app

# Installation des dépendances pour serveur HTTP léger
RUN apt-get update && apt-get install -y \
    libmicrohttpd-dev \
    libcjson-dev \
    make \
    && rm -rf /var/lib/apt/lists/*

# Copie du code source
COPY src/system_executor/ .

# Compilation
RUN make clean && make

# Exposition du port
EXPOSE 5002

# Commande de démarrage
CMD ["/app/build/system_executor"]
