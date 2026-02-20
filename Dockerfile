# syntax=docker/dockerfile:1
# CourseForge – production image (deps from pyproject.toml via uv)
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1

WORKDIR /app

# Install uv and sync dependencies from pyproject.toml (no dev groups)
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen --no-dev --no-install-project

# Copy application
COPY . .
RUN uv sync --frozen --no-dev

# Collect static files (required for WhiteNoise)
RUN uv run python manage.py collectstatic --noinput --clear 2>/dev/null || true

EXPOSE 8000

# Run gunicorn; override with docker run ... or in compose
CMD ["uv", "run", "gunicorn", "courseforge.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "4"]
