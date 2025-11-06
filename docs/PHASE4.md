# Phase 4 - Intelligence & Apprentissage

**Amélioration continue de l'intelligence de HOPPER via fine-tuning, apprentissage des préférences et mécanismes de décision**

---

## 📋 Vue d'Ensemble

**Durée**: 8 semaines (Mois 7-8)  
**Objectif**: Assistant "apprenant" adapté aux préférences utilisateur  
**Prérequis**: Phase 3 opérationnelle (Voice + Email + Notifications)

---

## 🎯 Objectifs Clés

1. **Fine-tuning LLM** - Adapter le modèle aux cas d'usage spécifiques
2. **Règles personnalisées** - Configuration utilisateur (heures silence, VIP, etc.)
3. **Moteur de décision** - Classification intentions, priorisation intelligente
4. **Feedback utilisateur** - Collecte satisfaction, amélioration continue
5. **Sécurité renforcée** - Robustesse, validation commandes, gestion erreurs

---

## 📅 Planning Détaillé

### 🗓️ Semaine 1-2: Collecte de Données & Infrastructure LoRA

**Objectifs:**
- Collecter conversations réelles Phase 3
- Identifier patterns d'erreurs/améliorations
- Setup infrastructure fine-tuning avec LoRA

**Tâches:**

1. **Logger conversations** (data/training/conversations/)
   ```python
   # src/llm_engine/conversation_logger.py
   - Enregistrer: user_input, llm_response, user_feedback, timestamp
   - Format: JSONL pour fine-tuning
   - Consentement utilisateur (opt-in)
   - Anonymisation si nécessaire
   ```

2. **Analyser qualité réponses**
   ```bash
   # scripts/analyze_conversations.py
   - Identifier réponses insatisfaisantes
   - Extraire patterns d'erreurs
   - Générer rapport qualité
   ```

3. **Créer dataset fine-tuning**
   ```python
   # data/training/finetune_dataset.jsonl
   Format: {"instruction": "...", "input": "...", "output": "..."}
   Target: 100-500 exemples qualité
   ```

4. **Setup LoRA infrastructure**
   ```bash
   # Installation
   pip install peft transformers bitsandbytes accelerate
   
   # Script fine-tuning
   src/llm_engine/finetune_lora.py
   - Charger modèle base (Mistral 7B)
   - Config LoRA (r=16, alpha=32)
   - Training 3-5 epochs
   - Sauvegarde adapters
   ```

**Livrables:**
- ✅ 200+ conversations collectées
- ✅ Dataset fine-tuning prêt
- ✅ Script LoRA fonctionnel
- ✅ Documentation process

---

### 🗓️ Semaine 3-4: Fine-Tuning & Évaluation Modèle

**Objectifs:**
- Entraîner LoRA adapters
- Évaluer amélioration
- Déployer modèle affiné

**Tâches:**

1. **Lancer fine-tuning**
   ```bash
   python src/llm_engine/finetune_lora.py \
     --base_model mistralai/Mistral-7B-Instruct-v0.2 \
     --dataset data/training/finetune_dataset.jsonl \
     --output_dir data/models/hopper_lora_v1 \
     --epochs 5 \
     --batch_size 4 \
     --learning_rate 2e-4
   
   # Temps estimé: 2-4h sur Mac M1/M2
   ```

2. **Évaluation quantitative**
   ```python
   # tests/phase4/test_llm_quality.py
   - Perplexité avant/après
   - Accuracy sur test set
   - Latence inférence
   ```

3. **Évaluation qualitative**
   ```bash
   # tests/phase4/manual_eval.py
   - 20 prompts test
   - Comparaison base vs fine-tuned
   - Scoring humain 1-5
   ```

4. **Intégration modèle affiné**
   ```python
   # src/llm_engine/llm_server.py
   from peft import PeftModel
   
   base_model = AutoModelForCausalLM.from_pretrained(...)
   model = PeftModel.from_pretrained(base_model, "data/models/hopper_lora_v1")
   ```

**Livrables:**
- ✅ Modèle LoRA entraîné
- ✅ Rapport évaluation (accuracy +10-15%)
- ✅ Modèle déployé dans LLM service
- ✅ A/B test framework

---

### 🗓️ Semaine 5: Règles Heuristiques & Configuration Utilisateur

**Objectifs:**
- Système de préférences utilisateur
- Règles personnalisables
- Interface configuration

**Tâches:**

