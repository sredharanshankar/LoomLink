FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev gcc && apt-get clean

COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[dev]"

COPY . .

RUN useradd -m appuser && chown -R appuser /app
USER appuser

ENTRYPOINT ["./scripts/entrypoint.sh"]
