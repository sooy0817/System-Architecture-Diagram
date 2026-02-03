from typing import Dict, Any, List
from graph.state import NodeType
from core.logging import get_logger

logger = get_logger(__name__)


class EdgesNode:
    """Handles edge connections and relationships"""

    def __init__(self):
        self.node_type = NodeType.EDGES

    def execute(self, session_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute edges step"""
        logger.info(f"Executing edges step for session {session_id}")

        edge_config = input_data.get("edge_config", {})

        result = {
            "edges": self._process_edges(edge_config),
            "connections": edge_config.get("connections", []),
            "relationships": edge_config.get("relationships", []),
            "status": "connected",
        }

        return result

    def _process_edges(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process edge configurations"""
        edges = config.get("edges", [])
        processed = []

        for edge in edges:
            processed.append(
                {
                    "id": edge.get("id"),
                    "source": edge.get("source"),
                    "target": edge.get("target"),
                    "type": edge.get("type", "connection"),
                    "weight": edge.get("weight", 1.0),
                    "properties": edge.get("properties", {}),
                }
            )

        return processed

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for this node"""
        return "edge_config" in input_data
