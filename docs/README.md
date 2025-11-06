# Documentation HOPPER

## 📚 Documentation par Phase

### Phases Implémentées
- **[PHASE1.md](PHASE1.md)** - Infrastructure de Base & LLM Core ✅
- **[PHASE2.md](PHASE2.md)** - Concrétisation & Production-Ready ✅
- **[PHASE3.md](PHASE3.md)** - Fonctionnalités Vocales ✅
- **[PHASE4.md](PHASE4.md)** - Intelligence & Apprentissage 📋

## 🔧 Guides Techniques

- **[QUICKSTART.md](QUICKSTART.md)** - Démarrage rapide
- **[USER_GUIDE.md](USER_GUIDE.md)** - Guide utilisateur
- **[DEV_GUIDE.md](DEV_GUIDE.md)** - Guide développeur
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Architecture système
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Développement & contribution
- **[OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md)** - Optimisations

## 🚀 Démarrage Rapide

```bash
# Cloner le projet
git clone https://github.com/jilani-BLK/H.O.P.P.E.R.git
cd HOPPER

# Lancer tous les services
docker-compose up -d

# Vérifier statut
docker ps

# Utiliser la CLI
hopper "Quelle est la capitale de la France?"
```

## 📊 État Actuel

| Phase | Status | Services | Fonctionnalités |
|-------|--------|----------|-----------------|
| Phase 1 | ✅ | orchestrator, llm, system_executor | LLM de base, commandes système |
| Phase 2 | ✅ | + qdrant, CLI | Base vectorielle, CLI native |
| Phase 3 | ✅ | + whisper, tts_piper | Pipeline vocal complet |
| Phase 4 | 📋 | + fine-tuning | Apprentissage, règles |

## 🔗 Liens Utiles

- **API Docs**: http://localhost:5050/docs
- **Qdrant UI**: http://localhost:6333/dashboard
- **Repository**: https://github.com/jilani-BLK/H.O.P.P.E.R

---

**Version**: 3.0  
**Dernière MAJ**: 5 Novembre 2025
