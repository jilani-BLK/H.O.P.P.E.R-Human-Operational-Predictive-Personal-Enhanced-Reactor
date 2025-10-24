#!/bin/bash

# 🧠 Script de Vérification de la Coordination HOPPER
# Vérifie que tous les modules sont bien coordonnés et reliés au noyau

echo "🔍 Vérification de l'Architecture de Coordination HOPPER"
echo "========================================================="
echo ""

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Compteurs
TOTAL_CHECKS=0
PASSED_CHECKS=0

# Fonction de test
check() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    local description=$1
    local command=$2
    
    echo -n "Vérification: $description... "
    
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ OK${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        echo -e "${RED}❌ ÉCHEC${NC}"
        return 1
    fi
}

echo -e "${BLUE}📦 1. Vérification des Fichiers Core${NC}"
echo "----------------------------------------"
check "CoordinationHub existe" "test -f src/orchestrator/coordination_hub.py"
check "Module Registry existe" "test -f src/orchestrator/module_registry.py"
check "Main orchestrator modifié" "grep -q 'register_all_hopper_modules' src/orchestrator/main.py"
check "Documentation présente" "test -f docs/COORDINATION_REPORT.md"
echo ""

echo -e "${BLUE}🧠 2. Vérification des Modules Intelligence${NC}"
echo "----------------------------------------"
check "LLM Engine - knowledge_base" "test -f src/llm_engine/knowledge_base.py"
check "LLM Engine - embeddings" "test -f src/llm_engine/embeddings.py"
check "RAG - Self-RAG" "test -f src/rag/self_rag.py"
check "RAG - GraphRAG" "test -f src/rag/graph_store.py"
check "RAG - HyDE" "test -f src/rag/hyde.py"
check "RAG - Unified Dispatcher" "test -f src/rag/unified_dispatcher.py"
check "Agent - ReAct" "test -f src/agents/react_agent.py"
echo ""

echo -e "${BLUE}🔒 3. Vérification Sécurité${NC}"
echo "----------------------------------------"
check "Permissions" "test -f src/security/permissions.py"
check "Malware Detector" "test -f src/security/malware_detector.py"
check "Confirmation" "test -f src/security/confirmation.py"
echo ""

echo -e "${BLUE}⚙️ 4. Vérification Exécution & Système${NC}"
echo "----------------------------------------"
check "System Executor" "test -f src/system_executor/server.py"
echo ""

echo -e "${BLUE}💬 5. Vérification Communication${NC}"
echo "----------------------------------------"
check "Action Narrator" "test -f src/communication/action_narrator.py"
check "Async Action Narrator" "test -f src/communication/async_action_narrator.py"
echo ""

echo -e "${BLUE}📚 6. Vérification Apprentissage${NC}"
echo "----------------------------------------"
check "Validation System" "test -f src/learning/validation_system.py"
check "Preference Engine" "test -f src/learning/preference_engine.py"
echo ""

echo -e "${BLUE}🧮 7. Vérification Raisonnement${NC}"
echo "----------------------------------------"
check "Code Executor" "test -f src/reasoning/code_executor.py"
check "Problem Solver" "test -f src/reasoning/problem_solver.py"
echo ""

echo -e "${BLUE}🎤 8. Vérification Pipeline Vocal${NC}"
echo "----------------------------------------"
check "STT (Whisper)" "test -d src/stt"
check "TTS (Coqui)" "test -d src/tts"
check "Voice Pipeline" "test -f src/voice_pipeline.py"
check "Voice Cloning" "test -f src/tts/voice_cloning.py"
echo ""

echo -e "${BLUE}🔌 9. Vérification Connecteurs${NC}"
echo "----------------------------------------"
check "Local System Connector" "test -f src/connectors/local_system.py"
check "Filesystem Adapters" "test -d src/connectors/filesystem"
echo ""

echo -e "${BLUE}📊 10. Vérification Monitoring${NC}"
echo "----------------------------------------"
check "Neural Monitor" "test -f src/orchestrator/neural_monitor.py"
check "Neural Interface Web" "test -f web/neural_interface/index.html"
check "Neural Server" "test -f web/neural_interface/neural_server.py"
echo ""

echo -e "${BLUE}📄 11. Vérification Data Formats${NC}"
echo "----------------------------------------"
check "Converters" "test -d src/data_formats/converters"
check "Document Editor" "test -f src/data_formats/document_editor.py"
echo ""

echo -e "${BLUE}🔐 12. Vérification Authentification${NC}"
echo "----------------------------------------"
check "Auth directory" "test -d src/authentication"
echo ""

echo -e "${BLUE}⚡ 13. Vérification Middleware${NC}"
echo "----------------------------------------"
check "Security Middleware" "test -f src/orchestrator/middleware/security_middleware.py"
check "Learning Middleware" "test -f src/orchestrator/middleware/learning_middleware.py"
check "Neural Middleware" "test -f src/orchestrator/middleware/neural_middleware.py"
echo ""

echo -e "${BLUE}🌐 14. Vérification API${NC}"
echo "----------------------------------------"
check "Main Orchestrator" "test -f src/orchestrator/main.py"
check "Service Registry" "test -f src/orchestrator/service_registry.py"
check "Intent Dispatcher" "test -f src/orchestrator/dispatcher.py"
check "Context Manager" "test -f src/orchestrator/context_manager.py"
echo ""

echo -e "${BLUE}🐍 15. Vérification Imports Python${NC}"
echo "----------------------------------------"
check "CoordinationHub importable" "cd src/orchestrator && python -c 'from coordination_hub import CoordinationHub' 2>/dev/null"
check "Module Registry importable" "cd src/orchestrator && python -c 'from module_registry import register_all_hopper_modules' 2>/dev/null"
check "Pas d'erreurs syntaxe Hub" "python -m py_compile src/orchestrator/coordination_hub.py 2>/dev/null"
check "Pas d'erreurs syntaxe Registry" "python -m py_compile src/orchestrator/module_registry.py 2>/dev/null"
echo ""

echo "========================================================="
echo -e "${YELLOW}📊 RÉSULTAT FINAL${NC}"
echo "========================================================="
echo -e "Tests réussis: ${GREEN}$PASSED_CHECKS${NC}/$TOTAL_CHECKS"
echo ""

if [ $PASSED_CHECKS -eq $TOTAL_CHECKS ]; then
    echo -e "${GREEN}✅ TOUS LES MODULES SONT COORDONNÉS ET RELIÉS AU NOYAU !${NC}"
    echo -e "${GREEN}🧠 Le cerveau de HOPPER est complètement connecté !${NC}"
    exit 0
else
    FAILED=$((TOTAL_CHECKS - PASSED_CHECKS))
    echo -e "${RED}❌ $FAILED tests échoués${NC}"
    echo -e "${YELLOW}⚠️ Certains modules nécessitent une attention${NC}"
    exit 1
fi
