param([string]$Target = "help", [string]$Name = "unnamed")
switch ($Target) {
    "setup" {
        git config core.hooksPath .githooks
        if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env" }
        Write-Host "Setup complete."
    }
    "dev"          { docker compose up -d }
    "down"         { docker compose down }
    "logs"         { docker compose logs -f }
    "demo-reset"   { docker compose exec backend python -m app.seed.run --reset }
    "test" {
        docker compose exec backend pytest tests/ -v
        docker compose exec frontend npm test
    }
    "test-core"    { docker compose exec backend pytest tests/ -v }
    "test-ripple"  { docker compose exec backend pytest tests/ripple/ -v }
    "test-web"     { docker compose run --rm frontend npm test }
    "e2e"          { docker compose exec frontend npx playwright test }
    "lint" {
        docker compose exec backend ruff check app/ tests/
        docker compose exec backend mypy app/ --ignore-missing-imports
        docker compose exec frontend npm run lint
        docker compose exec frontend npm run typecheck
    }
    "fmt" {
        docker compose exec backend ruff format app/ tests/
        docker compose exec frontend npm run lint -- --fix
    }
    "gen-api" {
        docker compose exec backend python scripts/export_openapi.py
        docker compose exec frontend npm run gen:api
    }
    "migrate"       { docker compose exec backend alembic upgrade head }
    "makemigration" { docker compose exec backend alembic revision --autogenerate -m $Name }
    "help" {
        Write-Host "Usage: ./scripts/dev.ps1 <target> [-Name <name>]"
        Write-Host "Targets: setup dev down logs demo-reset test test-core test-ripple test-web e2e lint fmt gen-api migrate makemigration"
    }
    default { Write-Error "Unknown target: $Target"; exit 1 }
}