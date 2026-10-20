# Django-FastStart

Подготовленный шаблон Django-проекта для быстрого старта нового приложения. Он собран так, чтобы не каждый раз заново настраивать окружение, деплой, базу данных, логирование и стартовую инфраструктуру. В репозитории уже есть:

- Django 5.2.x
- PostgreSQL 16 через Docker Compose
- `.env`-конфигурация через `python-dotenv`
- скрипт генерации `SECRET_KEY`
- pytest-конфигурация
- файловое и консольное логирование с ротацией
- `entrypoint.sh` для запуска в контейнере
- `deploy.sh` как заготовка для ручного деплоя на сервер

## Что входит в проект

- `manage.py` - точка входа для Django management-команд.
- `config/settings.py` - настройки Django, БД, статики, медиа и логирования.
- `config/urls.py` - URL-конфигурация проекта.
- `config/logger/` - кастомные форматтеры и contextvars для логов.
- `config/utils/` - вспомогательные заготовки для health-check, JWT, пагинации и отладочного вывода в тестах.
- `docker-compose.yml` - контейнер PostgreSQL.
- `entrypoint.sh` - ожидание БД, миграции, collectstatic и запуск приложения.
- `deploy.sh` - сценарий деплоя с `git pull`, пересборкой Docker-образов и health-check.
- `generate_secret_key.py` - обновление `SECRET_KEY` в `.env`.
- `pytest.ini` и `conftest.py` - минимальная конфигурация тестов.
- `env.example` - пример переменных окружения.

## Требования

- Python 3.11+ рекомендуется
- Docker и Docker Compose
- PostgreSQL, если запускаете БД не через Docker

## Быстрый старт

### 1. Клонировать и установить зависимости

```bash
git clone <url_репозитория>
cd Django-FastStart

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

Для Windows:

```bash
.venv\Scripts\activate
```

### 2. Создать `.env`

```bash
cp env.example .env
```

Минимально проверьте переменные:

```env
SECRET_KEY=django-insecure-...
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=example_db
DB_USER=example_user
DB_PASSWORD=example_password
DB_HOST=localhost
DB_PORT=5432
```

Важно:

- Если Django запускается локально, а PostgreSQL поднят в Docker, оставьте `DB_HOST=localhost`.
- Если Django запускается внутри Docker-сети рядом с сервисом `db`, используйте `DB_HOST=db`.
- Если `SECRET_KEY` нужно обновить, используйте `python generate_secret_key.py` (оно сразу установит key в .env).

### 3. Поднять PostgreSQL

```bash
docker compose up -d
```

`docker-compose.yml` пробрасывает БД только на `127.0.0.1:${DB_PORT}:5432`.

### 4. Применить миграции и запустить проект

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Проект будет доступен по адресу:

```text
http://127.0.0.1:8000/
```

Админка:

```text
http://127.0.0.1:8000/admin/
```

## Запуск в Docker

`entrypoint.sh` предназначен для контейнера приложения. Он:

1. ждёт доступность PostgreSQL;
2. выполняет `python manage.py migrate --noinput`;
3. выполняет `python manage.py collectstatic --noinput`;
4. запускает команду, переданную контейнеру.

Обычно это используется вместе с отдельным контейнером для Django-приложения.

## Генерация `SECRET_KEY`

Скрипт `generate_secret_key.py` обновляет строку `SECRET_KEY=` в `.env`.

Запуск:

```bash
python generate_secret_key.py
```

Требования:

- файл `.env` должен существовать;
- в `.env` должна быть строка `SECRET_KEY=...`.

## Тесты

В проекте подключён `pytest-django`.

Конфигурация:

- `pytest.ini` задаёт `DJANGO_SETTINGS_MODULE = config.settings`
- шаблон для вспомогательных фикстур лежит в `conftest.py`

Запуск:

```bash
pytest
```

Прикладных тестов пока нет. В `config/logger/tests/` есть тесты настройки Django, маршрутизации логов, форматтеров и контекста; база данных для них не нужна.

## Логирование

Django подключает логирование через `LOGGING = build_logging(BASE_DIR, DEBUG)` в
`config/settings.py`. Конфигурация находится в `config/logger/config.py`.
Импорт пакета не создаёт файлов или обработчиков.

По умолчанию доступны:

- консоль (stderr);
- `logs/app.log` и `logs/app.json.log` — DEBUG/INFO;
- `logs/error.log` и `logs/error.json.log` — WARNING/ERROR/CRITICAL;
- ротация в полночь, по 14 архивов каждого файла.

При `DEBUG=True` уровень по умолчанию DEBUG, иначе INFO. Настройки в `.env`
позволяют менять уровень, форматы, пути и ротацию (см. `env.example`).
Относительные пути отсчитываются от корня проекта.
Логи Django и приложений проходят через общие обработчики без дублирования.

```python
import logging