1. **Schéma configuration** (config/user_preferences.yaml)
   ```yaml
   user:
     name: "Jean"
     timezone: "Europe/Paris"
   
   notifications:
     quiet_hours:
       start: "22:00"
       end: "07:00"
     vip_contacts:
       - "marie@example.com"
       - "boss@company.com"
     min_priority: 7  # 0-10
     notification_modes:
       work_hours: "vocal"    # 9h-18h
       evening: "silent"      # 18h-22h
       night: "disabled"      # 22h-7h
   
   voice:
     activation_keyword: "hopper"
     speaker_verification: true
     voice_profile: "jean_profile_v1"
   
   email:
     auto_categorize: true
     urgent_keywords: ["urgent", "asap", "important"]
     spam_senders:
       - "newsletter@spam.com"
   
   learning:
     enable_fine_tuning: true
     feedback_frequency: "daily"  # daily, weekly
     data_retention_days: 90
   ```

2. **Moteur de règles**
   ```python
   # src/orchestrator/rules_engine.py
   class RulesEngine:
       def should_notify(self, notification, time, user_prefs):
           # Check quiet hours
           # Check VIP status
           # Check priority threshold
           # Return decision + reason
       
       def categorize_email(self, email, rules):
           # Apply keyword matching
           # Sender reputation
           # Return category + confidence
   ```

3. **Interface configuration vocale**
   ```python
   # src/orchestrator/voice_config.py
   Commandes:
   - "Hopper, active le mode nuit"
   - "Hopper, ajoute Marie aux contacts VIP"
   - "Hopper, ne me dérange pas avant 8h"
   - "Hopper, augmente la priorité des emails de Paul"
   ```

4. **Tests règles**
   ```python
   # tests/phase4/test_rules_engine.py
   - Test quiet hours
   - Test VIP notifications
   - Test email categorization
   - Test mode switches
   ```

**Livrables:**
- ✅ Système préférences complet
- ✅ 10+ règles configurables
- ✅ Interface vocale config
- ✅ Tests automatisés

---

### 🗓️ Semaine 6: Moteur de Décision RL (Simple)

**Objectifs:**
- Classification intentions
- Priorisation adaptative
- Apprentissage par feedback

**Tâches:**

1. **Classifier intentions**
   ```python
   # src/orchestrator/intent_classifier.py
   from sklearn.ensemble import RandomForestClassifier
   
   class IntentClassifier:
       """
       Input: user_input, context, time, history
       Output: intent (notification_now, defer, ignore, escalate)
       """
       def train(self, examples):
           # X: features (text embeddings, time, priority)
           # y: labels (user feedback)
       
       def predict(self, notification):
           return intent, confidence
   ```

2. **Features engineering**
   ```python
   def extract_features(notification, context):
       return {
           'priority': notification.priority,
           'hour': datetime.now().hour,
           'day_of_week': datetime.now().weekday(),
           'sender_frequency': count_emails_from(sender),
           'keyword_match': has_urgent_keywords(),
           'user_activity': is_user_active(),
           'text_embedding': get_sentence_embedding(text)
       }
   ```

3. **Apprentissage par feedback**
   ```python
   # src/orchestrator/feedback_loop.py
   def collect_feedback(notification_id, user_action):
       """
       Actions: 'read_immediately', 'read_later', 'dismissed', 'marked_important'
       """
       save_to_training_data(notification_id, user_action)
       
       if len(training_data) >= 50:
           retrain_classifier()
   ```

4. **Q-Learning simple (optionnel)**
   ```python
   # src/orchestrator/rl_agent.py
   State: (notification_pending, user_activity, time_slot)
   Actions: [notify_vocal, notify_silent, defer_1h, defer_next_day]
   Reward: +1 si user satisfait, -1 si ignoré
   
   # Update Q-table based on feedback
   ```

**Livrables:**
- ✅ Intent classifier (80%+ accuracy)
- ✅ Feedback loop fonctionnel
- ✅ 50+ exemples training
- ✅ Amélioration priorisation mesurée

---

### 🗓️ Semaine 7: Feedback Utilisateur & Évaluation Continue

**Objectifs:**
- Système d'évaluation quotidienne
- Analyse satisfaction
- Métriques qualité

**Tâches:**

1. **Prompt évaluation quotidienne**
   ```python
   # src/orchestrator/daily_evaluation.py
   
   async def ask_daily_feedback():
       """
       Triggered: 20h every day
       """
       questions = [
           "Comment évaluez-vous Hopper aujourd'hui ? (1-5)",
           "Qu'est-ce qui a bien fonctionné ?",
           "Qu'est-ce qui pourrait être amélioré ?"
       ]
       
       # Vocal ou texte
       responses = await collect_responses(questions)
       save_feedback(responses)
       analyze_sentiment(responses)
   ```

