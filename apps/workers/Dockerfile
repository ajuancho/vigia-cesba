FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml ./
COPY packages ./packages
COPY apps/workers ./apps/workers

RUN pip install --no-cache-dir uv \
 && uv pip install --system -e ./packages/shared -e ./packages/connectors -e ./apps/workers

# Default = worker; compose puede sobrescribir con `celery beat`.
CMD ["celery", "-A", "vigia_workers", "worker", "--loglevel=info", "--concurrency=2"]
