"""Логгер проекта; обработчики подключает Django через settings.LOGGING.

В каждом приложении, в начале модулей с логированием (views.py, services.py,
tasks.py и т. п.), рекомендуется писать:

    import logging

    logger = logging.getLogger(__name__)

Далее используйте logger.info(...), logger.warning(...), logger.exception(...).
Имена логгеров будут соответствовать модулям: users.views, orders.services.
Все они используют общие обработчики; добавлять приложения в LOGGING не нужно.

Импорт from config.logger import log даёт общий логгер main_app.
При таком импорте имя логгера одинаково во всех модулях; наличие Django-приложения
с именем main_app не требуется.
"""

import logging

log = logging.getLogger("main_app")

__all__ = ["log"]
