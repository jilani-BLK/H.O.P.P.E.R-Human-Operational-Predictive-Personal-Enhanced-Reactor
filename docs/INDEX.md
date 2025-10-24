# 📚 HOPPER - Index de Documentation

Bienvenue dans la documentation du projet HOPPER ! Cette page vous guide vers toutes les ressources disponibles.

## 🗂️ Structure de la Documentation

```
docs/
├── INDEX.md (ce fichier)
├── architecture/     # Architecture et conception
├── guides/          # Guides d'utilisation
├── phases/          # Documentation des phases de développement
├── reports/         # Rapports d'analyse et de progression
└── troubleshooting/ # Guides de dépannage
```

## 🚀 Démarrage Rapide

### Pour les nouveaux utilisateurs
1. **[README.md](../README.md)** - Vue d'ensemble du projet
2. **[QUICK_REFERENCE.md](../QUICK_REFERENCE.md)** - Référence rapide des commandes
3. **[CONTRIBUTING.md](../CONTRIBUTING.md)** - Guide de contribution

### Installation
- **[scripts/install/install.sh](../scripts/install/install.sh)** - Installation complète
- **[scripts/install/setup_rag_minimal.sh](../scripts/install/setup_rag_minimal.sh)** - Installation minimale RAG
- **[scripts/install/setup_rag_advanced.sh](../scripts/install/setup_rag_advanced.sh)** - Installation RAG avancée

## 📖 Documentation par Thème

### Architecture & Conception

| Document | Description |
|----------|-------------|
| **[reports/ARCHITECTURE_ANALYSIS.md](reports/ARCHITECTURE_ANALYSIS.md)** | Analyse complète de l'architecture (Oct 2024) |
| Architecture détaillée | Voir `architecture/` pour les diagrammes et specs |

### Rapports de Progression

| Document | Date | Sujet |
|----------|------|-------|
| **[reports/ADAPTIVE_LEARNING_SUMMARY.md](reports/ADAPTIVE_LEARNING_SUMMARY.md)** | Oct 2024 | Résumé du système d'apprentissage adaptatif |
| **[reports/VALIDATION_FINALE.md](reports/VALIDATION_FINALE.md)** | Oct 2024 | Validation finale Phase 2 |
| **[reports/RAPPORT_TESTS_COMPLET.md](reports/RAPPORT_TESTS_COMPLET.md)** | Oct 2024 | Rapport complet des tests |
| **[reports/PERFORMANCE_ANALYSIS.md](reports/PERFORMANCE_ANALYSIS.md)** | Oct 2024 | Analyse de performance (26 KB) |
| **[reports/TESTS_CONCRETS_RESULTATS.md](reports/TESTS_CONCRETS_RESULTATS.md)** | Oct 2024 | Résultats tests concrets |
| **[reports/OPTIMIZATION_RESULTS.md](reports/OPTIMIZATION_RESULTS.md)** | Oct 2024 | Résultats optimisations |

### Corrections & Résolution de Problèmes

| Document | Description |
|----------|-------------|
| **[reports/RESOLUTION_143_ERREURS.md](reports/RESOLUTION_143_ERREURS.md)** | Résolution de 143 erreurs Python |
| **[reports/CORRECTIONS_APPLIQUEES.md](reports/CORRECTIONS_APPLIQUEES.md)** | Corrections appliquées |
| **[reports/INSTRUCTIONS_145.md](reports/INSTRUCTIONS_145.md)** | Instructions corrections 145 |
| **[reports/PROBLEMES_IDENTIFIES.md](reports/PROBLEMES_IDENTIFIES.md)** | Problèmes identifiés |

### Guides de Dépannage

| Document | Description |
|----------|-------------|
| **[troubleshooting/TROUBLESHOOTING.md](troubleshooting/TROUBLESHOOTING.md)** | Guide général de dépannage |
| **[troubleshooting/PYTHON_ERRORS_GUIDE.md](troubleshooting/PYTHON_ERRORS_GUIDE.md)** | Guide erreurs Python |

## 🔧 Scripts Utiles

### Déploiement
```bash
scripts/deploy/start_orchestrator.sh  # Démarrer l'orchestrateur
scripts/deploy/start-phase1.sh        # Démarrer Phase 1
scripts/deploy/apply_port_change.sh   # Appliquer changements ports
```

### Tests
```bash
scripts/test/run_complete_tests.sh    # Tests complets
scripts/test/test-standalone.sh       # Tests standalone
scripts/test/validate_phase1.py       # Valider Phase 1
scripts/test/validate_phase3.py       # Valider Phase 3
```

### Monitoring
```bash
scripts/monitoring/check_errors.sh    # Vérifier erreurs
scripts/monitoring/diagnose_port.sh   # Diagnostiquer ports
scripts/monitor.sh                    # Monitoring général
```

## 📊 Statistiques du Projet

- **Langage**: Python 3.11+
- **Lignes de code**: ~50,000
- **Modules**: 15
- **Services**: 7 (architecture microservices)
- **Phase actuelle**: Phase 2 (95% complétée)
- **Tests**: 264+ fichiers Python

## 🎯 Prochaines Étapes

1. **Phase 3**: Intégration avancée et optimisations
2. **Documentation**: Compléter guides utilisateur
3. **Tests**: Améliorer couverture de tests

## 📦 Data & Modèles

- **[data/models/README.md](../data/models/README.md)** - Instructions téléchargement modèles LLM
- Les modèles (4.1 GB) ne sont pas versionnés dans Git
- Utiliser Docker volumes pour la gestion des modèles

## 🐛 Signaler un Problème

1. Consulter **[troubleshooting/TROUBLESHOOTING.md](troubleshooting/TROUBLESHOOTING.md)**
2. Vérifier les **[issues GitHub](https://github.com/jilani-BLK/H.O.P.P.E.R-Human-Operational-Predictive-Personal-Enhanced-Reactor/issues)**
3. Créer une nouvelle issue si nécessaire

## 📝 Changelog

Voir **[CHANGELOG.md](../CHANGELOG.md)** pour l'historique complet des modifications.

## 📄 Licence

Voir **[LICENSE](../LICENSE)** pour les détails de licence.

---

**Dernière mise à jour**: 24 octobre 2024  
**Version**: 1.0.0 (Phase 2)  
**Maintenu par**: Équipe HOPPER
