from typing import Dict, Any, List
from graph.state import NodeType
from core.logging import get_logger

logger = get_logger(__name__)


class UserNode:
    """Handles user-related operations"""

    def __init__(self):
        self.node_type = NodeType.USER

    def execute(self, session_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute user step"""
        logger.info(f"Executing user step for session {session_id}")

        user_data = input_data.get("user_data", {})

        result = {
            "users": self._process_users(user_data),
            "roles": user_data.get("roles", []),
            "permissions": user_data.get("permissions", []),
            "status": "processed",
        }

        return result

    def _process_users(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process user data"""
        users = data.get("users", [])
        processed = []

        for user in users:
            processed.append(
                {
                    "id": user.get("id"),
                    "name": user.get("name"),
                    "role": user.get("role", "user"),
                    "department": user.get("department"),
                    "access_level": user.get("access_level", "basic"),
                }
            )

        return processed

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for this node"""
        return "user_data" in input_data
