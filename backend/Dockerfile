FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY app ./app
COPY alembic.ini .
COPY alembic ./alembic

ENV PYTHONUNBUFFERED=1
EXPOSE 8080

# Cloud Run sets PORT; local Docker defaults to 8000.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
