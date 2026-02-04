# app/graph/checkpointer.py
from __future__ import annotations

from typing import Optional

try:
    from langgraph.checkpoint.memory import MemorySaver
except Exception:  # pragma: no cover
    MemorySaver = None  # type: ignore


def get_checkpointer(mode: str = "memory", sqlite_path: Optional[str] = None):
    """
    mode:
      - "memory": 서버 재시작 시 run state 소멸 (개발용)
      - "sqlite": sqlite_path 지정 시 파일로 저장 (간단한 영속)
    """
    if mode == "memory":
        if MemorySaver is None:
            raise RuntimeError(
                "MemorySaver import failed. Please check langgraph version."
            )
        return MemorySaver()

    if mode == "sqlite":
        if not sqlite_path:
            raise ValueError("sqlite_path is required when mode='sqlite'")
        # (질문) SQLiteSaver를 쓸지 여부는 langgraph 버전에 따라 달라요.
        # 보통은 아래처럼 사용합니다.
        from langgraph.checkpoint.sqlite import SqliteSaver  # type: ignore

        return SqliteSaver.from_conn_string(f"sqlite:///{sqlite_path}")

    raise ValueError(f"Unknown checkpointer mode: {mode}")
