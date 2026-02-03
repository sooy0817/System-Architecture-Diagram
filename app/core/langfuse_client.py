from __future__ import annotations

from app.core.settings import settings

_handler = None


def get_langfuse_handler():
    """
    Langfuse 키가 없으면 None 반환 -> tracing 없이 동작
    """
    global _handler

    if not settings.LANGFUSE_PUBLIC_KEY or not settings.LANGFUSE_SECRET_KEY:
        return None

    if _handler is None:
        # langfuse>=2 + langfuse-langchain 환경 가정
        from langfuse.langchain import CallbackHandler

        _handler = CallbackHandler()
    return _handler