logger = logging.getLogger(__name__)
logger.info("Пользователь создан", extra={"user_id": 42})
```

Рекомендуемый способ для каждого модуля, в том числе при нескольких Django-приложениях,
— `logging.getLogger(__name__)`. Имена логгеров автоматически соответствуют модулям:
`users.views`, `orders.services`, `payments.tasks`. По имени в записи видно источник
сообщения. Все эти логгеры используют общие обработчики; добавлять каждое приложение
в настройки логирования не нужно.

Также доступен `from config.logger import log` — общий стандартный логгер с именем
`main_app`. Это только имя логгера, а не требование создать приложение `main_app`.
Такой импорт удобен для общих сообщений, но не различает модули по имени логгера.

Контекст через `contextvars`, примеры и ограничения описаны в
[config/logger/Readme.md](config/logger/Readme.md).

## Настройки Django

### База данных

По умолчанию используется PostgreSQL:

- `ENGINE = django.db.backends.postgresql`
- `NAME`, `USER`, `PASSWORD` берутся из `.env`
- `HOST` по умолчанию равен `db`
- `PORT` по умолчанию равен `5432`

### Статика и медиа

- `STATIC_URL = /static/`
- `STATICFILES_DIRS = [BASE_DIR / "static"]`
- `STATIC_ROOT = BASE_DIR / "staticfiles"`
- `MEDIA_URL = /media/`
- `MEDIA_ROOT = BASE_DIR / "media"`

### Локаль

- `LANGUAGE_CODE = ru`
- `TIME_ZONE = Europe/Moscow`
- `USE_I18N = True`
- `USE_TZ = True`

### Тип первичного ключа

- `DEFAULT_AUTO_FIELD = django.db.models.BigAutoField`

## Заготовки и потенциальные расширения

В проекте уже лежат подготовленные, но не включённые по умолчанию блоки. Это не активный функционал, а шаблоны для быстрого включения при необходимости.

### DRF и JWT

В `requirements.txt` есть закомментированные зависимости:

- `djangorestframework`
- `djangorestframework-simplejwt`

В `config/settings.py` подготовлены:

- `REST_FRAMEWORK`
- `SIMPLE_JWT`
- опциональное подключение `rest_framework_simplejwt.token_blacklist`

### CORS, CSRF и session cookies

В `requirements.txt` и `config/settings.py` есть заготовки для:

- `django-cors-headers`
- `CORS_ALLOWED_ORIGINS`
- `CORS_ALLOW_ALL_ORIGINS`
- `CSRF_TRUSTED_ORIGINS`
- `CSRF_COOKIE_*`
- `SESSION_COOKIE_*`

### HTTPS / SSL

В `config/settings.py` есть закомментированный блок для production-режима:

- `SECURE_SSL_REDIRECT`
- `SECURE_REDIRECT_EXEMPT`
- `SECURE_HSTS_SECONDS`
- `SECURE_HSTS_INCLUDE_SUBDOMAINS`
- `SECURE_HSTS_PRELOAD`
- `SECURE_PROXY_SSL_HEADER`

### Email

В `config/settings.py` и `env.example` подготовлены переменные и блок SMTP:

- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `EMAIL_USE_SSL`
- `FRONTEND_URL`

### Health-check и утилиты

В `config/utils/` лежат вспомогательные заготовки:

- `health.py` - health-check view для проверки БД
- `jwt_token.py` - выдача пары токенов JWT
- `pagination.py` - базовая пагинация для DRF
- `test_print.py` - отладочный вывод ответа в тестах

### Логирование

Дополнительно в проекте есть готовая логика для:

- контекста логирования через `contextvars`
- текстового formatter
- JSON formatter
- файлового логирования с ротацией

## Деплой

`deploy.sh` - это шаблон деплой-скрипта для сервера. Он делает следующее:

1. переходит в директорию проекта;
2. выполняет `git pull origin main`;
3. пересобирает контейнеры через `docker compose build`;
4. поднимает контейнеры через `docker compose up -d`;
5. ждёт доступность health-check;
6. при неудаче отправляет уведомление в Telegram;
7. в конце очищает старые образы командой `docker image prune -f`.

Что нужно заполнить вручную в `deploy.sh`:

- `PROJECT_DIR`
- `HEALTH_URL`
- `CHAT_ID`
- `BOT_TOKEN`

Важно:

- в текущем виде скрипт является заготовкой и требует настройки под конкретный сервер;
- health-check URL должен существовать в вашем проекте, если вы хотите использовать этот сценарий как есть.
- У меня в GitHub есть готовый deploy service, который принимает вебхуки от GitHub и автоматически запускает deploy.sh для соответствующего проекта. Для корректной работы важно, чтобы название директории с проектом совпадало с названием проекта в GitHub, в самом GitHub были настроены вебхуки на события коммита, а в проекте были заполнены все необходимые переменные окружения.

## Полезные команды

```bash
python manage.py check
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
python manage.py collectstatic
pytest
docker compose logs -f db
docker compose down
```
