# LoomLink — Intelligent Textile Mill Management

> Team 45 · Hackathon submission

LoomLink is a full-stack mill management platform for **Everest Textile Mills** that turns raw sensor and production data into actionable intelligence via the **Ripple** engine — a constraint-aware event propagation and recommendation system.

---

## Quick start (demo)

```bash
# 1. Start all services
docker compose up -d

# 2. Wait for DB, then seed
docker compose exec api python -m app.seed.run --reset

# 3. Open browser
open http://localhost:5173
```

**Demo accounts** (see `docs/SEED.md` for full list):

| Role | Employee code | Password |
|---|---|---|
| Owner | OWN-001 | demo1234 |
| Manager | MGR-001 | demo1234 |
| Storekeeper | STK-001 | demo1234 |
| Operator (PIN) | EMP-001…EMP-012 | PIN 1234 |

---

## Architecture

```
┌──────────────────────────────────────────┐
│  React 18 + TypeScript + Vite 5          │
│  TanStack Query · i18next · Tailwind 3.4 │
└────────────────┬─────────────────────────┘
                 │ REST + WebSocket
┌────────────────▼─────────────────────────┐
│  FastAPI · SQLAlchemy 2 · Alembic        │
│  Ripple engine (app/ripple/)             │
│  PDF generator (app/pdf/)                │
└────────────────┬─────────────────────────┘
                 │
┌────────────────▼─────────────────────────┐
│  PostgreSQL 16                           │
└──────────────────────────────────────────┘
```

### Money, units, time conventions

| Concept | Storage |
|---|---|
| Money | BIGINT paise (÷100 = ₹) |
| Yarn | INTEGER grams |
| Fabric | INTEGER centimetres |
| Durations | INTEGER minutes |
| Time | `app.core.time.now()` — supports `DEMO_CLOCK_START` |

---

## Modules

| Module | Route |
|---|---|
| Dashboard | `/app/dashboard` |
| Floor view | `/app/floor` |
| Orders | `/app/orders` |
| Inventory | `/app/inventory` |
| Production | `/app/production` |
| Quality | `/app/quality` |
| Dispatch | `/app/dispatch` |
| Workers | `/app/workers` |
| Finance | `/app/finance` |
| **Ripple inbox** | `/app/ripple` |
| **Leak Meter** | `/app/leak` |
| Worker app | `/w` (PIN login) |
| Buyer portal | `/buyer-line` |

---

## Ripple — the intelligence layer

Ripple propagates production events (breakdowns, yarn shortages, QC failures) through the constraint graph and computes:

1. **Order health** — green / amber / red + slack minutes
2. **At-risk value** — estimated penalty + idle cost if nothing changes
3. **Ranked fixes** — machine reassignment, overtime, split runs
4. **Promise Date** — earliest confirmed delivery for a new order
5. **Idle Hunter** — machines sitting idle that could absorb queued work
6. **Leak Meter** — running tally of idle + rework + waste + overtime cost

---

## Development

```bash
# Backend
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev

# Type check
npm run typecheck

# Unit tests (backend)
cd backend && pytest

# E2E tests
cd frontend && npx playwright test
```

### Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://loomlink:loomlink@db:5432/loomlink` | DB connection |
| `JWT_SECRET` | (required) | Token signing |
| `DEMO_CLOCK_START` | (empty = real time) | Override demo clock |
| `VITE_API_BASE` | `/api/v1` | Frontend API base |
| `VITE_MOCK_MODULES` | (empty = no mocks) | Comma-separated modules to mock |

---

## Team

| Name | Area | Branch |
|---|---|---|
| Sredharan Shankar | Backend · infra · docs | `core/inventory-to-hardening` |
| Gugan S S | Ripple engine · BoL · Buyer Line | Ripple feature branches |
| Dilip Dhanasekar | Frontend · UX | `web/c-m1` |
