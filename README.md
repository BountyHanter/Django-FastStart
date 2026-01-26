# Django Fast Start

Это базовый шаблон для быстрого старта проекта на Django. В нем уже настроены основные папки, подключены переменные окружения и подготовлен Docker Compose для базы данных PostgreSQL.

## Структура проекта

- `config/` — настройки Django (settings, urls, wsgi, asgi).
- `static/` — статические файлы (CSS, JS, изображения).
- `media/` — файлы, загружаемые пользователями.
- `templates/` — HTML-шаблоны.
- `env.example` — пример файла с переменными окружения.
- `docker-compose.yml` — конфигурация для запуска PostgreSQL в Docker.

---

## Быстрый старт

### 1. Подготовка окружения
Клонируйте репозиторий и перейдите в папку проекта:
```bash
git clone <url_репозитория>
cd DjangoFastStart
```

Создайте виртуальное окружение и активируйте его:
```bash
python -m venv venv

# Для Linux/macOS:
source venv/bin/activate

# Для Windows:
venv\Scripts\activate
```

Установите зависимости:
```bash
pip install -r requirements.txt
```

### 2. Настройка переменных окружения
Создайте файл `.env` на основе `env.example`:
```bash
cp env.example .env
```
Откройте `.env` и укажите свои данные (или оставьте для теста те, что есть).

### 3. Настройка базы данных (PostgreSQL)

Проект настроен так, что базу данных можно запустить через Docker.

**Запуск БД:**
```bash
docker-compose up -d
```
После этого PostgreSQL будет доступен на порту `6000` (как указано в `docker-compose.yml`).

**Подключение PostgreSQL в Django:**
В файле `config/settings.py` найдите секцию `DATABASES`. Закомментируйте стандартный блок для `sqlite3` и раскомментируйте блок для `postgresql`.

*Не забудьте установить драйвер для PostgreSQL (если его нет в requirements):*
```bash
pip install psycopg2-binary
```

### 4. Применение миграций и запуск
Создайте таблицы в базе данных:
```bash
python manage.py migrate
```

Создайте суперпользователя:
```bash
python manage.py createsuperuser
```

Запустите сервер разработки:
```bash
python manage.py runserver
```

Проект будет доступен по адресу: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

## Что можно добавить еще (рекомендации)

Если проект будет расти, вот что обычно ставят в дополнение:

1.  **Django Rest Framework (DRF)** — если нужно делать API.
    - `pip install djangorestframework`
2.  **Celery + Redis** — для фоновых задач (рассылка писем, тяжелая обработка данных).
    - Потребуется добавить Redis в `docker-compose.yml`.

---

## Полезные команды

- `docker-compose logs -f db` — просмотр логов базы данных.
- `docker-compose down` — остановить и удалить контейнеры с БД.
- `python manage.py collectstatic` — собрать всю статику в одну папку (перед деплоем).

---