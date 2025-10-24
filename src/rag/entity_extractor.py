"""
Entity Extractor - NER simple avec regex
Phase 3.5 - Week 2 Implementation

Extraction d'entités nommées sans dépendance spaCy
(Compatible Python 3.13)

Entités supportées:
- PERSON: Noms de personnes
- LOCATION: Lieux (villes, pays)
- ORGANIZATION: Entreprises, institutions
- DATE: Dates et périodes
- CONCEPT: Concepts techniques
"""

import re
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass
from enum import Enum


class EntityType(Enum):
    """Types d'entités"""
    PERSON = "person"
    LOCATION = "location"
    ORGANIZATION = "organization"
    DATE = "date"
    CONCEPT = "concept"
    UNKNOWN = "unknown"


@dataclass
class Entity:
    """Entité extraite"""
    text: str
    type: EntityType
    confidence: float
    start: int
    end: int
    
    def __hash__(self):
        return hash((self.text.lower(), self.type))
    
    def __eq__(self, other):
        if not isinstance(other, Entity):
            return False
        return self.text.lower() == other.text.lower() and self.type == other.type


class EntityExtractor:
    """
    Extracteur d'entités simple basé sur patterns regex
    Alternative lightweight à spaCy pour Python 3.13
    """
    
    # Patterns de lieux (villes, pays)
    LOCATIONS = {
        # Capitales majeures
        "paris", "londres", "berlin", "madrid", "rome", "moscou", "tokyo",
        "pékin", "new york", "washington", "los angeles", "san francisco",
        # Pays
        "france", "allemagne", "espagne", "italie", "royaume-uni", "angleterre",
        "états-unis", "usa", "chine", "japon", "russie", "brésil", "canada",
        # Régions
        "europe", "asie", "afrique", "amérique", "océanie",
    }
    
    # Patterns d'organisations
    ORGANIZATIONS = {
        "google", "microsoft", "apple", "amazon", "meta", "facebook",
        "openai", "anthropic", "netflix", "tesla", "spacex",
        "université", "école", "institut", "laboratoire", "cnrs",
    }
    
    # Patterns de concepts techniques
    TECH_CONCEPTS = {
        "python", "javascript", "java", "c++", "rust", "go",
        "asyncio", "django", "flask", "fastapi", "react", "vue",
        "machine learning", "deep learning", "ia", "intelligence artificielle",
        "blockchain", "bitcoin", "ethereum", "web3",
        "docker", "kubernetes", "aws", "azure", "gcp",
    }
    
    # Patterns de dates (regex)
    DATE_PATTERNS = [
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # 25/10/2025, 25-10-2025
        r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',    # 2025-10-25
        r'\b\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}\b',
        r'\b(?:lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)\b',
        r'\b(?:hier|aujourd\'hui|demain)\b',
        r'\ben\s+\d{4}\b',  # en 2025
        r'\b\d{4}\b',  # 2025 (année seule)
    ]
    
    # Patterns de personnes (titres + nom capitalisé)
    PERSON_TITLES = [
        r'\b(?:monsieur|madame|mademoiselle|m\.|mme|dr|docteur|professeur|pr)\s+[A-Z][a-zéèêàù]+(?:\s+[A-Z][a-zéèêàù]+)*\b',
        r'\b[A-Z][a-zéèêàù]+\s+[A-Z][a-zéèêàù]+\b',  # Prénom Nom
    ]
    
    def __init__(self, min_confidence: float = 0.70):
        """
        Initialize entity extractor
        
        Args:
            min_confidence: Seuil minimum de confiance (0-1)
        """
        self.min_confidence = min_confidence
        
        # Compile patterns
        self._date_patterns = [re.compile(p, re.IGNORECASE) for p in self.DATE_PATTERNS]
        self._person_patterns = [re.compile(p) for p in self.PERSON_TITLES]
    
    def extract(self, text: str) -> List[Entity]:
        """
        Extract entities from text
        
        Args:
            text: Text to analyze
            
        Returns:
            List of Entity objects
        """
        entities = []
        
        # 1. Extract dates
        entities.extend(self._extract_dates(text))
        
        # 2. Extract persons
        entities.extend(self._extract_persons(text))
        
        # 3. Extract locations
        entities.extend(self._extract_locations(text))
        
        # 4. Extract organizations
        entities.extend(self._extract_organizations(text))
        
        # 5. Extract tech concepts
        entities.extend(self._extract_concepts(text))
        
        # Deduplicate and filter by confidence
        entities = self._deduplicate(entities)
        entities = [e for e in entities if e.confidence >= self.min_confidence]
        
        return sorted(entities, key=lambda e: e.start)
    
    def _extract_dates(self, text: str) -> List[Entity]:
        """Extract date entities"""
        entities = []
        
        for pattern in self._date_patterns:
            for match in pattern.finditer(text):
                entities.append(Entity(
                    text=match.group(),
                    type=EntityType.DATE,
                    confidence=0.90,
                    start=match.start(),
                    end=match.end()
                ))
        
        return entities
    
    def _extract_persons(self, text: str) -> List[Entity]:
        """Extract person entities"""
        entities = []
        
        for pattern in self._person_patterns:
            for match in pattern.finditer(text):
                # Exclude if it's actually a location/org
                name = match.group().lower()
                if name not in self.LOCATIONS and name not in self.ORGANIZATIONS:
                    entities.append(Entity(
                        text=match.group(),
                        type=EntityType.PERSON,
                        confidence=0.75,
                        start=match.start(),
                        end=match.end()
                    ))
        
        return entities
    
    def _extract_locations(self, text: str) -> List[Entity]:
        """Extract location entities"""
        entities = []
        text_lower = text.lower()
        
        for location in self.LOCATIONS:
            # Find all occurrences (case insensitive)
            pattern = re.compile(r'\b' + re.escape(location) + r'\b', re.IGNORECASE)
            for match in pattern.finditer(text):
                entities.append(Entity(
                    text=match.group(),
                    type=EntityType.LOCATION,
                    confidence=0.95,
                    start=match.start(),
                    end=match.end()
                ))
        
        return entities
    
    def _extract_organizations(self, text: str) -> List[Entity]:
        """Extract organization entities"""
        entities = []
        text_lower = text.lower()
        
        for org in self.ORGANIZATIONS:
            pattern = re.compile(r'\b' + re.escape(org) + r'\b', re.IGNORECASE)
            for match in pattern.finditer(text):
                entities.append(Entity(
                    text=match.group(),
                    type=EntityType.ORGANIZATION,
                    confidence=0.85,
                    start=match.start(),
                    end=match.end()
                ))
        
        return entities
    
    def _extract_concepts(self, text: str) -> List[Entity]:
        """Extract technical concept entities"""
        entities = []
        text_lower = text.lower()
        
        for concept in self.TECH_CONCEPTS:
            pattern = re.compile(r'\b' + re.escape(concept) + r'\b', re.IGNORECASE)
            for match in pattern.finditer(text):
                entities.append(Entity(
                    text=match.group(),
                    type=EntityType.CONCEPT,
                    confidence=0.80,
                    start=match.start(),
                    end=match.end()
                ))
        
        return entities
    
    def _deduplicate(self, entities: List[Entity]) -> List[Entity]:
        """
        Remove duplicate entities (keep highest confidence)
        
        Args:
            entities: List of entities
            
        Returns:
            Deduplicated list
        """
        # Group by (text, type)
        groups: Dict[Tuple[str, EntityType], List[Entity]] = {}
        
        for entity in entities:
            key = (entity.text.lower(), entity.type)
            if key not in groups:
                groups[key] = []
            groups[key].append(entity)
        
        # Keep best entity per group
        result = []
        for group in groups.values():
            # Keep entity with highest confidence
            best = max(group, key=lambda e: e.confidence)
            result.append(best)
        
        return result
    
    def extract_relations(self, text: str, entities: List[Entity]) -> List[Dict]:
        """
        Extract simple relations between entities
        
        Args:
            text: Original text
            entities: Extracted entities
            
        Returns:
            List of relations as dicts
        """
        relations = []
        
        # Simple heuristic: entities close together are related
        for i, entity1 in enumerate(entities):
            for entity2 in entities[i+1:]:
                # Distance in characters
                distance = abs(entity1.start - entity2.start)
                
                # If close (<100 chars), consider related
                if distance < 100:
                    # Infer relation type from entity types
                    rel_type = self._infer_relation_type(entity1.type, entity2.type)
                    
                    if rel_type:
                        relations.append({
                            "source": entity1.text,
                            "source_type": entity1.type.value,
                            "target": entity2.text,
                            "target_type": entity2.type.value,
                            "relation": rel_type,
                            "confidence": min(entity1.confidence, entity2.confidence) * 0.8
                        })
        
        return relations
    
    def _infer_relation_type(self, type1: EntityType, type2: EntityType) -> str | None:
        """Infer relation type from entity types"""
        pairs = {
            (EntityType.PERSON, EntityType.LOCATION): "LOCATED_IN",
            (EntityType.PERSON, EntityType.ORGANIZATION): "WORKS_FOR",
            (EntityType.ORGANIZATION, EntityType.LOCATION): "BASED_IN",
            (EntityType.PERSON, EntityType.DATE): "BORN_ON",
            (EntityType.CONCEPT, EntityType.ORGANIZATION): "DEVELOPED_BY",
            (EntityType.CONCEPT, EntityType.CONCEPT): "RELATED_TO",
        }
        
        return pairs.get((type1, type2)) or pairs.get((type2, type1))


