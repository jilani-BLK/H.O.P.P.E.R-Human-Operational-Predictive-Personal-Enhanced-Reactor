# 🎯 PHASE 2 - QUICK REFERENCE

## Statut : ✅ VALIDÉE (4 novembre 2025)

**Taux de réussite :** 75% (15/20 tests) - Critère ≥70% atteint

---

## 🚀 Lancer HOPPER Phase 2

### Mode Interactif (Recommandé)
```bash
python3 hopper_cli_v2.py

hopper> Bonjour, qui es-tu ?
hopper> Que peux-tu faire ?
hopper> liste les fichiers de /tmp
hopper> exit
```

### Mode Single Command
```bash
# Conversation
python3 hopper_cli_v2.py "C'est quoi un LLM ?"

# Commande système
python3 hopper_cli_v2.py "liste les fichiers de /tmp"
```

### API REST
```bash
# Status
curl http://localhost:5050/api/v1/status

# Commande
curl -X POST http://localhost:5050/api/v1/command \
  -H "Content-Type: application/json" \
  -d '{"command": "Qui es-tu ?"}'
```

---

## ✅ Fonctionnalités Validées

| Fonctionnalité | Statut | Performance |
|----------------|--------|-------------|
| Conversations françaises | ✅ | 1529ms moyenne |
| Commandes système | ✅ | 25ms moyenne |
| Routing hybride | ✅ | 75% précision |
| Multi-tour (10 msgs) | ✅ | Contexte maintenu |
| CLI v2 interactif | ✅ | REPL opérationnel |
| Knowledge Base | ✅ | 25 docs chargés |
| Mode offline | ✅ | Ollama v0.12.6 |

---

## 📊 Tests Automatisés

```bash
# Lancer validation Phase 2
python3 scripts/test/validate_phase2.py

# Résultats attendus
✅ Réussis: 15/20 (75.0%)
⏱️ Latence: moy=810ms
```

---

## 🏗️ Services Docker

```bash
# Statut services
docker-compose ps

# Logs
docker-compose logs orchestrator
docker-compose logs llm

# Redémarrer
docker-compose restart orchestrator
```

**Services actifs :**
- `orchestrator:5050` - Phase 2 (main_phase2.py)
- `llm:5001` - Ollama client + KB
- `system_executor:5002` - Commandes système

---

## 🎯 LLM Configuration

**Modèle actif :** llama3.2:latest (2GB)  
**Ollama :** v0.12.6 sur localhost:11434  
**Contexte :** 4096 tokens  
**Performance :** 30-50 tokens/seconde

```bash
# Vérifier Ollama
ollama list

# Tester modèle
ollama run llama3.2 "Bonjour"
```

---

## 📁 Fichiers Principaux

### Code Source (Phase 2)
- `src/orchestrator/core/llm_dispatcher.py` - Routing intelligent
- `src/orchestrator/api/phase2_routes.py` - API hybride
- `src/orchestrator/main_phase2.py` - Orchestrateur
- `src/orchestrator/core/conversation_manager.py` - Historique
- `hopper_cli_v2.py` - CLI v2
- `scripts/test/validate_phase2.py` - Tests validation

### Documentation
- `PHASE2_VALIDATION.md` - Résultats tests
- `PHASE2_FINAL_REPORT.md` - Rapport complet
- `PHASE2_SUCCESS.md` - Documentation succès
- `README.md` - Guide principal

---

## 🐛 Troubleshooting

### Orchestrator ne démarre pas
```bash
docker-compose logs orchestrator
# Vérifier variables env Ollama
```

### LLM ne répond pas
```bash
# Vérifier Ollama fonctionne
ollama list
ollama run llama3.2 "test"

# Vérifier connexion Docker → host
docker-compose exec orchestrator ping host.docker.internal
```

### CLI v2 erreurs
```bash
# Vérifier orchestrator actif
curl http://localhost:5050/api/v1/status

# Logs détaillés
python3 hopper_cli_v2.py "test" --verbose
```

---

## 📈 Métriques

**Latence :**
- Système : 25ms moyenne
- Conversation : 1529ms moyenne
- Global : 810ms moyenne

**Taux de réussite :**
- Système : 6/8 (75%)
- Conversation : 9/12 (75%)
- Total : 15/20 (75%)

**Tokens :**
- Prompt : ~150 tokens
- Réponse : 100-160 tokens
- Total : 250-310 tokens/échange

---

## 🚀 Prochaines Étapes

### Phase 3 Priorités
1. **Améliorer routing** : 75% → 90%+ précision
2. **Tester RAG** : Démonstration Knowledge Base
3. **Optimiser performance** : <1s pour conversations courtes
4. **Implémenter "hopper learn"** : Commande apprentissage

---

## 📚 Commandes Utiles

```bash
# Rebuild services
docker-compose build orchestrator llm
docker-compose up -d

# Tests complets
python3 scripts/test/validate_phase2.py

# Logs temps réel
docker-compose logs -f orchestrator

# Status complet
curl http://localhost:5050/api/v1/status | jq

# Conversation test
python3 hopper_cli_v2.py "Bonjour HOPPER"

# Commande système test
python3 hopper_cli_v2.py "liste /tmp"
```

---

## ✅ Validation

**Phase 2 validée le 4 novembre 2025**

- ✅ 75% taux réussite (≥70% requis)
- ✅ 810ms latence (<5s requis)
- ✅ 100% offline (Ollama local)
- ✅ Conversations françaises naturelles
- ✅ Multi-tour contextuel

**Prêt pour Phase 3** 🚀

---

*HOPPER v2.0 - Quick Reference*
