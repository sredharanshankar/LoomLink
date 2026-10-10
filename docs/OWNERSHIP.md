# LoomLink — Code Ownership (who may edit what)

Three lanes work in parallel. Each lane may **create and edit only the paths it owns**.
Each lane may **read** everything. Shared files change only through the contract process (`docs/CONTRACT.md` §13).

| Lane | Person | Tool | Branch prefix |
|---|---|---|---|
| **F** Foundation (one-time, ~2 h) | Team leader | Claude Code | `foundation/*` → merged to `main` before anyone else starts |
| **A** Backend Core + DevOps + Integration | Team leader | Claude Code | `core/*` |
| **B** Ripple & Intelligence (engine, Bol, Buyer Line, Ripple UI) | Member 2 | **Codex** | `ripple/*` |
| **C** Frontend Product (all app screens except Ripple features) | Member 3 | Claude Code | `web/*` |

## Path ownership

| Path | Owner | Notes |
|---|---|---|
| `docs/CONTRACT.md`, `docs/RBAC.md`, `docs/SEED.md`, `docs/OWNERSHIP.md` | A (leader) | Edited only via contract PRs |
| `docs/DECISIONS.md` | all (append-only, one line each, prefix with lane letter) | Merge conflicts: keep both lines |
| `docs/DEMO_SCRIPT.md` | A | |
| `docs/openapi.json` | generated (`make gen-api`); committed by whoever changed backend schemas | Regenerate after every backend schema change |
| `AGENTS.md`, `CLAUDE.md`, `README.md`, `Makefile`, `scripts/`, `docker-compose*.yml`, `Caddyfile`, `.env.example`, `.github/` | A | |
| `backend/pyproject.toml`, `backend/Dockerfile`, `backend/alembic.ini` | A | B requests deps via a one-line PR to A |
| `backend/alembic/versions/*` | A for core tables; B for `ripple_*`, `leak_entries`, `buyer_messages`, `machine_speeds` | File name prefix: `a_...` or `b_...`. If two heads appear, A runs `alembic merge` |
| `backend/app/main.py`, `config.py`, `db.py`, `deps.py` | A | Routers are already mounted by F; B never edits main.py |
| `backend/app/core/*` | A | B imports only |
| `backend/app/models/*` (except below) | A | |
| `backend/app/models/ripple.py` (ripple_snapshots, ripple_events, ripple_fixes, leak_entries, buyer_messages, machine_speeds) | B | |
| `backend/app/schemas/*` (except below) | A | |
| `backend/app/schemas/ripple.py`, `leak.py`, `bol.py`, `buyer_line.py`, `simulator.py` | B | |
| `backend/app/api/v1/*` (except below) | A | |
| `backend/app/api/v1/ripple.py`, `leak.py`, `bol.py`, `buyer_line.py`, `simulator.py`, `demo.py` | B | |
| `backend/app/services/*` (except interfaces' B half) | A | |
| `backend/app/services/interfaces.py` | Signatures: frozen by F. Bodies: A implements A-functions by delegating to `services/*`; B implements B-functions by delegating to `ripple_service/*` | Edit only your own function bodies |
| `backend/app/pdf/*` | A | |
| `backend/app/ripple/*`, `backend/app/ripple_service/*`, `backend/app/bol/*`, `backend/app/buyer_line/*` | B | |
| `backend/app/seed/base.py`, `history.py`, `run.py` | A | |
| `backend/app/seed/scenario_demo.py` | B | |
| `backend/tests/core/*`, `backend/tests/conftest.py` | A | |
| `backend/tests/ripple/*` | B | B may add `backend/tests/ripple/conftest.py` |
| `frontend/package.json`, `vite.config.ts`, `tailwind.config.ts`, `tsconfig*.json`, `index.html`, `frontend/Dockerfile` | C | B requests deps via a one-line PR to C |
| `frontend/src/main.tsx`, `App.tsx`, `router.tsx` | C | B's routes are already mounted by F |
| `frontend/src/lib/*`, `components/*`, `mocks/*` | C | B imports only (B may add mocks under `mocks/ripple/*`) |
| `frontend/src/features/{auth,dashboard,inventory,orders,production,quality,dispatch,workers,finance,buyer,scan,passport,admin}/*` | C | |
| `frontend/src/features/{ripple,bol,buyer-line}/*` | B | Export signatures frozen by F (CONTRACT §9.2) |
| `frontend/src/locales/*/common.json` | C | |
| `frontend/src/locales/*/ripple.json` | B | |
| `frontend/src/mocks/ripple/*` | B | |
| `frontend/tests/e2e/*` | C (A adds the final demo e2e during integration) | |

## Interaction rules

1. **Backend A ↔ B** go only through `services/interfaces.py` (Python) and domain events (`core/events.py`).
2. **Frontend C ↔ B** go only through the exports in `features/{ripple,bol,buyer-line}/index.ts` and the shared `lib/*` hooks.
3. **Frontend ↔ backend** go only through generated `lib/api-types.ts` plus `lib/api.ts`.
4. **Dependencies:** to add an npm or pip dependency outside your lane's files, open a tiny PR to the owner with the reason. Owners merge within 30 minutes.
5. **Never reformat files you don't own.** Run formatters only on your own paths (`ruff format backend/app/ripple`, `prettier --write src/features/ripple`).
6. **Merges:** rebase on `main` at least every 3 hours. PRs stay small (< 600 lines when possible). Squash-merge.
