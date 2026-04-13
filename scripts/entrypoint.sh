#!/usr/bin/env sh
set -eu

cd /app/backend

wait_for_redis() {
  echo "Waiting for Redis at ${BLOG_REDIS_URL:-redis://redis:6379/0}..."
  while ! python - <<'PY'
import os
from redis import Redis
from redis.exceptions import RedisError

url = os.getenv("BLOG_REDIS_URL", "redis://redis:6379/0")
try:
    Redis.from_url(url).ping()
except RedisError:
    raise SystemExit(1)
raise SystemExit(0)
PY
  do
    sleep 1
  done
  echo "Redis is ready."
}

run_startup_tasks() {
  mkdir -p /app/backend/logs

  python manage.py migrate --noinput
  python manage.py collectstatic --noinput
  python manage.py compilemessages

  if [ "${BLOG_SEED_DB:-false}" = "true" ]; then
    python manage.py seed
  fi
}

wait_for_redis

if [ "${BLOG_SKIP_SETUP:-false}" != "true" ]; then
  run_startup_tasks
fi

exec "$@"
