"""Фильтр уровней и файловый обработчик с созданием каталога."""

import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


class MaxLevelFilter(logging.Filter):
    """DEBUG/INFO идут в app.*, WARNING и выше — в error.*."""

    def __init__(self, max_level: int = logging.INFO):
        super().__init__()
        self.max_level = max_level

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno <= self.max_level


class RotatingFileHandler(TimedRotatingFileHandler):
    def __init__(self, filename, **kwargs):
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        super().__init__(filename, **kwargs)
