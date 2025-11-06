#!/usr/bin/env python3
"""
Migration FAISS → Qdrant
Transfère les documents de la KB FAISS vers Qdrant
"""

import sys
import os

# Ajouter src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from llm_engine.knowledge_base import KnowledgeBase as KnowledgeBaseFAISS
from llm_engine.knowledge_base_qdrant import KnowledgeBase as KnowledgeBaseQdrant
from loguru import logger

def migrate_faiss_to_qdrant(
    faiss_path: str = "data/vector_store",
    qdrant_host: str = "localhost",
    qdrant_port: int = 6333
):
    """
    Migre les données FAISS vers Qdrant
    
    Args:
        faiss_path: Chemin vers les données FAISS
        qdrant_host: Host Qdrant
        qdrant_port: Port Qdrant
    """
    logger.info("=" * 70)
    logger.info("🔄 Migration FAISS → Qdrant")
    logger.info("=" * 70)
    
    # Charger KB FAISS
    logger.info(f"\n📂 Chargement KB FAISS depuis: {faiss_path}")
    
    if not os.path.exists(f"{faiss_path}/faiss.index"):
        logger.error(f"❌ Pas de données FAISS trouvées dans {faiss_path}")
        logger.info("💡 Astuce: Vérifiez que le chemin est correct ou que la KB a bien été utilisée")
        return False
    
    try:
        kb_faiss = KnowledgeBaseFAISS(persist_path=faiss_path)
        
        if kb_faiss.simulation_mode:
            logger.error("❌ KB FAISS en mode simulation - aucune donnée à migrer")
            return False
        
        nb_docs = len(kb_faiss.texts)
        logger.success(f"✅ KB FAISS chargée: {nb_docs} documents")
        
        if nb_docs == 0:
            logger.warning("⚠️ KB FAISS vide - rien à migrer")
            return True
        
    except Exception as e:
        logger.error(f"❌ Erreur chargement FAISS: {e}")
        return False
    
    # Créer KB Qdrant
    logger.info(f"\n🔌 Connexion à Qdrant: {qdrant_host}:{qdrant_port}")
    
    try:
        kb_qdrant = KnowledgeBaseQdrant(
            qdrant_host=qdrant_host,
            qdrant_port=qdrant_port,
            collection_name="hopper_knowledge"
        )
        
        if not kb_qdrant.use_qdrant:
            logger.error("❌ Impossible de se connecter à Qdrant")
            logger.info("💡 Astuce: Vérifiez que Qdrant est démarré avec docker-compose")
            return False
        
        logger.success("✅ Connecté à Qdrant")
        
    except Exception as e:
        logger.error(f"❌ Erreur connexion Qdrant: {e}")
        return False
    
    # Migration par batch
    logger.info(f"\n📦 Migration {nb_docs} documents...")
    
    batch_size = 100
    total_migrated = 0
    
    try:
        for i in range(0, nb_docs, batch_size):
            batch = kb_faiss.texts[i:i+batch_size]
            added = kb_qdrant.add(batch)
            total_migrated += added
            
            logger.info(f"   ✓ Batch {i//batch_size + 1}: {added} documents")
        
        logger.success(f"\n✅ Migration complète: {total_migrated}/{nb_docs} documents")
        
        # Vérification
        stats = kb_qdrant.get_stats()
        logger.info(f"\n📊 Statistiques Qdrant:")
        logger.info(f"   • Total documents: {stats['total_documents']}")
        logger.info(f"   • Collection: {stats['collection_name']}")
        logger.info(f"   • Dimension: {stats['embedding_dimension']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur durant migration: {e}")
        return False

def main():
    """Point d'entrée"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrer KB FAISS vers Qdrant")
    parser.add_argument(
        "--faiss-path",
        default="data/vector_store",
        help="Chemin vers données FAISS (défaut: data/vector_store)"
    )
    parser.add_argument(
        "--qdrant-host",
        default="localhost",
        help="Host Qdrant (défaut: localhost)"
    )
    parser.add_argument(
        "--qdrant-port",
        type=int,
        default=6333,
        help="Port Qdrant (défaut: 6333)"
    )
    
    args = parser.parse_args()
    
    success = migrate_faiss_to_qdrant(
        faiss_path=args.faiss_path,
        qdrant_host=args.qdrant_host,
        qdrant_port=args.qdrant_port
    )
    
    if success:
        logger.info("\n" + "=" * 70)
        logger.success("🎉 Migration réussie !")
        logger.info("=" * 70)
        logger.info("\n💡 Prochaines étapes:")
        logger.info("   1. Mettre à jour src/llm_engine/server.py pour utiliser knowledge_base_qdrant")
        logger.info("   2. Redémarrer le service LLM: docker-compose restart llm")
        logger.info("   3. Tester avec: ./bin/hopper \"Quelle est la capitale de la France?\"")
        logger.info("")
        sys.exit(0)
    else:
        logger.error("\n❌ Migration échouée")
        sys.exit(1)

if __name__ == "__main__":
    main()
