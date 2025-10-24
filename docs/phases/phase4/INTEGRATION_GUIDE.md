# Phase 4 - Guide d'Intégration Learning

## 📋 Vue d'Ensemble

La Phase 4 ajoute l'intelligence et l'apprentissage à HOPPER via 3 composants principaux :

1. **Gestionnaire de Préférences** - Configuration utilisateur personnalisée
2. **Collecteur de Conversations** - Données pour fine-tuning
3. **Gestionnaire de Feedback** - Satisfaction et amélioration continue

## 🚀 Démarrage Rapide

### 1. Importer les Composants

```python
from src.learning.preferences.preferences_manager import PreferencesManager
from src.learning.fine_tuning.conversation_collector import ConversationCollector
from src.learning.feedback.feedback_manager import FeedbackManager
from src.learning.integration.learning_middleware import LearningMiddleware
```

### 2. Initialiser dans l'Orchestrateur

```python
# Dans src/orchestrator/app.py
from src.learning.integration.learning_middleware import LearningMiddleware

app = Flask(__name__)
learning = LearningMiddleware()

@app.before_request
def before_request():
    from flask import g
    g.learning_middleware = learning
    learning.before_request()

@app.after_request  
def after_request(response):
    return learning.after_request(response)
```

### 3. Collecter les Interactions

```python
@app.route('/api/chat', methods=['POST'])
def chat():
    from flask import request, g
    data = request.get_json()
    user_input = data.get('message')
    
    # Traiter la requête
    response = process_message(user_input)
    
    # Collecter l'interaction
    learning.collect_interaction(
        user_input=user_input,
        assistant_response=response,
        intent=detect_intent(user_input)
    )
    
    return {'response': response}
```

### 4. Gérer le Feedback

```python
@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    from flask import request
    data = request.get_json()
    
    learning.add_feedback(
        score=data.get('score'),  # 1-5
        comment=data.get('comment')
    )
    
    # Vérifier si demander feedback
    if learning.should_request_feedback():
        return {
            'message': 'Feedback enregistré',
            'request_feedback': True,
            'prompt': learning.get_feedback_prompt()
        }
    
    return {'message': 'Feedback enregistré'}
```

## 🎯 Fonctionnalités Principales

### Mode Nuit

Le mode nuit (22h-7h) bloque automatiquement les notifications non urgentes :

```python
# Vérifier si notification autorisée
if learning.should_notify(priority="medium", content="message"):
    send_notification(message)
```

### Verbosité Adaptative

Adapter la longueur des réponses selon les préférences :

```python
verbosity = learning.get_verbosity()  # concise | balanced | detailed

if verbosity == "concise":
    response = generate_short_response(input)
elif verbosity == "detailed":
    response = generate_long_response(input)
else:
    response = generate_balanced_response(input)
```

### Confirmations Sécurisées

Demander confirmation pour les commandes sensibles :

```python
command = "delete important_file.txt"

if learning.requires_confirmation(command):
    return {
        'requires_confirmation': True,
        'command': command,
        'message': 'Cette commande nécessite confirmation'
    }
```

## 📊 Statistiques et Analyse

### Résumé Quotidien

```python
stats = learning.get_daily_stats()
print(f"Satisfaction moyenne: {stats['avg_score']}/5")
print(f"Taux de satisfaction: {stats['satisfaction_rate']}%")
```

### Export pour Fine-Tuning

```python
# Exporter conversations avec satisfaction >= 3.0
dataset_path = learning.export_training_data(min_satisfaction=3.0)
print(f"Dataset créé: {dataset_path}")
```

## 🔧 Configuration

### Fichier: `config/user_preferences/default_preferences.yaml`

```yaml
# Mode nuit
modes:
  night_mode:
    enabled: true
    start_time: "22:00"
    end_time: "07:00"

# Contacts VIP (notifs même en mode nuit)
notifications:
  vip_contacts:
    - "famille"
    - "urgence"

# Verbosité
communication:
  verbosity: "balanced"  # concise | balanced | detailed
  tone: "professional"   # casual | professional | friendly

# Apprentissage
learning:
  collect_conversations: true
  anonymize_data: true
  request_daily_feedback: true
  feedback_time: "20:00"
```

