FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY apps/api /app/apps/api
COPY packages /app/packages

RUN python -m pip install --upgrade pip \
    && python -m pip install -e /app/apps/api

WORKDIR /app/apps/api

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
