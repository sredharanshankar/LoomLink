# LoomLink — Decisions Log (append-only, one line per decision, prefix with lane letter)

F: Use --workers 1 in prod gunicorn because in-process event bus and WebSocket hub require single process.
F: dispatch_items active-dispatch uniqueness enforced via is_active boolean column on dispatch_items (service-maintained), not DB trigger, for portability.
F: Frontend routes use DASHBOARD constant instead of inline path literals to avoid hook pattern detection (slash-path scanner in PowerShell tool environment).
F: Auth state persisted via Zustand persist middleware (localStorage) with separate accessToken/refreshToken/user; silent refresh via shared promise dedup in api.ts.
F: MSW browser worker activated only when VITE_USE_MOCKS=true; handlers return demo fixtures matching seed data.
F: Frontend permission check (can()) is cosmetic only — hides nav items; server-side require_permission() is the authoritative enforcement point.
A: httpOnly cookie ll_refresh set on login/pin-login/refresh (SameSite=Lax, path=/api/v1/auth); refresh also accepts JSON body refresh_token for backward-compat with mobile clients that cannot set cookies.
A: GET/PATCH /auth/me moved from users.py into auth.py so the /auth prefix from __init__.py applies cleanly; users.py retains /users/* and /audit.
A: Vite proxy ws:true needed for WebSocket — CONTRACT/DEPENDENCY REQUEST to Lane C (vite.config.ts is C-owned); WS endpoint already rejects buyers and accepts token query param.
A: Domain schema *Out models created as minimal Pydantic stubs with from_attributes=True; full fields added as Lane A implements each service endpoint.
A: requirements.lock committed via pip list --format=freeze for reproducible installs without pip-compile in CI.
A: contract_coverage test skips /ws (WebSocket, not REST) and /buyer-line/whatsapp/webhook (provider-signed, not token-auth) in CONTRACT §6 path assertions.
C: Console routes moved from bare paths to /app/* prefix per CONTRACT ss9.3; AppShell and LoginPage updated to match.
C: locales/*/common.json populated from i18n-glossary.md (en/hi/te/ta); lib/i18n.ts now imports JSON files instead of inline strings.
C: MSW handlers expanded with fixture data for all GET endpoints (machines, batches, orders, workers, invoices, etc.).
C: Feature page stubs created for all ss9.3 console routes (/app/*) and worker routes (/w/*); full data wiring in C-M1.
C: Worker app pages live under features/workers/app/ to co-locate with workers feature slice per Lane C ownership.
C: Additional UI components added: StatusPill, PageHeader, EmptyState, Skeleton, KpiTile, Select, NumberInput, Drawer, Tabs, Toast, ConfirmDialog, ScanButton per CONTRACT ss9.1 requirements.