2. **Dashboard satisfaction**
   ```python
   # scripts/satisfaction_dashboard.py
   Métriques:
   - Score moyen satisfaction (1-5)
   - Évolution sur 30 jours
   - Top 5 problèmes récurrents
   - Top 5 fonctionnalités appréciées
   - Temps réponse moyen
   - Taux de commandes réussies
   ```

3. **Analyse feedback texte**
   ```python
   # src/analytics/feedback_analyzer.py
   from transformers import pipeline
   
   sentiment = pipeline("sentiment-analysis")
   
   def analyze_feedback(text):
       # Sentiment: positive, negative, neutral
       # Keywords extraction
       # Topic modeling (what users talk about)
       # Identify pain points
   ```

4. **Rapport hebdomadaire automatique**
   ```python
   # scripts/weekly_report.py
   
   Génère rapport:
   - Satisfaction moyenne
   - Incidents rencontrés
   - Améliorations à prioriser
   - Suggestions d'optimisation
   
   Envoi: email + synthèse vocale vendredi 18h
   ```

**Livrables:**
- ✅ Système feedback opérationnel
- ✅ Dashboard satisfaction
- ✅ 7 jours de données collectées
- ✅ Premier rapport hebdomadaire

---

### 🗓️ Semaine 8: Sécurité & Robustesse

**Objectifs:**
- Tests adversariaux
- Gestion erreurs robuste
- Validation commandes sensibles

**Tâches:**

1. **Tests scénarios d'abus**
   ```python
   # tests/phase4/test_security.py
   
   Scénarios:
   - Voix inconnue essaie commande système
   - Commande mal interprétée ("supprime tous mes emails" → risque)
   - Injection dans prompt LLM
   - Déconnexion internet pendant requête
   - Service down en cascade
   - Buffer overflow audio
   - Token exhaustion LLM
   ```

2. **Validation commandes sensibles**
   ```python
   # src/orchestrator/command_validator.py
   
   DANGEROUS_COMMANDS = [
       "delete", "remove", "wipe", "format",
       "send email to all", "shutdown system"
   ]
   
   def validate_command(command, user_verified):
       if is_dangerous(command):
           if not user_verified:
               return "REJECT", "Speaker not verified"
           
           # Demander confirmation vocale
           confirm = ask_confirmation(command)
           if not confirm:
               return "REJECT", "User cancelled"
       
       return "ALLOW", None
   ```

3. **Circuit breakers**
   ```python
   # src/orchestrator/circuit_breaker.py
   
   class ServiceCircuitBreaker:
       """
       Si service échoue 5x en 1min → ouvert (fail fast)
       Réessayer après 30s
       """
       def call_service(self, service_url, data):
           if self.is_open():
               raise ServiceUnavailableError()
           
           try:
               response = requests.post(service_url, json=data, timeout=5)
               self.record_success()
               return response
           except Exception as e:
               self.record_failure()
               if self.failure_threshold_reached():
                   self.open_circuit()
               raise
   ```

4. **Logs sécurité**
   ```python
   # src/security/security_logger.py
   
   Log events:
   - Failed speaker verification
   - Dangerous command attempted
   - Service timeout/error
   - Unusual activity patterns
   - Data access (GDPR compliance)
   ```

5. **Tests chaos engineering**
   ```bash
   # scripts/chaos_test.sh
   
   # Kill random service
   docker-compose stop whisper
   # Check graceful degradation
   
   # Slow network
   tc qdisc add dev eth0 root netem delay 2000ms
   # Check timeout handling
   
   # Corrupt data
   echo "garbage" > data/voice_profiles/user.pkl
   # Check error recovery
   ```

**Livrables:**
- ✅ 20+ tests sécurité
- ✅ Confirmation commandes sensibles
- ✅ Circuit breakers actifs
- ✅ Rapport audit sécurité

---

## 🏗️ Architecture Phase 4

