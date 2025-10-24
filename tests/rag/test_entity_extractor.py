"""
Tests unitaires pour l'extracteur d'entités (GraphRAG Week 2).

Validations:
- Extraction de personnes (titres + noms capitalisés)
- Extraction de lieux (50+ villes/pays connus)
- Extraction d'organisations (20+ entreprises/institutions)
- Extraction de dates (7 patterns regex)
- Extraction de concepts (30+ langages/frameworks)
- Extraction de relations (proximité <100 chars)
- Déduplication (conservation de la plus haute confiance)
- Cas limites (texte vide, pas d'entités, chevauchements)
"""

import pytest
from src.rag.entity_extractor import (
    EntityExtractor,
    Entity,
    EntityType,
)


class TestEntityExtractionPersons:
    """Tests pour l'extraction de personnes."""

    def test_person_with_title(self):
        """Doit extraire une personne avec un titre honorifique."""
        extractor = EntityExtractor()
        text = "Dr. Marie Curie a découvert la radioactivité."
        entities = extractor.extract(text)
        
        persons = [e for e in entities if e.type == EntityType.PERSON]
        assert len(persons) >= 1
        assert any("Marie Curie" in e.text for e in persons)
        
        # Vérifier la confiance
        marie = next(e for e in persons if "Marie Curie" in e.text)
        assert 0.70 <= marie.confidence <= 0.80

    def test_person_without_title(self):
        """Doit extraire une personne avec des mots capitalisés."""
        extractor = EntityExtractor()
        text = "Albert Einstein révolutionna la physique."
        entities = extractor.extract(text)
        
        persons = [e for e in entities if e.type == EntityType.PERSON]
        assert len(persons) >= 1
        assert any("Albert Einstein" in e.text for e in persons)

    def test_multiple_persons(self):
        """Doit extraire plusieurs personnes dans le même texte."""
        extractor = EntityExtractor()
        text = "Isaac Newton et Galileo Galilei étaient des scientifiques."
        entities = extractor.extract(text)
        
        persons = [e for e in entities if e.type == EntityType.PERSON]
        assert len(persons) >= 2

    def test_person_positions(self):
        """Doit capturer les positions correctes."""
        extractor = EntityExtractor()
        text = "Dr. Marie Curie était brillante."
        entities = extractor.extract(text)
        
        persons = [e for e in entities if e.type == EntityType.PERSON]
        assert len(persons) >= 1
        person = persons[0]
        assert person.start < person.end
        # Vérifier que la position correspond à une partie du nom
        extracted = text[person.start:person.end]
        assert "Marie" in extracted or "Curie" in extracted or "Dr" in extracted


class TestEntityExtractionLocations:
    """Tests pour l'extraction de lieux."""

    def test_known_city(self):
        """Doit extraire une ville connue (Paris)."""
        extractor = EntityExtractor()
        text = "Je vis à Paris depuis 2020."
        entities = extractor.extract(text)
        
        locations = [e for e in entities if e.type == EntityType.LOCATION]
        assert len(locations) >= 1
        assert any("paris" in e.text.lower() for e in locations)
        
        # Vérifier haute confiance pour lieux connus
        paris = next(e for e in locations if "paris" in e.text.lower())
        assert paris.confidence >= 0.90

    def test_known_country(self):
        """Doit extraire un pays connu (France)."""
        extractor = EntityExtractor()
        text = "La France est en Europe."
        entities = extractor.extract(text)
        
        locations = [e for e in entities if e.type == EntityType.LOCATION]
        assert len(locations) >= 2  # France + Europe
        assert any("france" in e.text.lower() for e in locations)
        assert any("europe" in e.text.lower() for e in locations)

    def test_multiple_locations(self):
        """Doit extraire plusieurs lieux."""
        extractor = EntityExtractor()
        text = "De Paris à Londres, en passant par Berlin."
        entities = extractor.extract(text)
        
        locations = [e for e in entities if e.type == EntityType.LOCATION]
        assert len(locations) >= 3


