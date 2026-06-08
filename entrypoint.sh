#!/bin/sh

DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
DB_WAIT_TIMEOUT="${DB_WAIT_TIMEOUT:-60}"

case "$DB_WAIT_TIMEOUT" in
  0|*[!0-9]*)
    echo "DB_WAIT_TIMEOUT must be a positive integer" >&2
    exit 1
    ;;
esac

echo "Waiting for postgres at ${DB_HOST}:${DB_PORT}..."

elapsed=0
while ! nc -z "$DB_HOST" "$DB_PORT"; do
  elapsed=$((elapsed + 1))
  if [ "$elapsed" -ge "$DB_WAIT_TIMEOUT" ]; then
    echo "Postgres is unavailable after ${DB_WAIT_TIMEOUT}s" >&2
    exit 1
  fi
  sleep 1
done

echo "Postgres started"

echo "Applying migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting server..."
exec "$@"
