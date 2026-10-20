# Логирование Django

Настройку выполняет Django через `LOGGING` в `config/settings.py`.
`build_logging(BASE_DIR, DEBUG)` строит стандартный словарь конфигурации.
`.env` загружается в settings, повторной загрузки и настройки при импорте нет.

## Использование

```python
import logging

logger = logging.getLogger(__name__)
logger.info("Пользователь создан", extra={"user_id": 42})

try:
    do_something()
except Exception:
    logger.exception("Ошибка обработки")
```

Рекомендуется создавать логгер через `logging.getLogger(__name__)` в каждом модуле.
При нескольких Django-приложениях имена получатся автоматически: `users.views`,
`orders.services`, `payments.tasks`. По имени логгера видно источник сообщения.
Все они используют общие обработчики; регистрировать каждое приложение в `LOGGING`
не требуется.

Для короткого импорта доступен `from config.logger import log` — общий логгер
с именем `main_app`. Это только имя логгера, приложение с таким именем не требуется.
При таком импорте имя логгера одинаково во всех модулях.

Это стандартный `logging.Logger`: ключи `extra` не должны совпадать со стандартными
полями `LogRecord` (`name`, `message`, `levelname` и т. п.).

## Файлы и уровни

| Назначение | Текст | JSON |
| --- | --- | --- |
| DEBUG и INFO | `logs/app.log` | `logs/app.json.log` |
| WARNING, ERROR и CRITICAL | `logs/error.log` | `logs/error.json.log` |

В консоль (stderr) идут все сообщения от настроенного уровня.
По умолчанию уровень DEBUG при `DEBUG=True`, иначе INFO; `LOG_LEVEL` переопределяет его
для консоли и файлов. Traceback сохраняется при `logger.exception(...)`.
JSON содержит по одной записи на строку, контекст и `extra`.

Ротация — в полночь, хранится до 14 архивов каждого файла. Каталоги создаются
автоматически, сами файлы — при первой записи. Относительные пути считаются от
`BASE_DIR`, поэтому смена рабочей директории не меняет расположение логов.

Все переменные приведены в `env.example`: `LOG_CONSOLE`, `LOG_CONSOLE_FORMAT`,
`LOG_FILE_TEXT`, `LOG_FILE_JSON`, пути файлов, уровень, формат даты и параметры
ротации. Чтобы полностью отключить вывод, выставьте три переключателя в False.
Неправильный уровень или формат консоли вызывает ошибку конфигурации при запуске.

Логгеры Django (включая `django.request` и `django.server`) передают записи общим
обработчикам. Штатные консольный обработчик Django и отправка ошибок через
`mail_admins` заменены этой конфигурацией. Настройка логов процесса Gunicorn
выполняется отдельно в параметрах сервера.

`TimedRotatingFileHandler` рассчитан на один процесс, записывающий файлы.
Для нескольких workers отключайте файловый вывод и собирайте stderr средствами
Docker/systemd либо используйте отдельную систему сбора логов.

## Контекст

```python
from config.logger import log
from config.logger.context import clear_context, set_context

set_context(request_id="req-42", user_id=42)
try:
    log.info("Обработка запроса")
    log.info("Другая операция", extra={"user_id": 43})
finally:
    clear_context()
```

Контекст изолирован по потокам и async-задачам. `extra` имеет приоритет над
контекстом; базовые поля JSON (`level`, `logger`, `message`, и т. д.) сохраняются.
Автоматического заполнения или очистки контекста на HTTP-запросе нет: задавайте
его явно и очищайте в `finally`. Не храните в контексте объекты Request и пароли.

Доступны `get_context`, `set_context`, `set_context_dict`, `remove_context`,
`clear_context`, `set_request_id` и `get_request_id`.

## Структура

- `__init__.py` — короткий импорт стандартного логгера.
- `config.py` — словарь `LOGGING` из переменных окружения.
- `handlers.py` — разделение уровней и создание каталога логов.
- `formatters.py` — текстовый и JSON-форматтеры.
- `context.py` — произвольный контекст через `contextvars`.
- `tests/` — проверки интеграции с Django и форматов; PostgreSQL не требуется.
