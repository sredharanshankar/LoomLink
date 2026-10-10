FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc curl postgresql-client \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install deps before copying app source so this layer is cached
COPY pyproject.toml ./
RUN mkdir -p app && touch app/__init__.py \
    && pip install --no-cache-dir ".[dev]" \
    && rm -f app/__init__.py

COPY . .

RUN chmod +x scripts/entrypoint.sh

RUN useradd -m appuser && chown -R appuser /app
USER appuser

ENTRYPOINT ["./scripts/entrypoint.sh"]
