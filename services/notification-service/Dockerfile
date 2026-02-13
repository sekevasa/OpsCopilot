"""Dockerfile for notification service."""

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY shared/ /app/shared/
COPY services/notification-service/ /app/

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8005

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8005/api/v1/health')"

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8005"]