```
┌─────────────────────────────────────────────────────────────────┐
│                       HOPPER - Phase 4                           │
│                  Intelligence & Apprentissage                    │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐        ┌──────────────────┐
│  LLM Fine-Tuned  │◄───────│   LoRA Adapter   │
│  (Mistral 7B)    │        │  (data/models/)  │
└────────┬─────────┘        └──────────────────┘
         │
         │ Enhanced responses
         │
┌────────▼────────────────────────────────────────────────────────┐
│                     Orchestrateur Phase 4                        │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐  │
│  │ Rules Engine │  │   Intent     │  │  Feedback Collector │  │
│  │              │  │  Classifier  │  │                     │  │
│  │ - Quiet hrs  │  │              │  │ - Daily eval        │  │
│  │ - VIP list   │  │ - Priority   │  │ - Satisfaction      │  │
│  │ - Modes      │  │ - Timing     │  │ - Analytics         │  │
│  └──────────────┘  └──────────────┘  └─────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │           Command Validator & Security                 │    │
│  │  - Speaker verification                                │    │
│  │  - Dangerous command confirmation                      │    │
│  │  - Circuit breakers                                    │    │
│  └────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘

         │
         │ Secured & Intelligent decisions
         │
┌────────▼────────────────────────────────────────────────────────┐
│                    User Preferences                              │
│                 (config/user_preferences.yaml)                   │
│                                                                  │
│  - Notification rules          - Learning settings              │
│  - VIP contacts                - Voice config                   │
│  - Quiet hours                 - Email filters                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 📊 Métriques de Succès

### Quantitatives

| Métrique | Baseline (Phase 3) | Target (Phase 4) |
|----------|-------------------|------------------|
| Satisfaction utilisateur | N/A | >4.0/5.0 |
| Taux commandes réussies | ~75% | >85% |
| Latence réponse LLM | 2-3s | <2.5s |
| Précision intent classifier | N/A | >80% |
| Faux positifs notifications | ~30% | <15% |
| Accuracy modèle fine-tuned | Baseline | +10-15% |

### Qualitatives

- ✅ Réponses plus contextuelles et personnalisées
- ✅ Adaptation aux habitudes utilisateur
- ✅ Gestion erreurs gracieuse
- ✅ Confiance utilisateur accrue
- ✅ Réduction frustrations (mesurée par feedback)

---

## 🛠️ Stack Technique Phase 4

```python
# Fine-tuning & ML
peft==0.7.0              # LoRA adapters
transformers==4.36.0     # Hugging Face
bitsandbytes==0.41.0     # Quantization
accelerate==0.25.0       # Distributed training
scikit-learn==1.3.2      # Intent classifier
torch==2.1.0             # Deep learning

# Feedback & Analytics
pandas==2.1.4            # Data analysis
matplotlib==3.8.2        # Visualizations
seaborn==0.13.0          # Stats plots
nltk==3.8.1              # Text processing

# Security
cryptography==41.0.7     # Encryption
jwt==2.8.0               # Token validation
ratelimit==2.2.1         # API rate limiting
```

---

## 📁 Structure Fichiers Phase 4

```
HOPPER/
├── src/
│   ├── llm_engine/
│   │   ├── finetune_lora.py          # LoRA training script
│   │   ├── conversation_logger.py     # Log conversations
│   │   └── llm_server.py              # (modifié: load LoRA)
│   │
│   ├── orchestrator/
│   │   ├── rules_engine.py            # User rules
│   │   ├── intent_classifier.py       # ML intent classification
│   │   ├── command_validator.py       # Security validation
│   │   ├── feedback_loop.py           # Adaptive learning
│   │   ├── circuit_breaker.py         # Fault tolerance
│   │   └── daily_evaluation.py        # User feedback
│   │
│   ├── analytics/
│   │   ├── feedback_analyzer.py       # Sentiment analysis
│   │   └── satisfaction_dashboard.py  # Metrics viz
│   │
│   └── security/
│       ├── security_logger.py         # Audit logs
│       └── auth_validator.py          # Enhanced auth
│
├── config/
│   └── user_preferences.yaml          # User config
│
├── data/
│   ├── training/
│   │   ├── conversations/             # Logged chats
│   │   ├── finetune_dataset.jsonl     # Training data
│   │   └── feedback/                  # User feedback
│   │
│   └── models/
│       ├── hopper_lora_v1/            # Fine-tuned adapter
│       └── intent_classifier.pkl      # Trained classifier
│
├── tests/
│   └── phase4/
│       ├── test_llm_quality.py        # Model evaluation
│       ├── test_rules_engine.py       # Rules testing
│       ├── test_intent_classifier.py  # ML testing
│       └── test_security.py           # Security tests
│
└── scripts/
    ├── analyze_conversations.py       # Data analysis
    ├── train_intent_classifier.py     # ML training
    ├── satisfaction_dashboard.py      # Metrics viz
    ├── weekly_report.py               # Auto reports
    └── chaos_test.sh                  # Chaos engineering
```

---

## 🚀 Quick Start Phase 4

```bash
# 1. Installer dépendances Phase 4
pip install peft transformers bitsandbytes accelerate scikit-learn

# 2. Activer logging conversations (Phase 3 doit tourner)
python src/llm_engine/conversation_logger.py --enable

# 3. Collecter 7 jours de données
# (Utiliser normalement HOPPER pendant 1 semaine)

