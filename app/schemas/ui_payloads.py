from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class CreateSessionRequest(BaseModel):
    raw_text: Optional[str] = None


class CreateSessionResponse(BaseModel):
    run_id: str
    state: Dict[str, Any]


class CorpCenterStepRequest(BaseModel):
    corporation: str
    centers: List[str]


class StepResponse(BaseModel):
    run_id: str
    state: Dict[str, Any]
    next_step: Optional[str] = None
    message: Optional[str] = None


class NetworksStepRequest(BaseModel):
    # 센터별 zone 입력(자유 텍스트)
    center_zones: Dict[str, str]  # {"의왕":"내부망, DMZ망", "안성":"내부망, DMZ망"}
    # 센터별 장비 입력(자유 텍스트)
    center_devices: Optional[Dict[str, str]] = (
        None  # {"의왕":"외부GSLB, SK회선,...", "안성":""}
    )

    # 센터 외 네트워크(선택)
    external_networks: Optional[List[dict]] = None
    # 예: [{"name":"중계기관", "zones":"대외망"}]  zones도 자유텍스트로 받아도 됨


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
