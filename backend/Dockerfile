FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY app ./app
COPY alembic.ini .
COPY alembic ./alembic

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

# Apply versioned migrations, then serve. Prod relies on Alembic (not create_all).
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
