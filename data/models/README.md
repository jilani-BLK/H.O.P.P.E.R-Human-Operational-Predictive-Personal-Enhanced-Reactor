# 🤖 Modèles LLM HOPPER

Les modèles LLM ne sont **pas versionnés dans Git** en raison de leur taille (4+ GB).

## 📥 Téléchargement

### Mistral 7B (Recommandé - 4.1 GB)

```bash
# Télécharger depuis Hugging Face
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.Q4_K_M.gguf \
  -O data/models/mistral-7b-instruct-v0.1.Q4_K_M.gguf
```

### LLaMA 2 7B (Alternative - 3.8 GB)

```bash
wget https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf \
  -O data/models/llama-2-7b-chat.Q4_K_M.gguf
```

## 🐳 Docker

Les modèles sont montés via volumes dans `docker-compose.yml`:

```yaml
volumes:
  - ./data/models:/app/data/models:ro
```

## 📋 Modèles Supportés

- ✅ Mistral 7B Instruct (Recommandé)
- ✅ LLaMA 2 7B Chat
- ✅ Tout modèle GGUF compatible llama.cpp
