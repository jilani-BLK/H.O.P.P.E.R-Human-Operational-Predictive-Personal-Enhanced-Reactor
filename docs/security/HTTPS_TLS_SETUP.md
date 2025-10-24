# 🔒 HTTPS/TLS Configuration - HOPPER Production

**Objectif**: Sécuriser les communications avec certificats SSL/TLS

---

## 📋 Prérequis

- Nom de domaine pointant vers le serveur (ex: `hopper.example.com`)
- Serveur accessible depuis Internet (ports 80 et 443 ouverts)
- Docker et docker-compose installés

---

## 🚀 Option 1: HTTPS avec Nginx + Let's Encrypt (Recommandé)

### 1. Créer nginx.conf

```nginx
# /Users/jilani/Projet/HOPPER/nginx/nginx.conf

# Redirection HTTP -> HTTPS
server {
    listen 80;
    server_name hopper.example.com;
    
    # Let's Encrypt challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    # Redirection forcée HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS avec reverse proxy
server {
    listen 443 ssl http2;
    server_name hopper.example.com;
    
    # Certificats SSL
    ssl_certificate /etc/letsencrypt/live/hopper.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/hopper.example.com/privkey.pem;
    
    # Options SSL recommandées
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Headers de sécurité
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Reverse proxy vers Orchestrator
    location / {
        proxy_pass http://orchestrator:5050;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (si nécessaire)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # TTS service
    location /tts/ {
        proxy_pass http://tts:5004/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # STT service
    location /stt/ {
        proxy_pass http://stt:5003/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 25M;  # Pour uploads audio
    }
}
```

### 2. Ajouter nginx et certbot au docker-compose.yml

```yaml
services:
  # ... services existants ...
  
  nginx:
    image: nginx:alpine
    container_name: hopper-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - certbot_conf:/etc/letsencrypt:ro
      - certbot_www:/var/www/certbot:ro
    networks:
      - hopper-network
    depends_on:
      - orchestrator
      - tts
      - stt
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "nginx", "-t"]
      interval: 30s
      timeout: 10s
      retries: 3
  
  certbot:
    image: certbot/certbot
    container_name: hopper-certbot
    volumes:
      - certbot_conf:/etc/letsencrypt
      - certbot_www:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"
    networks:
      - hopper-network

volumes:
  # ... volumes existants ...
  certbot_conf:
  certbot_www:
```

### 3. Obtenir certificat Let's Encrypt

```bash
# Créer répertoire nginx
mkdir -p nginx

# Démarrer nginx temporairement (HTTP seulement)
docker-compose up -d nginx

# Obtenir certificat
docker-compose run --rm certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email admin@example.com \
  --agree-tos \
  --no-eff-email \
  -d hopper.example.com

# Redémarrer nginx avec HTTPS
docker-compose restart nginx
```

### 4. Renouvellement automatique

Le container certbot renouvelle automatiquement les certificats tous les 12h.

**Test manuel**:
```bash
docker-compose run --rm certbot renew --dry-run
```

---

## 🔧 Option 2: HTTPS avec Traefik (Alternative)

### 1. Créer traefik.yml

```yaml
# /Users/jilani/Projet/HOPPER/traefik/traefik.yml

entryPoints:
  web:
    address: ":80"
    http:
      redirections:
        entryPoint:
          to: websecure
          scheme: https
  
  websecure:
    address: ":443"

certificatesResolvers:
  letsencrypt:
    acme:
      email: admin@example.com
      storage: /letsencrypt/acme.json
      httpChallenge:
        entryPoint: web

providers:
  docker:
    exposedByDefault: false
```

### 2. Ajouter Traefik au docker-compose.yml

```yaml
services:
  traefik:
    image: traefik:v2.10
    container_name: hopper-traefik
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
      - "--certificatesresolvers.letsencrypt.acme.email=admin@example.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
      - "8080:8080"  # Dashboard
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - traefik_letsencrypt:/letsencrypt
    networks:
      - hopper-network
    restart: unless-stopped
  
  orchestrator:
    # ... config existante ...
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.orchestrator.rule=Host(`hopper.example.com`)"
      - "traefik.http.routers.orchestrator.entrypoints=websecure"
      - "traefik.http.routers.orchestrator.tls.certresolver=letsencrypt"
      - "traefik.http.services.orchestrator.loadbalancer.server.port=5050"

volumes:
  traefik_letsencrypt:
```

---

## 🧪 Tests HTTPS

### Test 1: Certificat valide
```bash
# Vérifier certificat SSL
openssl s_client -connect hopper.example.com:443 -servername hopper.example.com < /dev/null

# Vérifier expiration
echo | openssl s_client -connect hopper.example.com:443 2>/dev/null | \
  openssl x509 -noout -dates
```

### Test 2: Redirection HTTP -> HTTPS
```bash
curl -I http://hopper.example.com
# → Devrait retourner 301 avec Location: https://
```

### Test 3: Headers de sécurité
```bash
curl -I https://hopper.example.com
# → Vérifier présence de:
#   Strict-Transport-Security
#   X-Frame-Options
#   X-Content-Type-Options
```

### Test 4: Grade SSL
- **SSL Labs**: https://www.ssllabs.com/ssltest/
- **Mozilla Observatory**: https://observatory.mozilla.org/

**Target**: Grade A minimum

---

## 🔧 Dépannage

### Problème 1: "Connection refused"
```bash
# Vérifier ports ouverts
sudo netstat -tlnp | grep -E ':(80|443)'

# Vérifier firewall
sudo ufw status
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### Problème 2: "Certificate not found"
```bash
# Vérifier certificats
docker-compose exec nginx ls -la /etc/letsencrypt/live/

# Re-générer
docker-compose run --rm certbot certonly --force-renewal \
  --webroot --webroot-path=/var/www/certbot \
  -d hopper.example.com
```

### Problème 3: "Too many requests" (Let's Encrypt)
- Limite: 5 certificats/semaine/domaine
- Solution: Utiliser staging pendant tests
```bash
docker-compose run --rm certbot certonly \
  --staging \
  --webroot --webroot-path=/var/www/certbot \
  -d hopper.example.com
```

---

## 📋 Checklist Production

- [ ] Nom de domaine configuré (DNS A record)
- [ ] Ports 80 et 443 ouverts dans firewall
- [ ] Nginx/Traefik déployé avec reverse proxy
- [ ] Certificat Let's Encrypt obtenu
- [ ] Redirection HTTP -> HTTPS active
- [ ] Headers de sécurité configurés
- [ ] Renouvellement automatique testé
- [ ] Grade SSL: A ou A+ (SSL Labs)
- [ ] HSTS activé (Strict-Transport-Security)
- [ ] Tests validés (curl, openssl)

---

## 📚 Ressources

- **Let's Encrypt**: https://letsencrypt.org/docs/
- **Nginx SSL Config**: https://ssl-config.mozilla.org/
- **Traefik Docs**: https://doc.traefik.io/traefik/https/acme/
- **SSL Labs Test**: https://www.ssllabs.com/ssltest/
- **Mozilla Observatory**: https://observatory.mozilla.org/

---

**Dernière MAJ**: 22 Octobre 2025  
**Status**: Guide complet HTTPS/TLS production
