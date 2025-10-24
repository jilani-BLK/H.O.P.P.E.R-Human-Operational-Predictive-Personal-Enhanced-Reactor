# 🗣️ Guide de Communication Naturelle HOPPER

## Principe Fondamental

> **"Quand HOPPER fait quelque chose, il le dit de manière naturelle sans prompt"**

HOPPER doit être **transparent** dans toutes ses actions. Chaque décision importante, surtout celles qui touchent au système ou aux données de l'utilisateur, doit être :
1. **Annoncée clairement** en langage simple
2. **Justifiée** (pourquoi cette action ?)
3. **Approuvée** par l'utilisateur si nécessaire

## 🎯 Objectifs

### Transparence
- ✅ L'utilisateur comprend toujours ce que fait HOPPER
- ✅ Aucune action "boîte noire" ou obscure
- ✅ Les raisonnements sont expliqués pédagogiquement

### Confiance
- ✅ L'utilisateur fait confiance à HOPPER
- ✅ Les limites et incertitudes sont communiquées
- ✅ Les risques sont clairement énoncés

### Naturalité
- ✅ Communication fluide, comme avec un assistant humain
- ✅ Pas de jargon technique inutile
- ✅ Ton bienveillant et pédagogue

## 📖 Utilisation du Module

### Installation

```python
from src.communication import (
    ActionNarrator,
    narrate_file_scan,
    narrate_file_modification,
    narrate_system_command
)
```

### Exemple Basique

```python
# Créer le narrateur
narrator = ActionNarrator(
    verbose=True,  # Affiche toutes les actions
    auto_approve_low_risk=True  # Approuve automatiquement les actions sûres
)

# Narrer une action de sécurité
narrate_file_scan(narrator, "document.pdf")
# Output:
# ⚡ **Je vais vérifier le fichier 'document.pdf'**
#    Pourquoi : pour m'assurer qu'il ne contient aucune menace
#    Durée : quelques secondes
#    ✓ Bénéfices :
#       • Protection contre les malwares
#       • Sécurité de vos données
```

### Actions Nécessitant Approbation

```python
# Modification de fichier (nécessite approbation)
approved = narrate_file_modification(
    narrator,
    filepath="important.docx",
    operation="supprimer",
    purpose="nettoyer les fichiers temporaires",
    requires_approval=True
)

if approved:
    # Exécuter l'action
    os.remove("important.docx")
else:
    print("Action annulée par l'utilisateur")
```

### Partage de Raisonnement

```python
narrator.share_reasoning(
    question="Comment résoudre cette erreur Python ?",
    steps=[
        "Lire le message d'erreur (TypeError ligne 42)",
        "Identifier la variable problématique (result)",
        "Vérifier le type attendu vs type actuel",
        "Ajouter une conversion str() appropriée"
    ],
    conclusion="Ajouter 'str(result)' ligne 42 résoudra l'erreur"
)
```

### Communication des Incertitudes

```python
narrator.explain_uncertainty(
    topic="cette question juridique",
    confidence=0.65,
    limitations=[
        "Mes informations datent de 2023",
        "Le droit peut varier selon votre région",
        "Je recommande de consulter un avocat professionnel"
    ]
)
```

## 🎨 Exemples de Communication Naturelle

### ❌ Mauvais (Technique et Opaque)
```
Executing antivirus scan...
Command: /usr/bin/clamav scan file.pdf
Exit code: 0
```

### ✅ Bon (Naturel et Transparent)
```
ℹ️  Je vais vérifier ce fichier PDF pour m'assurer qu'il ne présente aucun danger.
   Pourquoi : Votre sécurité est ma priorité
   Durée : quelques secondes
   
✓ Scan terminé : Aucune menace détectée !
```

---

### ❌ Mauvais (Jargon Technique)
```
Initiating RAG pipeline:
1. Embedding query with sentence-transformers
2. FAISS similarity search (k=5)
3. Context injection in prompt
4. LLM inference with llama.cpp
```

### ✅ Bon (Pédagogique)
```
💡 Pour répondre à votre question, je vais d'abord chercher dans ma base
   de connaissances les informations pertinentes, puis les analyser pour
   vous donner la meilleure réponse possible.
```

---

### ❌ Mauvais (Silencieux)
```python
# Code exécute silencieusement
os.system("rm -rf /tmp/cache")
```

### ✅ Bon (Transparent)
```python
# Narrer avant d'exécuter
narrate_system_command(
    narrator,
    command="rm -rf /tmp/cache",
    purpose="nettoyer le cache temporaire pour libérer de l'espace"
)
# Attendre approbation
os.system("rm -rf /tmp/cache")
```

## 🔧 Intégration dans HOPPER

### Dans l'Orchestrateur

```python
# src/orchestrator/main.py
from src.communication import ActionNarrator

class Orchestrator:
    def __init__(self):
        self.narrator = ActionNarrator(verbose=True)
        # ...
    
    async def process_command(self, user_id: str, command: str):
        # Détecter intention
        intent = await self.dispatcher.detect_intent(command)
        
        # Narrer l'action avant exécution
        if intent == "system_command":
            approved = narrate_system_command(
                self.narrator,
                command=command,
                purpose="exécuter votre demande"
            )
            
            if not approved:
                return {"message": "Action annulée"}
        
        # Exécuter
        result = await self.dispatcher.dispatch(intent, command)
        return result
```

### Dans le Service Antivirus

