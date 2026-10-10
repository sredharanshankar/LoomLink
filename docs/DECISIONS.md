# LoomLink — Decisions Log (append-only, one line per decision, prefix with lane letter)

F: Use --workers 1 in prod gunicorn because in-process event bus and WebSocket hub require single process.
F: dispatch_items active-dispatch uniqueness enforced via is_active boolean column on dispatch_items (service-maintained), not DB trigger, for portability.