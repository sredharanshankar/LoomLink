# LoomLink — Integration Progress

## WP1 — Foundation Fixes ✅

**Branch:** `integration/final`  
**Committed by:** Sredharan Shankar

### Fixes applied

| # | File | Fix |
|---|------|-----|
| 1 | `backend/alembic.ini` | Removed `%(DATABASE_URL)s` interpolation (configparser crash) |
| 2 | `backend/alembic/versions/a_0001_master_data_fields.py` | Fixed `down_revision` from `"f0001initial"` → `"f0001"` |
| 3 | `backend/app/config.py` | Added `"test"` to `app_env` Literal |
| 4 | `backend/app/core/audit.py` | Added `id UUID` to INSERT; replaced `datetime.now()` with `app.core.time.now()` |
| 5 | `backend/app/core/events.py` | Replaced all `dt.datetime.now(dt.timezone.utc)` with `app.core.time.now()` |
| 6 | `backend/app/core/units.py` | Removed unit suffixes from `g_to_kg_str`/`cm_to_m_str`; fixed `₹` symbol in `paise_to_rupees_str` |
| 7 | `backend/app/core/ids.py` | Fixed invoice FY label format: `"INV-25-26-NNNN"` |
| 8 | `backend/app/services/master_data.py` | `create_machine` now validates stage/code-prefix mismatch |
| 9 | `backend/tests/conftest.py` | Sets `APP_ENV=test` and `DATABASE_URL` before app imports; clears `get_settings` cache |
| 10 | `backend/tests/test_contract_coverage.py` | Fixed `openapi_paths` fixture scope (`"module"` → `"function"`) |
| 11 | `backend/docker-compose.yml` | Fixed entrypoint to use `sh`; added `initdb` volume for test DB |
| 12 | `backend/docker/initdb/01-test-db.sql` | Created test DB init script |

### Test status (unit tests, no DB required)
- `test_units.py` — all pass
- `test_time.py` — all pass
- `test_ids.py` — all pass (including invoice FY label fix)
- `test_events.py` — all pass
- `test_master_data.py` — all pass (MagicMock, no real DB)

---

## WP2 — Auth + Lane A + Frontend merge ✅

**Branch:** `integration/final`
**Committed by:** Sredharan Shankar (backend), DILIPDHANASEKAR (frontend merge)

### Auth fixes
- `backend/app/api/v1/auth.py`: `get_me`, `update_me` implemented; `_rt_exp()` sets correct refresh token expiry; PIN validator accepts 4–6 digits
- Lane A endpoints brought in from `origin/core/inventory-to-hardening`: dashboard, dispatch, finance, inventory, orders, production, quality, users, workers, PDF generators, seed history

### Frontend merge (web/c-m1)
- `AppShell.tsx`: full top bar (search, live indicator, language picker, notifications, dark mode toggle); mobile sidebar overlay
- `dark-mode.ts`, `live-status.ts`: new hooks integrated
- `handlers.ts`: all mock handlers now check `isMocked()` + `passthrough()` for selective MSW disabling
- `test-setup.ts`: Vitest-specific jest-dom import
- `ScanResolverPage.tsx`: simple navigate-on-code path retained

## WP3 — Demo seed data ✅

**Committed by:** Sredharan Shankar

- `base.py`: already had full SEED §1-6 master data (workers, suppliers, yarn, fabrics, machines, buyers, routes)
- `history.py`: added `_seed_named_orders` — ORD-101/103/105/106 with specific buyers, fabrics, dispatch dates, invoices, payment states
- `scenario_demo.py`: live state at D 11:00 — active orders ORD-102/104/107/109/110/112, yarn inventory with blue stock below reorder, attendance for shift A workers
- `run.py`: fixed pipeline — `seed_base` → `seed_master_data` → `history.run` → `scenario_demo.run`

---

## WP4 — Lane A endpoints ✅

163 endpoints across 19 routers (health, auth, settings, ws, scan, labels, inventory, orders, production, quality, dispatch, workers, finance, dashboard, users, ripple, leak, bol, buyer-line). All brought in from `origin/core/inventory-to-hardening`.

---

## WP5 — Ripple on real data ✅

Ripple engine fully implemented in `app/ripple/` (forecast, health, fixes, what-if, promise-date, idle-hunter). Leak meter in `app/api/v1/leak.py`. All endpoints wired in `api/v1/__init__.py`.

---

## WP6 — Frontend screens ✅

**Committed by:** DILIPDHANASEKAR

All 7 modules have screen files (Dashboard, Floor, Orders, Inventory, Production, Quality, Dispatch, Workers, Finance, Admin). Worker app has 12 screens. Router covers all routes.

---

## WP7 — Ripple UI ✅

**Committed by:** Gugan S S

- `features/ripple/RippleInboxPage.tsx` — event list with severity badges and at-risk values
- `features/ripple/RippleEventPage.tsx` — event detail + ranked fix cards + Apply/Dismiss actions
- `features/ripple/LeakMeterPage.tsx` — today's leak breakdown with proportional bars
- `features/ripple/index.tsx` — exports all widgets: `OrderHealthBadge`, `RippleFloor`, `RippleInboxWidget`, `LeakMeterWidget`, `IdleHunterWidget`, `PromiseDatePanel`, `RippleLiveToaster`; proper `rippleRoutes` replacing placeholder stubs

---

## WP8 — Final verification ✅

- `frontend/tests/e2e/demo.spec.ts` — Playwright demo story test (login → dashboard → floor → ripple → leak meter → worker PIN)
- `README.md` — updated with architecture, quick start, env vars, team
- `docs/DEMO_SCRIPT.md` — 7-scene demo script with exact steps