## 📈 Métriques Disponibles

### Feedback

```python
feedback_mgr = FeedbackManager()

# Résumé journalier
daily = feedback_mgr.get_daily_summary()
# → avg_score, satisfaction_rate, distribution, etc.

# Résumé hebdomadaire
weekly = feedback_mgr.get_weekly_summary(weeks=1)
# → trend (improving/declining/stable), common_issues, etc.
```

### Conversations

```python
collector = ConversationCollector()

# Statistiques
stats = collector.get_statistics()
# → total_conversations, avg_turns, avg_satisfaction, etc.

# Charger conversations
conversations = collector.load_conversations(
    start_date="20251001",
    end_date="20251023"
)
```

## 🎨 Exemples Complets

### Scénario 1: Chat avec Collecte Auto

```python
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_input = data['message']
    
    # Détecter l'intention
    intent = detect_intent(user_input)
    
    # Générer réponse selon verbosité
    verbosity = learning.get_verbosity()
    response = generate_response(user_input, verbosity)
    
    # Collecter automatiquement
    learning.collect_interaction(
        user_input=user_input,
        assistant_response=response,
        intent=intent
    )
    
    # Vérifier si demander feedback
    extra = {}
    if learning.should_request_feedback():
        extra['feedback_request'] = learning.get_feedback_prompt()
    
    return {'response': response, **extra}
```

### Scénario 2: Notification avec Filtres

```python
def notify_user(message, priority="medium", from_contact=None):
    # Vérifier si notification autorisée
    if not learning.should_notify(
        priority=priority,
        contact=from_contact,
        content=message
    ):
        print(f"🔕 Notification bloquée (mode nuit ou faible priorité)")
        return False
    
    # Envoyer la notification
    send_push_notification(message)
    return True
```

### Scénario 3: Commande avec Confirmation

```python
@app.route('/api/execute', methods=['POST'])
def execute_command():
    command = request.get_json()['command']
    
    # Vérifier si confirmation nécessaire
    if learning.requires_confirmation(command):
        # Vérifier si confirmation fournie
        if not request.get_json().get('confirmed'):
            return {
                'requires_confirmation': True,
                'message': f'Confirmer: {command} ? (oui/non)'
            }
    
    # Exécuter
    result = execute(command)
    
    return {'result': result}
```

## 🔄 Workflow Complet

```
1. Utilisateur → Message
   ↓
2. Orchestrateur reçoit
   ↓
3. Learning Middleware:
   - Vérifie préférences (mode nuit, etc.)
   - Lance timer
   ↓
4. Traitement message
   - Détection intention
   - Génération réponse (verbosité adaptée)
   ↓
5. Learning Middleware:
   - Collecte interaction (anonymisée)
   - Calcule temps réponse
   ↓
6. Réponse → Utilisateur
   ↓
7. Demande feedback si approprié
   ↓
8. Export périodique dataset fine-tuning
```

## 📅 Export Quotidien (Cron)

```bash
# Ajouter à crontab
0 2 * * * cd /path/to/HOPPER && python -c "from src.learning.integration.learning_middleware import LearningMiddleware; LearningMiddleware().export_training_data()" >> /var/log/hopper_export.log 2>&1
```

## 🎯 Prochaines Étapes

1. ✅ **Intégrer dans orchestrateur** (priorité 1)
2. 🔜 **Pipeline LoRA** (fine-tuning sur données collectées)
3. 🔜 **Moteur RL** (classification intentions, Q-learning)
4. 🔜 **Sécurité renforcée** (auth vocale, scénarios abus)

## 📚 Ressources

- Préférences: `src/learning/preferences/`
- Conversations: `src/learning/fine_tuning/`
- Feedback: `src/learning/feedback/`
- Intégration: `src/learning/integration/`

- Données: `data/conversations/`, `data/training/`, `data/feedback/`
- Config: `config/user_preferences/default_preferences.yaml`
