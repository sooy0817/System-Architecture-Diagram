from typing import Dict, Any, List
from graph.state import NodeType
from core.logging import get_logger

logger = get_logger(__name__)


class ReviewNode:
    """Handles diagram review and validation"""

    def __init__(self):
        self.node_type = NodeType.REVIEW

    def execute(self, session_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute review step"""
        logger.info(f"Executing review step for session {session_id}")

        review_data = input_data.get("review_data", {})

        result = {
            "validation_results": self._validate_diagram(review_data),
            "suggestions": self._generate_suggestions(review_data),
            "quality_score": self._calculate_quality_score(review_data),
            "status": "reviewed",
        }

        return result

    def _validate_diagram(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate diagram structure and content"""
        validations = []

        # Check for required elements
        if not data.get("nodes"):
            validations.append(
                {"type": "error", "message": "No nodes found in diagram"}
            )

        if not data.get("edges"):
            validations.append(
                {"type": "warning", "message": "No edges found in diagram"}
            )

        return validations

    def _generate_suggestions(self, data: Dict[str, Any]) -> List[str]:
        """Generate improvement suggestions"""
        suggestions = []

        node_count = len(data.get("nodes", []))
        if node_count > 20:
            suggestions.append("Consider grouping nodes to reduce complexity")

        return suggestions

    def _calculate_quality_score(self, data: Dict[str, Any]) -> float:
        """Calculate diagram quality score"""
        score = 100.0

        # Deduct points for issues
        validations = self._validate_diagram(data)
        for validation in validations:
            if validation["type"] == "error":
                score -= 20
            elif validation["type"] == "warning":
                score -= 10

        return max(0.0, score)

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for this node"""
        return "review_data" in input_data
