#!/usr/bin/env bash
set -euo pipefail

# всегда запускаемся из директории скрипта
cd "$(dirname "$0")"

# нормализуем PATH для systemd/docker/webhook
export PATH="$PATH:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"


PROJECT_DIR="/var/www/Project" # Вставь путь к проекту
HEALTH_URL="http://127.0.0.1:8000/api/v1/health/"
CHAT_ID="123456" # Айди чата куда слать уведомления

# ===== ВСТАВЬ СЮДА ТОКЕН =====
BOT_TOKEN=""

send_tg () {
  MESSAGE=$1

  curl -v -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
       -d chat_id="${CHAT_ID}" \
       -d text="${MESSAGE}" \
       -d parse_mode="HTML" > /dev/null
}

echo "=== НАЧАЛО ДЕПЛОЯ ==="

cd $PROJECT_DIR

echo "Получение изменений из репозитория..."
git pull origin main

echo "Пересборка контейнеров..."
docker compose build

echo "Запуск контейнеров..."
docker compose up -d

echo "Ожидание запуска приложения..."
sleep 10

# ===== ПРОВЕРКА HEALTH =====

ATTEMPTS=10
SUCCESS=false

for i in $(seq 1 $ATTEMPTS); do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL || true)

    if [ "$STATUS" = "200" ]; then
        SUCCESS=true
        break
    fi

    echo "Попытка health-check $i провалилась..."
    sleep 3
done

# ===== РЕЗУЛЬТАТ =====

if [ "$SUCCESS" = true ]; then
    echo "Деплой успешно завершён"
else
    echo "Деплой провален"

    send_tg "❌ ДЕПЛОЙ ПРОВАЛЕН

Проект: !!!ЗАМЕНИ НАЗВАНИЕ!!!
Этап: Проверка health-check
Сервер: $(hostname)
Время: $(date '+%Y-%m-%d %H:%M:%S')"

    exit 1
fi

echo "Очистка старых образов..."
docker image prune -f

echo "=== ДЕПЛОЙ ЗАВЕРШЁН ==="