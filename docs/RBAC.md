# LoomLink — Roles & Permissions

The backend enforces these with `require_permission("<perm>")` on every endpoint (`app/core/rbac.py` holds the same matrix as code).
The frontend reads `permissions` from `GET /auth/me` and hides what the user cannot do. Hiding things in the UI is only cosmetic; the server always decides.

## 1. Roles

| Role | Who at Everest | Signs in with | Default landing |
|---|---|---|---|
| `owner` | Mill owner | email/phone + password | `/app/dashboard` |
| `manager` | Production manager / planner / supervisor | email/phone + password | `/app/floor` |
| `storekeeper` | Store & receiving | email/phone + password (or PIN) | `/w` (worker shell) with store actions, `/app/inventory` on desktop |
| `operator` | Machine operator | worker code + PIN | `/w` |
| `qc_inspector` | Quality inspector | email/phone + password (or PIN) | `/w/qc` |
| `dispatch` | Dispatch clerk | email/phone + password (or PIN) | `/w` dispatch actions, `/app/dispatch` |
| `accounts` | Accounts / office | email/phone + password | `/app/finance` |
| `buyer` | Customer | email/phone + password, or the tracking link (no login) | `/buyer` |

## 2. Permission matrix

✓ = granted · ◐ = granted with a row-level limit (see §3) · blank = denied

| Permission | owner | manager | storekeeper | operator | qc_inspector | dispatch | accounts | buyer |
|---|---|---|---|---|---|---|---|---|
| users.manage | ✓ | | | | | | | |
| settings.view | ✓ | ✓ | | | | | ✓ | |
| settings.manage | ✓ | | | | | | | |
| audit.view | ✓ | | | | | | | |
| scan.use | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| labels.print | ✓ | ✓ | ✓ | | ◐ roll only | | | |
| suppliers.view | ✓ | ✓ | ✓ | | | | ✓ | |
| suppliers.manage | ✓ | | ✓ | | | | ✓ | |
| inventory.view | ✓ | ✓ | ✓ | ◐ batch summary | | | ✓ | |
| inventory.manage (yarn types, reorder levels) | ✓ | ✓ | ✓ | | | | | |
| inventory.receive | ✓ | | ✓ | | | | | |
| inventory.issue (issue/return) | ✓ | ✓ | ✓ | | | | | |
| inventory.adjust | ✓ | ✓ | | | | | | |
| purchasing.manage | ✓ | ✓ | ✓ | | | | ✓ | |
| buyers.view | ✓ | ✓ | | | | ✓ | ✓ | |
| buyers.manage | ✓ | ✓ | | | | | ✓ | |
| orders.view | ✓ | ✓ | ✓ | ◐ own jobs | ✓ | ✓ | ✓ | |
| orders.manage | ✓ | ✓ | | | | | | |
| orders.lookup | ✓ | ✓ | ✓ | | ✓ | ✓ | ✓ | |
| production.view | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | | |
| production.plan (assign/reorder/split) | ✓ | ✓ | | | | | | |
| production.operate (start/progress/pause/handover/finish/breakdown/repaired) | ✓ | ✓ | | ◐ on shift, skilled stage | | | | |
| machines.manage | ✓ | ✓ | | | | | | |
| rolls.create | ✓ | ✓ | | ◐ finishing stage | ✓ | | | |
| quality.view | ✓ | ✓ | | | ✓ | ✓ | | |
| quality.inspect | ✓ | | | | ✓ | | | |
| rolls.passport | ✓ | ✓ | | | ✓ | ✓ | ✓ | |
| dispatch.view | ✓ | ✓ | ✓ | | ✓ | ✓ | ✓ | |
| dispatch.manage | ✓ | | | | | ✓ | | |
| workers.view | ✓ | ✓ | | | | | ✓ | |
| workers.manage | ✓ | ✓ | | | | | ✓ | |
| attendance.self | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| attendance.view | ✓ | ✓ | | | | | ✓ | |
| attendance.manage (badge check-in, corrections, shift/overtime assignment) | ✓ | ✓ | | | | | | |
| payroll.view (wage rates, payroll) | ✓ | | | | | | ✓ | |
| payroll.manage (compute, advances, mark paid) | ✓ | | | | | | ✓ | |
| payroll.approve | ✓ | | | | | | | |
| finance.view | ✓ | | | | | | ✓ | |
| finance.manage (supplier bills, expenses) | ✓ | | | | | | ✓ | |
| finance.record_payment | ✓ | | | | | | ✓ | |
| finance.view_costs (order/roll cost & margin) | ✓ | ◐ cost, not wages per person | | | | | ✓ | |
| dashboard.owner | ✓ | ◐ no cash/receivables tiles | | | | | ✓ | |
| ripple.view | ✓ | ✓ | | | | | | |
| ripple.manage (recompute, simulator) | ✓ | ✓ | | | | | | |
| ripple.apply (apply/dismiss fixes) | ✓ | ✓ | | | | | | |
| leak.view | ✓ | ✓ | | | | | ✓ | |
| bol.use | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | | |
| buyer.own | | | | | | | | ✓ |

