# HOPPER - Optimisations Performance (Quick Wins)

**Date**: 22 Octobre 2025  
**Objectif**: Améliorer latence LLM de 40% (11s → 6-7s)

## 🎯 Optimisations à Appliquer

### 1. Augmenter GPU Layers (PRIORITÉ HAUTE)

**Changement**:
```bash
# .env
LLM_N_GPU_LAYERS=1  →  LLM_N_GPU_LAYERS=10
```

**Impact attendu**:
- Latence: -30-40%
- Utilisation GPU Metal: Optimale pour M3 Max
- Stabilité: À tester (actuellement 1 layer = très stable)

**Commandes**:
```bash
# 1. Backup configuration actuelle
cp .env .env.backup

# 2. Modifier GPU layers
sed -i '' 's/LLM_N_GPU_LAYERS=1/LLM_N_GPU_LAYERS=10/' .env

# 3. Redémarrer service LLM
docker compose restart llm

# 4. Attendre chargement modèle (~30s)
sleep 30

# 5. Tester performance
time curl -s -X POST http://localhost:8000/command \
  -H "Content-Type: application/json" \
  -d '{"text": "Explique Python en 2 phrases"}'
```

---

### 2. Réduire Context Window (PRIORITÉ MOYENNE)

**Changement**:
```bash
# .env
LLM_CONTEXT_SIZE=4096  →  LLM_CONTEXT_SIZE=2048
```

**Impact attendu**:
- Latence: -10-15%
- Mémoire: -500 MB RAM
- Historique conversation: 10 → 5 échanges (acceptable)

**Commandes**:
```bash
# Modifier context size
sed -i '' 's/LLM_CONTEXT_SIZE=4096/LLM_CONTEXT_SIZE=2048/' .env

# Redémarrer
docker compose restart llm
```

---

### 3. Truncation Historique (PRIORITÉ MOYENNE)

**Changement**:
```python
# src/orchestrator/core/prompt_builder.py
max_history_tokens=2048  →  max_history_tokens=1024
```

**Impact attendu**:
- Taille prompts: -15-20%
- Latence: -5-10%

---

### 4. Cache Embeddings KB (PRIORITÉ BASSE)

**Code à ajouter**:
```python
# src/llm_engine/knowledge_base.py
from functools import lru_cache

@lru_cache(maxsize=128)
def _encode_cached(self, text: str):
    return self.encoder.encode([text])[0]
```

**Impact attendu**:
- Recherche KB: 50ms → <10ms
- Mémoire: +10 MB

---

## 📊 Plan d'Exécution

**Phase 1 - Immédiat (5 minutes)**:
1. ✅ GPU Layers: 1 → 10
2. ✅ Redémarrage LLM service
3. ✅ Test latence

**Phase 2 - Optionnel (10 minutes)**:
4. Context Window: 4096 → 2048
5. Test stabilité
6. Mesure amélioration

**Validation**:
```bash
# Benchmark avant optimisation
# Moyenne: 11s pour 55 tokens

# Benchmark après optimisation
# Objectif: <7s pour 55 tokens
```

---

## 🔄 Rollback si Problème

```bash
# Restaurer configuration d'origine
cp .env.backup .env
docker compose restart llm

# Vérifier santé
curl http://localhost:5001/health
```

---

**Gain total attendu**: Latence 11s → **6-7s** (~40% amélioration)
