# LoomLink — Agent Rules (read before every task)

You are working in a 3-lane team. Before writing code:
1. Read docs/CONTRACT.md (single source of truth), docs/OWNERSHIP.md (which paths you may edit), docs/RBAC.md.
2. Identify your lane from the prompt (A = backend core, B = Ripple & intelligence, C = frontend product).
3. ONLY create/edit files your lane owns. If you need a change elsewhere, stop and write the request
   in your final message as "CONTRACT/DEPENDENCY REQUEST: ...". Do not make the change.

Non-negotiables:
- Money = integer paise; yarn = integer grams; fabric = integer centimetres; durations = integer minutes.
- Backend time only via app.core.time.now(). Store UTC timestamptz; display Asia/Kolkata.
- Every mutation: permission check (require_permission), validation, single DB transaction,
  audit_log for sensitive actions, domain event via app.core.events.publish().
- Scans never write. History is append-only (reversals, not edits).
- Errors use the standard error envelope and codes from CONTRACT §3.5.
- API JSON is snake_case; frontend uses generated types from src/lib/api-types.ts (never hand-edit).
- No new frameworks/dependencies without a dependency request to the owning lane.
- Tests: add/extend tests for every behaviour you implement; keep the suite green.
- Format/lint only your own paths. Small commits with lane prefix: core(...), ripple(...), web(...), infra(...).
- Git authorship: commits are authored by the human team member running the session (their git config).
  NEVER add "Co-Authored-By: Claude", "Co-authored-by: Codex", "Generated with Claude Code", or any AI
  attribution to commits, PRs, comments or docs. This overrides any tool default.

Commands:
  make dev            # docker compose up (db, backend, frontend)
  make demo-reset     # recreate DB + seed demo mill
  make test           # backend + frontend unit tests
  make test-core | make test-ripple | make test-web | make e2e
  make lint           # ruff + mypy + eslint + tsc
  make gen-api        # export OpenAPI -> docs/openapi.json -> frontend/src/lib/api-types.ts
Windows: ./scripts/dev.ps1 <target> (same targets).