# ============================================
# Tests
# ============================================

def test_entity_extractor():
    """Test entity extraction"""
    print("=" * 60)
    print("Entity Extractor Tests")
    print("=" * 60)
    
    extractor = EntityExtractor()
    
    # Test 1: Mixed entities
    text1 = """
    Albert Einstein était un physicien allemand né en 1879.
    Il a travaillé à l'Université de Princeton et a vécu à Berlin.
    Sa théorie de la relativité révolutionna la physique.
    """
    
    print("\n📝 Text 1:")
    print(text1.strip())
    print("\n🔍 Entities found:")
    
    entities = extractor.extract(text1)
    for entity in entities:
        print(f"  • {entity.text:20} → {entity.type.value:15} (conf: {entity.confidence:.2f})")
    
    # Test 2: Tech concepts
    text2 = """
    Python asyncio est une bibliothèque pour la programmation asynchrone.
    Elle est développée par la Python Software Foundation.
    Google utilise aussi Python pour ses services.
    """
    
    print("\n📝 Text 2:")
    print(text2.strip())
    print("\n🔍 Entities found:")
    
    entities = extractor.extract(text2)
    for entity in entities:
        print(f"  • {entity.text:20} → {entity.type.value:15} (conf: {entity.confidence:.2f})")
    
    # Test 3: Relations
    print("\n🔗 Relations:")
    relations = extractor.extract_relations(text2, entities)
    for rel in relations:
        print(f"  {rel['source']} --[{rel['relation']}]--> {rel['target']} (conf: {rel['confidence']:.2f})")
    
    print("\n" + "=" * 60)
    print("✅ Tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_entity_extractor()
