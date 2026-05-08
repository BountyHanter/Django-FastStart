# AvitoBulkDeliv

Базовый Django-проект с PostgreSQL, настройками окружения через `.env`, Docker Compose для базы данных, pytest-конфигурацией и заготовками для DRF/JWT, CORS/CSRF/session, SSL/HTTPS, email и логирования.

## Структура проекта

- `config/` - настройки Django, URL, WSGI/ASGI и вспомогательные утилиты.
- `static/` - статические файлы для dev-режима.
- `media/` - пользовательские файлы.
- `templates/` - HTML-шаблоны.
- `env.example` - пример переменных окружения.
- `docker-compose.yml` - PostgreSQL 16 в Docker.
- `pytest.ini` и `conftest.py` - базовая конфигурация тестов.
- `logs/` - создается автоматически, сюда пишется `app.log`.

## Быстрый старт

### 1. Подготовка окружения

```bash
git clone <url_репозитория>
cd AvitoBulkDeliv

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

Для Windows активация окружения:

```bash
.venv\Scripts\activate
```

### 2. Настройка `.env`

Создайте файл окружения:

```bash
cp env.example .env
```

Минимально проверьте и заполните:

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

`config/settings.py` сейчас использует PostgreSQL по умолчанию. Если Django запускается локально, а база поднята через Docker, оставьте `DB_HOST=localhost`. Если Django будет запускаться внутри Docker-сети рядом с сервисом `db`, используйте `DB_HOST=db`.

### 3. Запуск PostgreSQL

```bash
docker-compose up -d
```

`docker-compose.yml` пробрасывает PostgreSQL только на `127.0.0.1:${DB_PORT}:5432`, поэтому внешний порт берется из `.env`.

### 4. Миграции и запуск Django

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Проект будет доступен по адресу:

```text
http://127.0.0.1:8000/
```

## Тесты

В зависимостях добавлен `pytest-django`, а `pytest.ini` уже указывает `DJANGO_SETTINGS_MODULE = config.settings`.

Запуск тестов:

```bash
pytest
```

Тестовая база для PostgreSQL задана как `test_db` в `config/settings.py`.

## Опциональные возможности

### DRF и JWT

В `requirements.txt` подготовлены закомментированные зависимости:

```text
#djangorestframework==3.17.1
#djangorestframework-simplejwt==5.5.1
```

Чтобы включить API на DRF:

1. Раскомментируйте и установите зависимости.
2. Добавьте `rest_framework` в `INSTALLED_APPS`.
3. При использовании blacklist для JWT добавьте `rest_framework_simplejwt.token_blacklist`.
4. Раскомментируйте блоки `REST_FRAMEWORK` и `SIMPLE_JWT` в `config/settings.py`.

По умолчанию заготовка JWT использует access-токен на 30 минут и refresh-токен на 30 дней.

### CORS, CSRF и cookies

Для CORS подготовлены:

```text
#django-cors-headers==4.9.0
```

И закомментированные настройки в `config/settings.py`. При включении:

1. Раскомментируйте зависимость и установите ее.
2. Добавьте `corsheaders` в `INSTALLED_APPS`.
3. Раскомментируйте `corsheaders.middleware.CorsMiddleware` в `MIDDLEWARE`.
4. Раскомментируйте production-блок CORS/CSRF/SESSION.
5. Заполните `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS` и cookie-настройки в `.env`.

В production-блоке cookie-параметры зависят от `USE_SSL`: при HTTPS используется `SameSite=None`, при HTTP - `Lax`.

### SSL/HTTPS

В `config/settings.py` есть готовый закомментированный блок для production:

- `SECURE_SSL_REDIRECT`
- `SECURE_HSTS_SECONDS`
- `SECURE_HSTS_INCLUDE_SUBDOMAINS`
- `SECURE_HSTS_PRELOAD`
- `SECURE_PROXY_SSL_HEADER`
- исключение редиректа для `api/v1/health/`

Включайте его только за HTTPS/proxy-инфраструктурой.

### Email

В `env.example` добавлены переменные:

```env
EMAIL_HOST=
EMAIL_PORT=
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_SSL=
```

В `config/settings.py` есть закомментированный SMTP-блок. При включении также укажите `FRONTEND_URL`, если письма содержат ссылки на фронтенд.

## Логирование

Логи пишутся в консоль и в файл:

```text
logs/app.log
```

Файловый логгер использует ежедневную ротацию и хранит архивы за 14 дней. Уровень обработчиков зависит от `DEBUG`: `DEBUG` в dev и `INFO` в production. Корневой логгер и логгер `users` настроены на `INFO`.

## Полезные команды

```bash
docker-compose logs -f db
docker-compose down
python manage.py collectstatic
pytest
```