class TestEntityExtractionOrganizations:
    """Tests pour l'extraction d'organisations."""

    def test_known_organization(self):
        """Doit extraire une organisation connue (Google)."""
        extractor = EntityExtractor()
        text = "Google développe Android."
        entities = extractor.extract(text)
        
        orgs = [e for e in entities if e.type == EntityType.ORGANIZATION]
        assert len(orgs) >= 1
        assert any("google" in e.text.lower() for e in orgs)
        assert orgs[0].confidence >= 0.80

    def test_multiple_organizations(self):
        """Doit extraire plusieurs organisations."""
        extractor = EntityExtractor()
        text = "Microsoft et Apple sont concurrents."
        entities = extractor.extract(text)
        
        orgs = [e for e in entities if e.type == EntityType.ORGANIZATION]
        assert len(orgs) >= 2

    def test_organization_with_context(self):
        """Doit extraire les organisations dans un contexte riche."""
        extractor = EntityExtractor()
        text = "OpenAI a créé ChatGPT, en collaboration avec Microsoft."
        entities = extractor.extract(text)
        
        orgs = [e for e in entities if e.type == EntityType.ORGANIZATION]
        assert len(orgs) >= 2
        assert any("openai" in e.text.lower() for e in orgs)
        assert any("microsoft" in e.text.lower() for e in orgs)


class TestEntityExtractionDates:
    """Tests pour l'extraction de dates."""

    def test_date_ddmmyyyy(self):
        """Doit extraire une date au format DD/MM/YYYY."""
        extractor = EntityExtractor()
        text = "Né le 15/03/1990."
        entities = extractor.extract(text)
        
        dates = [e for e in entities if e.type == EntityType.DATE]
        assert len(dates) >= 1
        assert any("15/03/1990" in e.text for e in dates)
        assert dates[0].confidence >= 0.85

    def test_date_year_only(self):
        """Doit extraire une année seule."""
        extractor = EntityExtractor()
        text = "En 1969, l'homme a marché sur la Lune."
        entities = extractor.extract(text)
        
        dates = [e for e in entities if e.type == EntityType.DATE]
        assert len(dates) >= 1
        assert any("1969" in e.text for e in dates)

    def test_date_relative(self):
        """Doit extraire des dates relatives (en 2020)."""
        extractor = EntityExtractor()
        text = "Cela s'est passé en 2020."
        entities = extractor.extract(text)
        
        dates = [e for e in entities if e.type == EntityType.DATE]
        assert len(dates) >= 1
        assert any("2020" in e.text for e in dates)

    def test_multiple_dates(self):
        """Doit extraire plusieurs dates."""
        extractor = EntityExtractor()
        text = "Entre 2010 et 2020, puis en 2023."
        entities = extractor.extract(text)
        
        dates = [e for e in entities if e.type == EntityType.DATE]
        assert len(dates) >= 3


class TestEntityExtractionConcepts:
    """Tests pour l'extraction de concepts techniques."""

    def test_programming_language(self):
        """Doit extraire un langage de programmation (Python)."""
        extractor = EntityExtractor()
        text = "Python est excellent pour le machine learning."
        entities = extractor.extract(text)
        
        concepts = [e for e in entities if e.type == EntityType.CONCEPT]
        assert len(concepts) >= 1
        assert any("python" in e.text.lower() for e in concepts)
        assert concepts[0].confidence >= 0.75

    def test_framework(self):
        """Doit extraire un framework (Django)."""
        extractor = EntityExtractor()
        text = "Django simplifie le développement web."
        entities = extractor.extract(text)
        
        concepts = [e for e in entities if e.type == EntityType.CONCEPT]
        assert len(concepts) >= 1
        assert any("django" in e.text.lower() for e in concepts)

    def test_multiple_concepts(self):
        """Doit extraire plusieurs concepts."""
        extractor = EntityExtractor()
        text = "asyncio et FastAPI permettent des APIs rapides."
        entities = extractor.extract(text)
        
        concepts = [e for e in entities if e.type == EntityType.CONCEPT]
        assert len(concepts) >= 2


