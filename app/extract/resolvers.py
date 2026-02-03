from typing import Dict, Any, List, Optional, Tuple
from core.logging import get_logger

logger = get_logger(__name__)


class EntityResolver:
    """Resolves and disambiguates extracted entities"""

    def __init__(self):
        self.entity_cache: Dict[str, Dict[str, Any]] = {}
        self.similarity_threshold = 0.8

    def resolve_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Resolve and deduplicate entities"""
        logger.info(f"Resolving {len(entities)} entities")

        resolved_entities = []
        entity_groups = self._group_similar_entities(entities)

        for group in entity_groups:
            canonical_entity = self._create_canonical_entity(group)
            resolved_entities.append(canonical_entity)

        logger.info(f"Resolved to {len(resolved_entities)} unique entities")
        return resolved_entities

    def _group_similar_entities(
        self, entities: List[Dict[str, Any]]
    ) -> List[List[Dict[str, Any]]]:
        """Group similar entities together"""
        groups = []
        processed = set()

        for i, entity in enumerate(entities):
            if i in processed:
                continue

            group = [entity]
            processed.add(i)

            for j, other_entity in enumerate(entities[i + 1 :], i + 1):
                if j in processed:
                    continue

                if self._are_similar_entities(entity, other_entity):
                    group.append(other_entity)
                    processed.add(j)

            groups.append(group)

        return groups

    def _are_similar_entities(
        self, entity1: Dict[str, Any], entity2: Dict[str, Any]
    ) -> bool:
        """Check if two entities are similar"""
        # Check type similarity
        if entity1.get("type") != entity2.get("type"):
            return False

        # Check name similarity
        name1 = entity1.get("name", "").lower()
        name2 = entity2.get("name", "").lower()

        if not name1 or not name2:
            return False

        similarity = self._calculate_string_similarity(name1, name2)
        return similarity >= self.similarity_threshold

    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings"""
        # Simple Jaccard similarity
        set1 = set(str1.split())
        set2 = set(str2.split())

        if not set1 and not set2:
            return 1.0

        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))

        return intersection / union if union > 0 else 0.0

    def _create_canonical_entity(
        self, entity_group: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create canonical entity from group of similar entities"""
        if not entity_group:
            return {}

        # Use the first entity as base
        canonical = entity_group[0].copy()

        # Merge properties from all entities
        all_properties = {}
        for entity in entity_group:
            properties = entity.get("properties", {})
            all_properties.update(properties)

        canonical["properties"] = all_properties
        canonical["source_count"] = len(entity_group)
        canonical["confidence"] = self._calculate_group_confidence(entity_group)

        return canonical

    def _calculate_group_confidence(self, entity_group: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for entity group"""
        if not entity_group:
            return 0.0

        confidences = [entity.get("confidence", 0.5) for entity in entity_group]
        return sum(confidences) / len(confidences)


class RelationshipResolver:
    """Resolves relationships between entities"""

    def __init__(self):
        self.relationship_types = {
            "works_at": ["employee", "member", "staff"],
            "located_in": ["in", "at", "within"],
            "uses": ["utilizes", "employs", "operates"],
            "connects_to": ["links", "joins", "bridges"],
        }

    def resolve_relationships(
        self, relationships: List[Dict[str, Any]], entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Resolve relationships with entity references"""
        logger.info(f"Resolving {len(relationships)} relationships")

        entity_lookup = {entity.get("name", ""): entity for entity in entities}
        resolved_relationships = []

        for relationship in relationships:
            resolved_rel = self._resolve_relationship(relationship, entity_lookup)
            if resolved_rel:
                resolved_relationships.append(resolved_rel)

        return resolved_relationships

    def _resolve_relationship(
        self, relationship: Dict[str, Any], entity_lookup: Dict[str, Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Resolve a single relationship"""
        source_name = relationship.get("source")
        target_name = relationship.get("target")

        if not source_name or not target_name:
            return None

        source_entity = entity_lookup.get(source_name)
        target_entity = entity_lookup.get(target_name)

        if not source_entity or not target_entity:
            return None

        return {
            "type": relationship.get("type"),
            "source": source_entity,
            "target": target_entity,
            "properties": relationship.get("properties", {}),
            "confidence": relationship.get("confidence", 0.5),
        }


entity_resolver = EntityResolver()
relationship_resolver = RelationshipResolver()
