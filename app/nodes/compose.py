from typing import Dict, Any
from graph.state import NodeType
from core.logging import get_logger

logger = get_logger(__name__)


class ComposeNode:
    """Handles composition of diagram elements"""

    def __init__(self):
        self.node_type = NodeType.COMPOSE

    def execute(self, session_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute compose step"""
        logger.info(f"Executing compose step for session {session_id}")

        composition_data = input_data.get("composition_data", {})

        result = {
            "composed_elements": self._compose_elements(composition_data),
            "layout": composition_data.get("layout", "hierarchical"),
            "styling": composition_data.get("styling", {}),
            "status": "composed",
        }

        return result

    def _compose_elements(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Compose diagram elements"""
        elements = data.get("elements", [])

        composed = {"nodes": [], "edges": [], "groups": []}

        for element in elements:
            element_type = element.get("type")
            if element_type == "node":
                composed["nodes"].append(element)
            elif element_type == "edge":
                composed["edges"].append(element)
            elif element_type == "group":
                composed["groups"].append(element)

        return composed

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for this node"""
        return "composition_data" in input_data
