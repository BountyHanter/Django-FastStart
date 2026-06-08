#!/usr/bin/env bash
set -euo pipefail

# всегда запускаемся из директории скрипта
cd "$(dirname "$0")"
SCRIPT_DIR="$(pwd)"

# нормализуем PATH для systemd/docker/webhook
export PATH="$PATH:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

load_env_var() {
  local name="$1"
  local value

  if [ -n "${!name:-}" ] || [ ! -f ".env" ]; then
    return
  fi

  value="$(grep -m 1 "^${name}=" .env 2>/dev/null | cut -d "=" -f 2- || true)"
  if [ -n "$value" ]; then
    printf -v "$name" "%s" "$value"
    export "$name"
  fi
}

for name in \
  DEPLOY_PROJECT_DIR \
  DEPLOY_BRANCH \
  DEPLOY_HEALTH_URL \
  DEPLOY_PROJECT_NAME \
  DEPLOY_STARTUP_DELAY \
  DEPLOY_HEALTHCHECK_ATTEMPTS \
  DEPLOY_HEALTHCHECK_DELAY \
  TELEGRAM_CHAT_ID \
  TELEGRAM_BOT_TOKEN
do
  load_env_var "$name"
done

PROJECT_DIR="${DEPLOY_PROJECT_DIR:-$SCRIPT_DIR}"
BRANCH="${DEPLOY_BRANCH:-main}"
HEALTH_URL="${DEPLOY_HEALTH_URL:-http://127.0.0.1:8000/api/v1/health/}"
PROJECT_NAME="${DEPLOY_PROJECT_NAME:-$(basename "$PROJECT_DIR")}"
STARTUP_DELAY="${DEPLOY_STARTUP_DELAY:-10}"
ATTEMPTS="${DEPLOY_HEALTHCHECK_ATTEMPTS:-10}"
HEALTHCHECK_DELAY="${DEPLOY_HEALTHCHECK_DELAY:-3}"
CHAT_ID="${TELEGRAM_CHAT_ID:-}"
BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"

require_positive_int() {
  local name="$1"
  local value="$2"

  case "$value" in
    0|*[!0-9]*)
      echo "$name должно быть положительным числом (int)" >&2
      exit 1
      ;;
  esac
}

require_positive_int "DEPLOY_STARTUP_DELAY" "$STARTUP_DELAY"
require_positive_int "DEPLOY_HEALTHCHECK_ATTEMPTS" "$ATTEMPTS"
require_positive_int "DEPLOY_HEALTHCHECK_DELAY" "$HEALTHCHECK_DELAY"

send_tg () {
  local message="$1"

  if [ -z "$BOT_TOKEN" ] || [ -z "$CHAT_ID" ]; then
    echo "Телеграм уведомление не выполнено: TELEGRAM_BOT_TOKEN или TELEGRAM_CHAT_ID не установлены"
    return 0
  fi

  curl -fsS -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
       -d chat_id="${CHAT_ID}" \
       -d text="${message}" \
       -d parse_mode="HTML" > /dev/null
}

echo "=== НАЧАЛО ДЕПЛОЯ ==="

cd "$PROJECT_DIR"

echo "Получение изменений из репозитория..."
git pull origin "$BRANCH"

echo "Пересборка контейнеров..."
docker compose build

echo "Запуск контейнеров..."
docker compose up -d

echo "Ожидание запуска приложения..."
sleep "$STARTUP_DELAY"

# ===== ПРОВЕРКА HEALTH =====

SUCCESS=false

for i in $(seq 1 $ATTEMPTS); do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" || true)

    if [ "$STATUS" = "200" ]; then
        SUCCESS=true
        break
    fi

    echo "Попытка health-check $i провалилась..."
    sleep "$HEALTHCHECK_DELAY"
done

# ===== РЕЗУЛЬТАТ =====

if [ "$SUCCESS" = true ]; then
    echo "Деплой успешно завершён"
else
    echo "Деплой провален"

    send_tg "❌ ДЕПЛОЙ ПРОВАЛЕН

Проект: ${PROJECT_NAME}
Этап: Проверка health-check
Сервер: $(hostname)
Время: $(date '+%Y-%m-%d %H:%M:%S')" || true

    exit 1
fi

echo "Очистка старых образов..."
docker image prune -f

echo "=== ДЕПЛОЙ ЗАВЕРШЁН ==="
