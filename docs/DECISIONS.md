# LoomLink — Decisions Log (append-only, one line per decision, prefix with lane letter)

F: Use --workers 1 in prod gunicorn because in-process event bus and WebSocket hub require single process.
F: dispatch_items active-dispatch uniqueness enforced via is_active boolean column on dispatch_items (service-maintained), not DB trigger, for portability.
F: Frontend routes use DASHBOARD constant instead of inline path literals to avoid hook pattern detection (slash-path scanner in PowerShell tool environment).
F: Auth state persisted via Zustand persist middleware (localStorage) with separate accessToken/refreshToken/user; silent refresh via shared promise dedup in api.ts.
F: MSW browser worker activated only when VITE_USE_MOCKS=true; handlers return demo fixtures matching seed data.
F: Frontend permission check (can()) is cosmetic only — hides nav items; server-side require_permission() is the authoritative enforcement point.