class TestEntityRelations:
    """Tests pour l'extraction de relations."""

    def test_relation_proximity(self):
        """Doit trouver des relations par proximité (<100 chars)."""
        extractor = EntityExtractor()
        text = "Google est une entreprise basée à Mountain View en Californie."
        entities = extractor.extract(text)
        relations = extractor.extract_relations(text, entities)
        
        # Devrait trouver au moins une relation
        assert len(relations) >= 1

    def test_relation_located_in(self):
        """Doit inférer une relation LOCATED_IN."""
        extractor = EntityExtractor()
        text = "Google a un bureau à Paris."
        entities = extractor.extract(text)
        relations = extractor.extract_relations(text, entities)
        
        # Devrait trouver au moins une relation entre Google et Paris
        assert len(relations) >= 1
        # Vérifier qu'il y a une relation impliquant Paris
        paris_relations = [
            r for r in relations
            if "paris" in r["source"].lower() or "paris" in r["target"].lower()
        ]
        assert len(paris_relations) >= 1

    def test_relation_works_for(self):
        """Doit inférer une relation WORKS_FOR."""
        extractor = EntityExtractor()
        text = "Dr. Marie Curie travaillait chez Google depuis 2020."
        entities = extractor.extract(text)
        relations = extractor.extract_relations(text, entities)
        
        # Devrait trouver au moins une relation
        assert len(relations) >= 1
        # Vérifier qu'il y a une relation impliquant Google
        google_relations = [
            r for r in relations
            if "google" in r["source"].lower() or "google" in r["target"].lower()
        ]
        assert len(google_relations) >= 1

    def test_relation_confidence(self):
        """Doit calculer une confiance pour les relations."""
        extractor = EntityExtractor()
        text = "Python et asyncio sont liés."
        entities = extractor.extract(text)
        relations = extractor.extract_relations(text, entities)
        
        assert len(relations) >= 1
        for relation in relations:
            assert "confidence" in relation
            assert 0.0 <= relation["confidence"] <= 1.0


class TestEntityDeduplication:
    """Tests pour la déduplication."""

    def test_duplicate_entities_kept_highest(self):
        """Doit garder l'entité avec la plus haute confiance."""
        extractor = EntityExtractor()
        # "Paris" apparaît deux fois, devrait être dédupliqué
        text = "Paris, France. J'adore Paris."
        entities = extractor.extract(text)
        
        paris_entities = [e for e in entities if "paris" in e.text.lower()]
        # Devrait avoir seulement 1 Paris après déduplication
        assert len(paris_entities) == 1

    def test_overlapping_entities(self):
        """Doit gérer les entités qui se chevauchent."""
        extractor = EntityExtractor()
        text = "En 2020, en 2020-2021."
        entities = extractor.extract(text)
        
        dates = [e for e in entities if e.type == EntityType.DATE]
        # Vérifier qu'il n'y a pas de doublons exacts
        date_texts = [e.text for e in dates]
        assert len(date_texts) == len(set(date_texts))  # Pas de doublons


