from typing import Dict, Any, List
from graph.state import NodeType
from core.logging import get_logger
import json

logger = get_logger(__name__)


class ExportNode:
    """Handles diagram export operations"""

    def __init__(self):
        self.node_type = NodeType.EXPORT
        self.supported_formats = ["json", "svg", "png", "pdf", "mermaid"]

    def execute(self, session_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute export step"""
        logger.info(f"Executing export step for session {session_id}")

        export_config = input_data.get("export_config", {})
        format_type = export_config.get("format", "json")

        result = {
            "exported_data": self._export_diagram(input_data, format_type),
            "format": format_type,
            "file_size": 0,  # Would be calculated in real implementation
            "status": "exported",
        }

        return result

    def _export_diagram(self, data: Dict[str, Any], format_type: str) -> str:
        """Export diagram in specified format"""
        if format_type == "json":
            return json.dumps(data, indent=2)
        elif format_type == "mermaid":
            return self._export_to_mermaid(data)
        elif format_type in ["svg", "png", "pdf"]:
            return f"<{format_type} export placeholder>"
        else:
            raise ValueError(f"Unsupported export format: {format_type}")

    def _export_to_mermaid(self, data: Dict[str, Any]) -> str:
        """Export diagram to Mermaid format"""
        mermaid = ["graph TD"]

        # Add nodes
        nodes = data.get("nodes", [])
        for node in nodes:
            node_id = node.get("id", "")
            node_label = node.get("label", node_id)
            mermaid.append(f"    {node_id}[{node_label}]")

        # Add edges
        edges = data.get("edges", [])
        for edge in edges:
            source = edge.get("source", "")
            target = edge.get("target", "")
            if source and target:
                mermaid.append(f"    {source} --> {target}")

        return "\n".join(mermaid)

    def get_supported_formats(self) -> List[str]:
        """Get list of supported export formats"""
        return self.supported_formats

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for this node"""
        export_config = input_data.get("export_config", {})
        format_type = export_config.get("format", "json")
        return format_type in self.supported_formats
