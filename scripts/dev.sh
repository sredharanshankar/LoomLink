#!/usr/bin/env bash
set -euo pipefail
TARGET=${1:-help}
case "$TARGET" in
  setup)
    git config core.hooksPath .githooks
    [ -f .env ] || cp .env.example .env
    echo "Setup complete."
    ;;
  dev) docker compose up -d ;;
  down) docker compose down ;;
  logs) docker compose logs -f ;;
  demo-reset) docker compose exec backend python -m app.seed.run --reset ;;
  test) docker compose exec backend pytest tests/ -v && docker compose exec frontend npm test ;;
  test-core) docker compose exec backend pytest tests/ -v ;;
  test-ripple) docker compose exec backend pytest tests/ripple/ -v ;;
  test-web) docker compose exec frontend npm test ;;
  e2e) docker compose exec frontend npx playwright test ;;
  lint)
    docker compose exec backend ruff check app/ tests/
    docker compose exec backend mypy app/ --ignore-missing-imports
    docker compose exec frontend npm run lint
    docker compose exec frontend npm run typecheck
    ;;
  fmt)
    docker compose exec backend ruff format app/ tests/
    docker compose exec frontend npm run lint -- --fix
    ;;
  gen-api)
    docker compose exec backend python backend/scripts/export_openapi.py
    docker compose exec frontend npm run gen:api
    ;;
  migrate) docker compose exec backend alembic upgrade head ;;
  makemigration)
    NAME=${2:-unnamed}
    docker compose exec backend alembic revision --autogenerate -m "$NAME"
    ;;
  help)
    echo "Usage: ./scripts/dev.sh <target> [args]"
    echo "Targets: setup dev down logs demo-reset test test-core test-ripple test-web e2e lint fmt gen-api migrate makemigration"
    ;;
  *) echo "Unknown target: $TARGET"; exit 1 ;;
esac