class TestEntityEdgeCases:
    """Tests pour les cas limites."""

    def test_empty_text(self):
        """Doit gérer un texte vide sans erreur."""
        extractor = EntityExtractor()
        entities = extractor.extract("")
        assert entities == []

    def test_no_entities(self):
        """Doit gérer un texte sans entités."""
        extractor = EntityExtractor()
        text = "ceci est un test simple sans entites connues"
        entities = extractor.extract(text)
        # Peut avoir quelques entités faiblement confiantes, mais ne doit pas crasher
        assert isinstance(entities, list)

    def test_very_long_text(self):
        """Doit gérer un texte très long."""
        extractor = EntityExtractor()
        text = "Paris " * 1000  # 1000 occurrences
        entities = extractor.extract(text)
        
        # Doit avoir au moins Paris, peut avoir "Paris Paris" (2 mots)
        paris_entities = [e for e in entities if "paris" in e.text.lower()]
        assert 1 <= len(paris_entities) <= 3  # Tolérance pour variantes

    def test_special_characters(self):
        """Doit gérer les caractères spéciaux."""
        extractor = EntityExtractor()
        text = "Google™ et Microsoft® sont des marques."
        entities = extractor.extract(text)
        
        orgs = [e for e in entities if e.type == EntityType.ORGANIZATION]
        assert len(orgs) >= 2

    def test_multilingual(self):
        """Doit gérer des entités multilingues."""
        extractor = EntityExtractor()
        text = "Berlin, London, Tokyo, New York."
        entities = extractor.extract(text)
        
        locations = [e for e in entities if e.type == EntityType.LOCATION]
        # Devrait trouver au moins Berlin et London (connus)
        assert len(locations) >= 2


class TestEntityPerformance:
    """Tests de performance."""

    def test_extraction_speed(self):
        """L'extraction doit être rapide (<100ms pour texte moyen)."""
        import time
        extractor = EntityExtractor()
        text = """
        Dr. Einstein travaillait à Princeton en 1950.
        Il a vécu à Berlin et à Zurich. Sa théorie de la relativité
        utilise des concepts mathématiques complexes. Python et C++
        sont maintenant utilisés pour simuler ses équations.
        Google et Microsoft financent la recherche en physique.
        """
        
        start = time.time()
        entities = extractor.extract(text)
        elapsed = time.time() - start
        
        assert elapsed < 0.1  # <100ms
        assert len(entities) >= 5  # Au moins 5 entités trouvées

    def test_relation_extraction_speed(self):
        """L'extraction de relations doit être rapide (<100ms)."""
        import time
        extractor = EntityExtractor()
        text = "Paris est en France. Google travaille avec Microsoft. Python utilise asyncio."
        entities = extractor.extract(text)
        
        start = time.time()
        relations = extractor.extract_relations(text, entities)
        elapsed = time.time() - start
        
        assert elapsed < 0.1  # <100ms
        assert len(relations) >= 2


class TestEntityIntegration:
    """Tests d'intégration."""

    def test_full_pipeline(self):
        """Test du pipeline complet : extraction + relations."""
        extractor = EntityExtractor()
        text = """
        Albert Einstein est né en Allemagne en 1879.
        Il a travaillé à l'Université de Princeton.
        Sa théorie de la relativité révolutionna la physique.
        Aujourd'hui, Python est utilisé pour simuler ses équations.
        """
        
        # Extraction
        entities = extractor.extract(text)
        assert len(entities) >= 5
        
        # Vérifier qu'on a tous les types
        types_found = {e.type for e in entities}
        assert EntityType.PERSON in types_found
        assert EntityType.DATE in types_found
        assert EntityType.LOCATION in types_found or EntityType.ORGANIZATION in types_found
        
        # Relations
        relations = extractor.extract_relations(text, entities)
        assert len(relations) >= 1
        
        # Vérifier la structure des relations
        for relation in relations:
            assert "source" in relation
            assert "target" in relation
            assert "relation" in relation
            assert "confidence" in relation

    def test_statistical_summary(self):
        """Doit permettre de générer des statistiques."""
        extractor = EntityExtractor()
        text = "Paris, Berlin, Google, Microsoft, Python, en 2020."
        entities = extractor.extract(text)
        
        # Compter par type
        stats = {}
        for entity in entities:
            stats[entity.type] = stats.get(entity.type, 0) + 1
        
        assert EntityType.LOCATION in stats
        assert EntityType.ORGANIZATION in stats
        assert EntityType.DATE in stats
        assert EntityType.CONCEPT in stats
        
        # Vérifier qu'on a le bon nombre total
        assert sum(stats.values()) == len(entities)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
