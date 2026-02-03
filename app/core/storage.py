from __future__ import annotations
import uuid
from threading import Lock
from typing import Any, Dict


class InMemoryStore:
    def __init__(self):
        self._lock = Lock()
        self._data: Dict[str, Dict[str, Any]] = {}

    def new_run_id(self) -> str:
        return f"run-{uuid.uuid4().hex[:16]}"

    def get(self, run_id: str) -> Dict[str, Any]:
        with self._lock:
            return (self._data.get(run_id) or {}).copy()

    def set(self, run_id: str, state: Dict[str, Any]) -> None:
        with self._lock:
            self._data[run_id] = state.copy()


store = InMemoryStore()
