from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

router = APIRouter()


@router.post("/{session_id}/export")
async def export_diagram(session_id: str):
    """Export diagram in various formats"""
    pass


@router.get("/{session_id}/export/formats")
async def get_export_formats(session_id: str):
    """Get available export formats"""
    pass