## 3. Row-level rules (enforced in services, not just routers)

1. **Operator on shift:** `production.operate` for an operator requires (a) an attendance check-in today without check-out, or a shift assignment covering *now*; and (b) the machine's stage ∈ worker.skill_stages. Otherwise → 403 `NOT_ON_SHIFT` / `FORBIDDEN`.
2. **Operator scope:** operators see jobs for their stages and their own sessions; no money fields at all.
3. **Operator inventory view:** batch code, yarn type, colour and remaining kg only (no rates).
4. **Manager costs:** the manager sees order and roll cost totals and margins, but never individual wage rates or payroll lines.
5. **Buyer:** sees only orders where `orders.buyer_id = user.buyer_id`, in the buyer-safe shape (no costs, workers, machines or internal notes). The public tracking link gives the same data for one order.
6. **Inspector independence (soft):** if the same user created a roll and records its QC decision, the inspection is still allowed, but it is stored with `self_inspected=true` in `audit_log` and shown with a badge in the QC history. This keeps a one-person demo working while still leaving a record.
7. **Approvals:** stock adjustments, attendance corrections and Ripple fix applications always record `actor_id` and `reason` in `audit_log`.
8. **Payroll lock:** once a payroll run is approved, attendance in that period becomes read-only (corrections → 409 `INVALID_STATE`).
9. **Demo endpoints** (`/simulator/*`, `/demo/*`) exist only when `DEMO_MODE=true`, and require `owner` or `ripple.manage`.

## 4. Field-level money filtering

| Field family | Visible to |
|---|---|
| `wage_rate_paise`, payroll lines, advances | owner, accounts |
| `rate_paise_per_kg` (yarn cost), supplier bills | owner, accounts, storekeeper (rates on receipts they create), manager (read) |
| `price_paise_per_m`, invoices, payments, receivables | owner, accounts, manager (price only, read) |
| order/roll cost & margin | owner, accounts, manager |
| leak ₹ amounts | owner, manager, accounts |

Implementation: response schemas have optional money fields. The service sets them to `null` when the caller lacks permission (helper `core.rbac.mask_money(obj, user)`).

## 5. Default demo accounts (seed — change before any real use)

| Login | Password / PIN | Role |
|---|---|---|
| owner@everest.test | Owner@123 | owner |
| manager@everest.test | Manager@123 | manager |
| store@everest.test | Store@123 | storekeeper |
| qc@everest.test | Qc@12345 | qc_inspector |
| dispatch@everest.test | Dispatch@123 | dispatch |
| accounts@everest.test | Accounts@123 | accounts |
| buyer.kaveri@everest.test | Buyer@123 | buyer (Kaveri Garments) |
| EMP-001 … EMP-012 | PIN 1234 | operator |
