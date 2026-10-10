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

## WP3 — Demo seed data (pending)
## WP4 — Lane A endpoints (pending)
## WP5 — Ripple on real data (pending)
## WP6 — Frontend screens (pending)
## WP7 — Ripple UI (pending)
## WP8 — Final verification (pending)
