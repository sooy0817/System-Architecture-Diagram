from typing import Dict, Any, List, Optional, Tuple
import re
from core.logging import get_logger

logger = get_logger(__name__)


class PatternMatcher:
    """Matches patterns in text and data"""

    def __init__(self):
        self.patterns = {
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "phone": r"\b\d{3}-\d{3}-\d{4}\b|\b\(\d{3}\)\s*\d{3}-\d{4}\b",
            "ip_address": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
            "url": r'https?://[^\s<>"{}|\\^`[\]]+',
            "date": r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
            "time": r"\b\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?\b",
        }

    def find_patterns(
        self, text: str, pattern_types: List[str] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Find patterns in text"""
        if pattern_types is None:
            pattern_types = list(self.patterns.keys())

        results = {}

        for pattern_type in pattern_types:
            if pattern_type in self.patterns:
                matches = self._find_pattern_matches(text, pattern_type)
                results[pattern_type] = matches

        return results

    def _find_pattern_matches(
        self, text: str, pattern_type: str
    ) -> List[Dict[str, Any]]:
        """Find matches for a specific pattern type"""
        pattern = self.patterns[pattern_type]
        matches = []

        for match in re.finditer(pattern, text):
            matches.append(
                {
                    "text": match.group(),
                    "start": match.start(),
                    "end": match.end(),
                    "type": pattern_type,
                    "confidence": 0.9,
                }
            )

        return matches

    def add_pattern(self, name: str, pattern: str):
        """Add a custom pattern"""
        self.patterns[name] = pattern
        logger.info(f"Added pattern '{name}': {pattern}")


class StructureMatcher:
    """Matches structural patterns in data"""

    def __init__(self):
        self.structure_patterns = {
            "hierarchy": self._match_hierarchy,
            "network": self._match_network,
            "sequence": self._match_sequence,
            "cluster": self._match_cluster,
        }

    def match_structures(self, data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Match structural patterns in data"""
        results = {}

        for pattern_name, matcher_func in self.structure_patterns.items():
            matches = matcher_func(data)
            if matches:
                results[pattern_name] = matches

        return results

    def _match_hierarchy(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Match hierarchical structures"""
        hierarchies = []

        # Look for parent-child relationships
        if "nodes" in data and "edges" in data:
            nodes = data["nodes"]
            edges = data["edges"]

            # Build parent-child map
            children_map = {}
            for edge in edges:
                parent = edge.get("source")
                child = edge.get("target")
                if parent and child:
                    if parent not in children_map:
                        children_map[parent] = []
                    children_map[parent].append(child)

            # Find root nodes (nodes with no parents)
            all_children = set()
            for children in children_map.values():
                all_children.update(children)

            node_ids = {node.get("id") for node in nodes}
            root_nodes = node_ids - all_children

            for root in root_nodes:
                hierarchy = self._build_hierarchy_tree(root, children_map)
                if hierarchy:
                    hierarchies.append(
                        {
                            "type": "hierarchy",
                            "root": root,
                            "structure": hierarchy,
                            "depth": self._calculate_hierarchy_depth(hierarchy),
                        }
                    )

        return hierarchies

    def _build_hierarchy_tree(
        self, node_id: str, children_map: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """Build hierarchy tree from node"""
        tree = {"id": node_id, "children": []}

        if node_id in children_map:
            for child_id in children_map[node_id]:
                child_tree = self._build_hierarchy_tree(child_id, children_map)
                tree["children"].append(child_tree)

        return tree

    def _calculate_hierarchy_depth(self, tree: Dict[str, Any]) -> int:
        """Calculate depth of hierarchy tree"""
        if not tree.get("children"):
            return 1

        max_child_depth = max(
            self._calculate_hierarchy_depth(child) for child in tree["children"]
        )
        return 1 + max_child_depth

    def _match_network(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Match network structures"""
        networks = []

        if "nodes" in data and "edges" in data:
            nodes = data["nodes"]
            edges = data["edges"]

            # Calculate network metrics
            node_count = len(nodes)
            edge_count = len(edges)

            if node_count > 0:
                density = (
                    (2 * edge_count) / (node_count * (node_count - 1))
                    if node_count > 1
                    else 0
                )

                networks.append(
                    {
                        "type": "network",
                        "node_count": node_count,
                        "edge_count": edge_count,
                        "density": density,
                        "connectivity": "connected"
                        if edge_count >= node_count - 1
                        else "disconnected",
                    }
                )

        return networks

    def _match_sequence(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Match sequential structures"""
        sequences = []

        # Look for sequential patterns in data
        if "steps" in data:
            steps = data["steps"]
            if isinstance(steps, list) and len(steps) > 1:
                sequences.append(
                    {
                        "type": "sequence",
                        "length": len(steps),
                        "steps": steps,
                        "is_linear": True,
                    }
                )

        return sequences

    def _match_cluster(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Match cluster structures"""
        clusters = []

        # Simple clustering based on node types or properties
        if "nodes" in data:
            nodes = data["nodes"]
            type_clusters = {}

            for node in nodes:
                node_type = node.get("type", "unknown")
                if node_type not in type_clusters:
                    type_clusters[node_type] = []
                type_clusters[node_type].append(node)

            for cluster_type, cluster_nodes in type_clusters.items():
                if len(cluster_nodes) > 1:
                    clusters.append(
                        {
                            "type": "cluster",
                            "cluster_type": cluster_type,
                            "size": len(cluster_nodes),
                            "nodes": cluster_nodes,
                        }
                    )

        return clusters


pattern_matcher = PatternMatcher()
structure_matcher = StructureMatcher()
