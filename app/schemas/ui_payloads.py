# app/schemas/ui_payloads.py
from __future__ import annotations
from pydantic import BaseModel
from typing import Any, Dict, List, Optional


class CreateSessionRequest(BaseModel):
    raw_text: Optional[str] = None


class CreateSessionResponse(BaseModel):
    run_id: str
    state: Dict[str, Any]


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant" | "system"
    content: str
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    run_id: str
    messages: List[ChatMessage]
    current_step: str
    next_step: Optional[str] = None
    state: Dict[str, Any]
    ui_data: Optional[Dict[str, Any]] = None  # 추가 UI 표시용 데이터


# 기존 스키마들은 내부 처리용으로 유지
class CorpCenterStepRequest(BaseModel):
    corporation: str
    centers: List[str]


class StepResponse(BaseModel):
    run_id: str
    state: Dict[str, Any]
    next_step: Optional[str] = None
    message: Optional[str] = None


class NetworksStepRequest(BaseModel):
    center_zones: Dict[str, str]
    center_devices: Optional[Dict[str, str]] = None
    external_networks: Optional[List[dict]] = None


class NextScopeResponse(BaseModel):
    run_id: str
    current_scope: Optional[Dict[str, Any]]
    remaining: int
    next_step: str
    message: str
    state: Dict[str, Any]


class ScopeDetailRequest(BaseModel):
    detail_text: str


class ScopeDetailResponse(BaseModel):
    run_id: str
    current_scope: dict | None
    remaining: int
    next_step: str
    message: str
    state: Dict[str, Any]


class EdgesRequest(BaseModel):
    edge_text: str


class EdgesResponse(BaseModel):
    run_id: str
    next_step: str
    message: str
    state: Dict[str, Any]