# 4. Analyser et créer dataset
python scripts/analyze_conversations.py \
  --input data/training/conversations/ \
  --output data/training/finetune_dataset.jsonl \
  --min_quality 3

# 5. Fine-tuner modèle
python src/llm_engine/finetune_lora.py \
  --dataset data/training/finetune_dataset.jsonl \
  --epochs 5 \
  --output data/models/hopper_lora_v1

# 6. Déployer modèle affiné
docker-compose restart llm

# 7. Configurer préférences
cp config/user_preferences.yaml.template config/user_preferences.yaml
nano config/user_preferences.yaml

# 8. Activer feedback quotidien
python src/orchestrator/daily_evaluation.py --enable

# 9. Tests sécurité
pytest tests/phase4/test_security.py -v

# 10. Dashboard satisfaction
python scripts/satisfaction_dashboard.py --serve
```

---

## ✅ Checklist Implémentation

### Semaine 1-2: Data & LoRA
- [ ] Logger conversations activé
- [ ] 200+ conversations collectées
- [ ] Dataset fine-tuning créé (100-500 exemples)
- [ ] Script LoRA fonctionnel
- [ ] Tests sur petit dataset

### Semaine 3-4: Fine-Tuning
- [ ] Modèle LoRA entraîné (5 epochs)
- [ ] Évaluation quantitative (perplexity, accuracy)
- [ ] Évaluation qualitative (20 prompts test)
- [ ] Modèle déployé dans LLM service
- [ ] Amélioration mesurée (+10-15%)

### Semaine 5: Règles & Config
- [ ] Schema user_preferences.yaml complet
- [ ] Rules engine implémenté
- [ ] 10+ règles testées
- [ ] Interface vocale config
- [ ] Tests automatisés

### Semaine 6: Intent Classifier
- [ ] Features extracted (8+ features)
- [ ] Classifier entraîné (RandomForest/SVM)
- [ ] Accuracy >80%
- [ ] Feedback loop intégré
- [ ] 50+ exemples training

### Semaine 7: Feedback
- [ ] Daily evaluation active
- [ ] Dashboard satisfaction
- [ ] Sentiment analysis
- [ ] Rapport hebdomadaire auto
- [ ] 7 jours de feedback collectés

### Semaine 8: Sécurité
- [ ] 20+ tests sécurité
- [ ] Command validator actif
- [ ] Circuit breakers implémentés
- [ ] Logs audit sécurité
- [ ] Rapport audit complet

---

## 🎓 Ressources

### Fine-Tuning LoRA
- [PEFT Documentation](https://huggingface.co/docs/peft)
- [LoRA Paper](https://arxiv.org/abs/2106.09685)
- [QLoRA: Efficient Fine-tuning](https://arxiv.org/abs/2305.14314)

### Intent Classification
- [Scikit-learn Classifiers](https://scikit-learn.org/stable/supervised_learning.html)
- [RASA NLU](https://rasa.com/docs/rasa/nlu-training-data/)

### Reinforcement Learning (Optionnel)
- [Stable Baselines3](https://stable-baselines3.readthedocs.io/)
- [OpenAI Spinning Up](https://spinningup.openai.com/)

### Security
- [OWASP AI Security](https://owasp.org/www-project-ai-security-and-privacy-guide/)
- [Prompt Injection Defense](https://simonwillison.net/2023/Apr/14/worst-that-can-happen/)

---

## 📝 Notes Importantes

### Consentement & RGPD
```python
# Toujours demander consentement explicite
def request_data_consent():
    """
    "Hopper souhaite apprendre de vos conversations pour mieux vous servir.
    Acceptez-vous que vos interactions soient enregistrées de manière anonyme ?
    Vous pouvez refuser ou retirer votre consentement à tout moment."
    """
    consent = await get_user_response()
    save_consent(user_id, consent, timestamp)
    return consent
```

### Fine-Tuning Mac Optimisations
```python
# Utiliser quantization 4-bit
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    load_in_4bit=True,
    device_map="auto"
)

# LoRA config pour Mac
lora_config = LoraConfig(
    r=16,              # Rank (plus petit = moins de VRAM)
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)
```

### Temps Estimés (Mac M1/M2)
- **Data collection**: 7 jours usage normal
- **Dataset preparation**: 2-4 heures
- **Fine-tuning LoRA**: 2-4 heures (500 samples, 5 epochs)
- **Evaluation**: 30 minutes
- **Full Phase 4**: 8 semaines

---

**Version**: 4.0.0  
**Status**: PRÊT À DÉMARRER (après Phase 3 opérationnelle)  
**Dernière mise à jour**: 5 novembre 2025
