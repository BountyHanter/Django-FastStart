"""Контекст логов, изолированный по потокам и async-задачам.

Контекст добавляется форматтерами; extra имеет приоритет.
Очищайте его в finally после обработки запроса или фоновой задачи.
"""

from contextvars import ContextVar
from typing import Any

_log_context: ContextVar[dict[str, Any] | None] = ContextVar("log_context", default=None)


def get_context() -> dict[str, Any]:
    return dict(_log_context.get() or {})


def set_context(**kwargs: Any) -> None:
    ctx = get_context()
    ctx.update({key: value for key, value in kwargs.items() if value is not None})
    _log_context.set(ctx)


def set_context_dict(data: dict[str, Any]) -> None:
    _log_context.set(dict(data))


def remove_context(*keys: str) -> None:
    ctx = get_context()
    for key in keys:
        ctx.pop(key, None)
    _log_context.set(ctx)


def clear_context() -> None:
    _log_context.set({})


def set_request_id(request_id: str | None) -> None:
    if request_id is None:
        remove_context("request_id")
    else:
        set_context(request_id=request_id)


def get_request_id() -> str | None:
    return get_context().get("request_id")
