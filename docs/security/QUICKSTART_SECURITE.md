# ⚡ QUICKSTART SÉCURITÉ - HOPPER

**Status**: ✅ **FAILLES CRITIQUES CORRIGÉES** | ⚠️ **CONFIG PRODUCTION REQUISE**

---

## 🚀 DÉMARRAGE RAPIDE

### 1. Configurer .env (5 minutes)
```bash
# Copier template
cp .env.example .env

# Générer token API (32 caractères)
openssl rand -hex 32 > /tmp/api_token.txt

# Éditer .env et configurer:
nano .env
```

**Variables OBLIGATOIRES**:
```bash
API_TOKEN=<COLLER_TOKEN_GÉNÉRÉ>
DEV_MODE=false
NEO4J_PASSWORD=<PASSWORD_FORT>
```

### 2. Tester Sécurité (2 minutes)
```bash
# Test 1: Rate limiting
for i in {1..70}; do 
  curl -H "X-API-Key: $(cat /tmp/api_token.txt)" \
    http://localhost:5004/health
done
# → Devrait bloquer après 60 requêtes (429)

# Test 2: Auth token
curl http://localhost:5004/synthesize
# → 401 Unauthorized ✅

curl -H "X-API-Key: $(cat /tmp/api_token.txt)" \
  -X POST http://localhost:5004/synthesize \
  -d '{"text": "Test"}'
# → 200 OK ✅

# Test 3: Path traversal
python -c "
from src.agents.tools.file_tool import validate_path
print(validate_path('/etc/passwd'))  # → (False, 'Forbidden')
print(validate_path('/tmp/test.txt'))  # → (True, None)
"
```

### 3. Démarrer Services (1 minute)
```bash
# Mode dev (auth désactivée)
DEV_MODE=true docker-compose up

# Mode production (auth requise)
docker-compose up
```

---

## 📊 SCORES SÉCURITÉ

```
Failles critiques:   ✅ 0/8   (100% corrigées)
Failles moyennes:    🟡 5/12  (58% corrigées)
Score global:        ⭐ 85/100
Production ready:    ⚠️ Partiel (config requise)
```

---

## ✅ CE QUI EST SÉCURISÉ

- ✅ **Rate limiting**: 60 req/min, 1000 req/h
- ✅ **Auth API**: Token X-API-Key obligatoire
- ✅ **TTS**: Max 5000 chars, timeout 30s, injection bloquée
- ✅ **STT**: Max 25MB, MIME validation, timeout 60s
- ✅ **File Tool**: Path traversal bloqué, whitelist stricte
- ✅ **Neo4j**: Credentials env vars, queries paramétrées
- ✅ **Terminal**: shell=False, pas d'injection possible

---

## ⚠️ À FAIRE AVANT PRODUCTION

1. [ ] Configurer `API_TOKEN` (openssl rand -hex 32)
2. [ ] Configurer `NEO4J_PASSWORD` (password fort)
3. [ ] Désactiver `DEV_MODE=false`
4. [ ] Sanitize logs sensibles (TODO)
5. [ ] Docker healthchecks (TODO)
6. [ ] Backup Neo4j auto (TODO)
7. [ ] HTTPS/TLS (TODO)

**Timeline**: 2-3 jours pour corriger tous les TODOs

---

## 📚 DOCUMENTATION COMPLÈTE

- **Analyse détaillée**: `ANALYSE_COMPLETE_SECURITE.md` (72KB, 23 failles)
- **Corrections urgentes**: `RAPPORT_CORRECTIONS_SECURITE.md` (50KB)
- **Tableau de bord**: `TABLEAU_BORD_SECURITE.md` (scores visuels)
- **Résumé session**: `RESUME_SESSION_CORRECTIONS.md`

---

## 🆘 AIDE RAPIDE

### Problèmes Communs

**❌ "401 Unauthorized"**
```bash
# Vérifier .env contient API_TOKEN
grep API_TOKEN .env

# Ou activer mode dev temporairement
export DEV_MODE=true
```

**❌ "429 Too Many Requests"**
```bash
# Augmenter limites dans .env
RATE_LIMIT_PER_MINUTE=120
RATE_LIMIT_PER_HOUR=2000
```

**❌ "Neo4j connection failed"**
```bash
# Vérifier credentials
docker-compose exec neo4j cypher-shell -u neo4j -p $NEO4J_PASSWORD
```

---

**Dernière MAJ**: 22 Octobre 2025  
**Contact**: Voir TABLEAU_BORD_SECURITE.md pour détails