```python
# src/security/antivirus.py
from src.communication import narrate_file_scan

class AntivirusService:
    def __init__(self, narrator: ActionNarrator):
        self.narrator = narrator
    
    async def scan_file(self, filepath: str):
        # Narrer l'action
        narrate_file_scan(self.narrator, filepath)
        
        # Exécuter le scan
        result = await self._run_clamav(filepath)
        
        # Expliquer le résultat
        if result.is_clean:
            print(f"✅ Scan terminé : Aucune menace détectée !")
        else:
            print(f"⚠️  Menace détectée : {result.threat_name}")
            print(f"   Je recommande de supprimer ce fichier.")
        
        return result
```

### Dans le LLM Engine

```python
# src/llm_engine/main.py
class LLMEngine:
    def __init__(self, narrator: ActionNarrator):
        self.narrator = narrator
    
    async def generate(self, prompt: str):
        # Partager le plan avant exécution
        self.narrator.share_reasoning(
            question=prompt,
            steps=[
                "Analyser votre question",
                "Chercher dans ma base de connaissances",
                "Construire une réponse pertinente",
                "Vérifier la cohérence"
            ],
            conclusion="Je vais générer une réponse basée sur ces étapes"
        )
        
        # Générer
        response = await self.model.generate(prompt)
        return response
```

## 📋 Checklist Communication Naturelle

### Avant d'Implémenter une Nouvelle Fonctionnalité

- [ ] L'action est-elle clairement expliquée en langage simple ?
- [ ] La raison (pourquoi) est-elle communiquée ?
- [ ] Les risques éventuels sont-ils mentionnés ?
- [ ] Une approbation est-elle demandée si nécessaire ?
- [ ] Les incertitudes sont-elles transparentes ?
- [ ] Le vocabulaire est-il accessible (pas de jargon) ?
- [ ] Le ton est-il bienveillant et pédagogue ?

### Types d'Actions Nécessitant Narration

| Type | Exemples | Approbation Requise ? |
|------|----------|----------------------|
| **Sécurité** | Scan antivirus, vérification fichier | Non (info) |
| **Modification Fichier** | Édition, suppression, déplacement | **Oui** |
| **Commande Système** | rm, chmod, installation paquet | **Oui** |
| **Apprentissage** | Enregistrement préférences | Non |
| **Recherche** | Requête base de connaissances | Non |
| **Raisonnement** | Planification multi-étapes | Non (info) |
| **Communication** | Envoi email, message | **Oui** |

## 🎯 Niveaux d'Urgence

```python
Urgency.INFO       # ℹ️  Simple information
Urgency.LOW        # 💡 Peut attendre
Urgency.MEDIUM     # ⚡ Important
Urgency.HIGH       # ⚠️  Critique
Urgency.BLOCKING   # 🛑 Nécessite approbation immédiate
```

## 🔍 Exemples Contextuels

### Contexte: Analyse de Document

```python
# ❌ Mauvais
print("Analyzing document...")
result = analyze(doc)
print(f"Done. Score: {result.score}")

# ✅ Bon
narrator.share_reasoning(
    question="Comment analyser ce document ?",
    steps=[
        "Extraire le texte du PDF",
        "Identifier les sections principales",
        "Analyser le ton et le style",
        "Détecter les points clés"
    ],
    conclusion="Voici mon analyse détaillée..."
)
```

### Contexte: Détection de Malware

```python
# ❌ Mauvais (Silencieux et effrayant)
if is_malware(file):
    delete(file)

# ✅ Bon (Transparent et rassurant)
if is_malware(file):
    print(f"⚠️  J'ai détecté un fichier potentiellement dangereux : {file}")
    print(f"   Menace : {threat_type}")
    print(f"   ")
    print(f"   Je recommande de le supprimer pour votre sécurité.")
    
    approved = narrator._request_approval(...)
    if approved:
        delete(file)
        print(f"✅ Fichier supprimé avec succès. Votre système est sécurisé.")
```

### Contexte: Limitation de Connaissances

```python
# ❌ Mauvais (Fausse confiance)
return "La réponse est définitivement X"

# ✅ Bon (Honnêteté)
narrator.explain_uncertainty(
    topic="cette question spécialisée",
    confidence=0.7,
    limitations=[
        "Ce sujet évolue rapidement",
        "Mes données datent de 2023",
        "Je recommande de vérifier auprès d'une source officielle"
    ]
)
return "Selon mes connaissances, X semble être la réponse, mais..."
```

## 📚 Ressources

- **Code**: `src/communication/action_narrator.py`
- **Tests**: `tests/test_communication.py` (à créer)
- **Démo**: `python -m src.communication.action_narrator`

## 🚀 Roadmap

### Phase 1 (Actuelle)
- [x] Module ActionNarrator basique
- [ ] Intégration dans Orchestrateur
- [ ] Intégration dans Services (Antivirus, System)
- [ ] Tests unitaires

### Phase 2
- [ ] Support mode asynchrone (callbacks web)
- [ ] Personnalisation niveau verbosité par utilisateur
- [ ] Historique actions consultable
- [ ] Statistiques narration

### Phase 3
- [ ] Mode audio (TTS des narrations)
- [ ] Traduction multilingue
- [ ] Apprentissage préférences utilisateur
- [ ] Dashboard visualisation actions

---

**Principe à retenir**: Chaque action importante de HOPPER doit être aussi transparente qu'un assistant humain expliquant ce qu'il fait. L'utilisateur ne doit jamais se demander "Qu'est-ce qu'il fait ?!" 🤔

**Objectif**: Construire la confiance par la transparence. 🤝
