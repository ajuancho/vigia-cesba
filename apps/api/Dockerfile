FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml ./
COPY packages ./packages
COPY apps/api ./apps/api
COPY db ./db

RUN uv pip install --system -e ./packages/shared -e ./packages/connectors -e ./apps/api

EXPOSE 8000
CMD ["uvicorn", "vigia_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
