from typing import Dict, Any, List
from graph.state import NodeType
from core.logging import get_logger

logger = get_logger(__name__)


class ZoneDetailNode:
    """Handles detailed zone configuration"""

    def __init__(self):
        self.node_type = NodeType.ZONE_DETAIL

    def execute(self, session_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute zone detail step"""
        logger.info(f"Executing zone detail step for session {session_id}")

        zone_config = input_data.get("zone_config", {})

        result = {
            "zones": self._process_zones(zone_config),
            "security_policies": zone_config.get("security_policies", []),
            "access_rules": zone_config.get("access_rules", []),
            "status": "detailed",
        }

        return result

    def _process_zones(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process zone configurations"""
        zones = config.get("zones", [])
        processed = []

        for zone in zones:
            processed.append(
                {
                    "id": zone.get("id"),
                    "name": zone.get("name"),
                    "type": zone.get("type", "security"),
                    "level": zone.get("level", "medium"),
                    "resources": zone.get("resources", []),
                }
            )

        return processed

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for this node"""
        return "zone_config" in input_data
