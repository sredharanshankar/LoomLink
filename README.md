# LoomLink

Production-grade textile manufacturing platform for Everest Textile Mills. Covers yarn inventory,
production scheduling, quality control, dispatch, workforce management, and financial management —
with Ripple, an in-process forecasting engine that surfaces risks and suggests fixes in real time.

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (with Docker Compose v2)
- Git

---

## Quick start

```bash
git clone https://github.com/sredharanshankar/LoomLink
cd loomlink
cp .env.example .env          # review and adjust if needed
docker compose up -d --build
make demo-reset               # create schema + seed demo mill (~15 s)
```

Open **https://localhost:5173** (accept the self-signed certificate once).

### Demo logins

| Role | Employee Code | Password | PIN |
|---|---|---|---|
| Owner | OWN-001 | demo1234 | 100001 |
| Manager | MGR-001 | demo1234 | 200002 |
| Storekeeper | STK-001 | demo1234 | 300003 |
| Operator | OPR-001 | — | 400004 |
| QC Inspector | QCI-001 | demo1234 | 500005 |
| Dispatch | DSP-001 | demo1234 | 600006 |
| Accounts | ACC-001 | demo1234 | 700007 |
| Buyer | BYR-001 | demo1234 | — |

---

## Phone setup

Phones need HTTPS for the camera (QR scanning). On the same LAN:

1. Find your laptop IP: `ipconfig` (Windows) or `ip a` (Linux/macOS)
2. Open **https://\<LAN-IP\>:5173** on the phone
3. Accept the certificate warning once

Or use a tunnel: `cloudflared tunnel --url https://localhost:5173`

---

## Windows (no `make`)

```powershell
./scripts/dev.ps1 dev          # start containers
./scripts/dev.ps1 demo-reset   # seed
./scripts/dev.ps1 test         # run tests
./scripts/dev.ps1 lint         # lint
./scripts/dev.ps1 gen-api      # regenerate types
```

---

## Project structure

```
loomlink/
├── backend/        Python 3.12, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL 16
├── frontend/       Vite 5, React 18, TypeScript strict, Tailwind CSS 3.4
├── docs/           CONTRACT.md (source of truth), RBAC.md, SEED.md, OWNERSHIP.md
└── scripts/        dev.sh / dev.ps1
```

See [docs/OWNERSHIP.md](docs/OWNERSHIP.md) for lane assignments.

---

## Development commands

```bash
make dev            # docker compose up -d (db + backend + frontend)
make down           # stop containers
make logs           # tail all logs
make demo-reset     # drop + recreate schema, seed demo data
make test           # all tests (backend + frontend)
make test-core      # backend unit tests only
make lint           # ruff + mypy + eslint + tsc
make gen-api        # export OpenAPI → docs/openapi.json → frontend/src/lib/api-types.ts
make migrate        # alembic upgrade head
make makemigration name=<name>
```

---

## First-time teammate setup

```bash
make setup          # sets git hooks path + copies .env.example → .env
```

This wires `.githooks/commit-msg` which strips AI co-author trailers from commits.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Port 5432 busy | Stop local Postgres or change DATABASE_URL port |
| Port 5173 busy | Change `ports` in docker-compose.yml |
| Camera blocked | Must be HTTPS; accept the cert on the phone |
| Docker WSL memory | Add `[wsl2] memory=4GB` to `%USERPROFILE%\.wslconfig` |
| `make demo-reset` slow | Normal on first run (pulls images); subsequent runs < 20 s |