FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gettext \
    && rm -rf /var/lib/apt/lists/*

COPY requirements /app/requirements
RUN pip install --upgrade pip \
    && pip install -r /app/requirements/prod.txt

COPY . /app


RUN chmod +x /app/scripts/entrypoint.sh \
    && useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/data /app/backend/logs \
    && chown -R appuser:appuser /app \
    && mkdir -p /app/backend/static \
    && chown -R appuser:appuser /app/backend/static

USER appuser

ENTRYPOINT ["/app/scripts/entrypoint.sh"]
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "settings.asgi:application"]
