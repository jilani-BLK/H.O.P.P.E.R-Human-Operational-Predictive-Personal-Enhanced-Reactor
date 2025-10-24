# Contribuer à HOPPER

Merci de votre intérêt pour contribuer à HOPPER ! Ce document vous guidera à travers le processus.

## 🎯 Comment Contribuer

### 1. Issues et Suggestions

- **Bugs**: Ouvrez une issue avec le label `bug`
- **Fonctionnalités**: Proposez avec le label `enhancement`
- **Questions**: Utilisez le label `question`

### 2. Pull Requests

#### Processus

1. **Fork** le projet
2. **Créez une branche**: `git checkout -b feature/ma-feature`
3. **Committez**: `git commit -m "feat: ajout de ma fonctionnalité"`
4. **Pushez**: `git push origin feature/ma-feature`
5. **Ouvrez une Pull Request**

#### Conventions de Commit

Nous utilisons [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: nouvelle fonctionnalité
fix: correction de bug
docs: documentation
style: formatage, point-virgules manquants, etc.
refactor: refactoring du code
test: ajout de tests
chore: tâches de maintenance
perf: amélioration de performance
```

Exemples:
```bash
git commit -m "feat(orchestrator): ajout du cache de réponses"
git commit -m "fix(llm): correction de la gestion du contexte"
git commit -m "docs: mise à jour du guide de démarrage"
```

## 📋 Checklist Pull Request

Avant de soumettre, vérifiez que:

- [ ] Le code est formaté (`make format`)
- [ ] Les tests passent (`make test`)
- [ ] La documentation est à jour
- [ ] Aucun secret n'est committé
- [ ] Le build Docker réussit (`make build`)
- [ ] Un health check est implémenté (nouveaux services)
- [ ] Des tests sont ajoutés (nouvelles fonctionnalités)

## 🎨 Standards de Code

### Python

```python
# Bon
def process_command(text: str, user_id: str) -> Dict[str, Any]:
    """
    Traite une commande utilisateur.
    
    Args:
        text: Texte de la commande
        user_id: Identifiant de l'utilisateur
        
    Returns:
        Résultat du traitement
    """
    result = {"success": True}
    return result

# Éviter
def process(t,u):
    r={"s":True}
    return r
```

**Règles**:
- Type hints partout
- Docstrings (Google style)
- snake_case pour fonctions/variables
- PascalCase pour classes
- UPPER_CASE pour constantes
- Longueur de ligne: 100 caractères max

### C

```c
// Bon
/**
 * Crée un fichier à l'emplacement spécifié
 * 
 * @param path Chemin du fichier
 * @return Résultat de l'exécution
 */
ExecutionResult create_file(const char *path) {
    ExecutionResult result;
    // ...
    return result;
}

// Éviter
ExecutionResult f(const char *p){return r;}
```

**Règles**:
- snake_case partout
- Commentaires Doxygen
- Vérifier tous les retours de fonctions
- Pas de magic numbers

## 🧪 Tests

### Tests Unitaires

```python
# tests/test_mon_module.py
import pytest
from src.mon_module import ma_fonction

def test_ma_fonction():
    """Test de ma_fonction"""
    result = ma_fonction("test")
    assert result == "expected"

def test_ma_fonction_erreur():
    """Test de gestion d'erreur"""
    with pytest.raises(ValueError):
        ma_fonction(None)
```

### Lancer les Tests

```bash
# Tous les tests
make test

# Un fichier spécifique
pytest tests/test_mon_module.py -v

# Avec couverture
pytest --cov=src tests/
```

## 📦 Ajouter un Nouveau Service

### 1. Créer le Service

```python
# src/mon_service/server.py
from fastapi import FastAPI
import os
from loguru import logger

app = FastAPI(title="Mon Service")

@app.on_event("startup")
async def startup():
    logger.info("🚀 Démarrage de Mon Service")

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("MON_SERVICE_PORT", 5007))
    uvicorn.run("server:app", host="0.0.0.0", port=port)
```

### 2. Créer le Dockerfile

```dockerfile
# docker/mon_service.Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN pip install fastapi uvicorn loguru

COPY src/mon_service/ .

EXPOSE 5007

CMD ["python", "server.py"]
```

### 3. Ajouter au docker-compose.yml

```yaml
  mon_service:
    build:
      context: .
      dockerfile: docker/mon_service.Dockerfile
    container_name: hopper-mon-service
    ports:
      - "5007:5007"
    networks:
      - hopper-network
```

### 4. Mettre à Jour la Documentation

- README.md (section Architecture)
- ARCHITECTURE.md (nouveau service)
- STRUCTURE.md (arborescence)

## 🔍 Review Process

Les Pull Requests seront reviewées selon ces critères:

1. **Fonctionnalité**: La PR fait ce qu'elle prétend faire
2. **Code Quality**: Respect des standards
3. **Tests**: Couverture suffisante
4. **Documentation**: Changements documentés
5. **Performance**: Pas de régression
6. **Sécurité**: Pas de vulnérabilités introduites

## 🌟 Bonnes Pratiques

### Git

```bash
# Commits atomiques
git add src/orchestrator/core/dispatcher.py
git commit -m "feat(dispatcher): ajout pattern email"

# Branches descriptives
git checkout -b fix/context-memory-leak
git checkout -b feature/iot-mqtt-connector
```

### Docker

```dockerfile
# Multi-stage builds pour taille réduite
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
COPY src/ /app/
CMD ["python", "server.py"]
```

### Python

```python
# Utiliser les context managers
with open(file_path, 'r') as f:
    content = f.read()

# Async/await pour I/O
async def fetch_data():
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
```

## 📞 Questions ?

- **Issues**: [GitHub Issues](https://github.com/jilani-BLK/H.O.P.P.E.R-Human-Operational-Predictive-Personal-Enhanced-Reactor/issues)
- **Documentation**: Dossier `docs/`
- **Discord**: (à venir)

## 📜 Code of Conduct

- Soyez respectueux
- Accueillez les nouveaux contributeurs
- Donnez des retours constructifs
- Concentrez-vous sur le code, pas sur la personne

## 🎁 Types de Contributions

Nous apprécions tous types de contributions:

- 🐛 Correction de bugs
- ✨ Nouvelles fonctionnalités
- 📝 Amélioration de la documentation
- 🎨 Amélioration du code
- 🧪 Ajout de tests
- 🌍 Traductions
- 💡 Idées et suggestions

## 🏆 Contributeurs

Liste des contributeurs sera ajoutée ici.

---

Merci de contribuer à HOPPER ! 🚀
