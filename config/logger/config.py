"""Конфигурация стандартного logging для Django.

В каждом модуле приложения, где нужны логи, пишите:
    import logging
    logger = logging.getLogger(__name__)

Имена вроде users.views и orders.services получатся автоматически.
Регистрировать каждое приложение в LOGGING не требуется.
"""

import logging
import os
from pathlib import Path


def _env(name: str, default: str) -> str:
    return os.getenv(name) or default


def _enabled(name: str, default: bool = True) -> bool:
    return _env(name, str(default)).lower() in {"true", "1", "yes", "y", "on"}


def build_logging(base_dir: Path, debug: bool = False) -> dict:
    """Строит LOGGING без создания обработчиков или повторной загрузки .env."""
    level = _env("LOG_LEVEL", "DEBUG" if debug else "INFO").upper()
    if level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise ValueError(f"Unsupported LOG_LEVEL: {level}")
    console_format = _env("LOG_CONSOLE_FORMAT", "text").lower()
    if console_format not in {"text", "json"}:
        raise ValueError("LOG_CONSOLE_FORMAT must be text or json")

    handlers = {}
    if _enabled("LOG_CONSOLE"):
        handlers["console"] = {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
            "level": level,
            "formatter": console_format,
        }

    for kind, suffix in (("text", "log"), ("json", "json.log")):
        if not _enabled(f"LOG_FILE_{kind.upper()}"):
            continue
        for is_error in (False, True):
            env_name = f"LOG_FILE_{kind.upper()}_{'ERROR_' if is_error else ''}PATH"
            path = Path(_env(env_name, f"logs/{'error' if is_error else 'app'}.{suffix}"))
            if not path.is_absolute():
                path = base_dir / path
            handlers[f"{kind}_{'error' if is_error else 'app'}"] = {
                "class": "config.logger.handlers.RotatingFileHandler",
                "filename": str(path),
                "level": max(getattr(logging, level), logging.WARNING) if is_error else level,
                "formatter": kind,
                "filters": [] if is_error else ["max_info"],
                "when": _env("LOG_ROTATION_WHEN", "midnight"),
                "interval": int(_env("LOG_ROTATION_INTERVAL", "1")),
                "backupCount": int(_env("LOG_ROTATION_BACKUP", "14")),
                "utc": _enabled("LOG_ROTATION_UTC", False),
                "encoding": "utf-8",
                "delay": True,
            }

    if not handlers:
        handlers["null"] = {"class": "logging.NullHandler"}

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {"max_info": {"()": "config.logger.handlers.MaxLevelFilter"}},
        "formatters": {
            "text": {
                "()": "config.logger.formatters.TextFormatter",
                "fmt": _env("LOG_TEXT_FMT", "%(asctime)s | %(levelname)s | %(name)s | %(message)s | %(filename)s:%(lineno)d"),
                "datefmt": _env("LOG_DATEFMT", "%Y-%m-%d %H:%M:%S"),
            },
            "json": {
                "()": "config.logger.formatters.JsonFormatter",
                "ts_key": _env("LOG_JSON_TS_KEY", "ts"),
                "datefmt": _env("LOG_DATEFMT", "%Y-%m-%d %H:%M:%S"),
            },
        },
        "handlers": handlers,
        "root": {"handlers": list(handlers), "level": level},
        "loggers": {
            name: {"handlers": [], "level": level, "propagate": True}
            for name in ("django", "django.server", "django.request", "main_app")
        },
    }
