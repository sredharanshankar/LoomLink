# LoomLink Screen Specs

For every route in CONTRACT §9.3. Covers layout, key components, API calls, empty/loading/error states, and required permissions.

**Notation**
- **Perm:** RBAC permission from `docs/RBAC.md` required to reach the route.
- **API:** REST endpoints hit on mount (query) and on user action (mutation).
- **Empty:** what renders when the list/resource is absent.
- **Loading:** skeleton or spinner shown while data is in-flight.
- **Error:** what renders on API failure.

---

## Public / Auth Shell

---

### `/login` — Staff Login
**Perm:** none (public)  
**Layout:** centred card, 400 px max-width, LoomLink logo, mill name from env.  
**Components:**
- `Input` email
- `Input` password (show/hide toggle)
- `Button` "Sign in" (primary, full-width)
- Link → `/pin` for workers

**API:**  
- `POST /auth/login` `{email, password}` → `{access_token, refresh_token, user}`

**Empty:** n/a  
**Loading:** button spinner, inputs disabled  
**Error:** inline `Toast` error — map 401 → "Invalid email or password", 429 → `RATE_LIMITED` message

---

### `/pin` — Worker PIN Login
**Perm:** none (public)  
**Layout:** full-screen mobile, centred; numeric keypad 3×3 + 0 + backspace; worker code field above.  
**Components:**
- `Input` worker code (e.g. EMP-012) — focus on mount; supports QR scan via `ScanButton`
- Large PIN display (4 dots, filled as typed)
- `Button` "Login" appears after 4 digits
- Link back → `/login`

**API:**  
- `POST /auth/pin` `{worker_code, pin}` → `{access_token, refresh_token, user}`

**Loading:** button spinner  
**Error:** shake animation + "Wrong PIN" inline message; clear PIN field

---

### `/s/:code` — Scan Resolver
**Perm:** any authenticated user  
**Layout:** full-screen white with spinner (no chrome); resolves instantly.  
**Logic:** extracts `code` → calls `GET /lookup/:code` (or client-side type detection) → redirects:
- Machine code → `/w/machine/:id` (workers) or `/app/machines/:id` (console)
- Roll code → `/w/roll/:id` (workers) or `/app/rolls/:id` (console)
- Batch code → `/w/batch/:id` (workers) or `/app/inventory/batches/:id` (console)
- Worker badge → `/w` attendance check-in flow (same page)

**Error:** `EmptyState` — "Unknown code — try scanning again" + back button

---

### `/track/:token` — Public Buyer Tracking
**Perm:** none (public)  
**Layout:** minimal public shell (no nav); LoomLink + mill name in header.  
**Components:**
- Order code + fabric name header
- Status timeline stepper: Confirmed → In Production → QC → Dispatched → Delivered (active step highlighted)
- Progress bar: metres passed / total ordered
- `Badge` dispatch status if dispatched
- Estimated dispatch date (labelled `is_estimate`)
- Shipment list (tracking ref, dispatched at, delivered at)
- "Last updated" relative time

**API:**  
- `GET /public/track/:token` → order snapshot

**Loading:** `Skeleton` stepper and progress bar  
**Error:** "This tracking link has expired or is invalid."

---

### `/buyer` — Buyer Portal
**Perm:** role `buyer` (JWT login)  
**Layout:** slim nav (logo + logout); list of own orders.  
**Components:**
- Order cards: code, fabric, qty, status badge, health badge (from Ripple), due date, estimated dispatch
- Link to `/track/:token` for each

**API:**  
- `GET /buyer/orders`

**Empty:** "No active orders"  
**Loading:** skeleton cards  
**Error:** `Toast` server error

---

## Worker Shell (`/w/*`) — Mobile, ≥56 px touch targets

All `/w` routes require `role = operator`. High-contrast light theme.

---

### `/w` — Worker Home
**Perm:** `attendance.self`  
**Layout:** bottom tab bar (Home | Scan | Jobs | Alerts); top strip shows worker name + shift badge.  
**Components:**
- Check-in / check-out `Button` (large, full-width) — state-aware label
- Today's shift assignment card (machine, shift)
- Active job card (if any): order code, stage badge, progress bar
- Low-stock alert strip (if any) — `amber` background
- `Badge` unread notifications count

**API (mount):**
- `GET /attendance?date=today` — check-in status
- `GET /jobs?operator_id=me&status=in_progress`

**API (action):**
- `POST /attendance/check-in` or `/check-out`

**Loading:** skeleton cards  
**Empty:** "No job assigned today"

---

### `/w/machine/:id` — Machine Detail (Worker)
**Perm:** `production.operate`  
**Layout:** full-screen card stack.  
**Components:**
- Machine code + name + stage badge + status pill
- Current job card: order code, planned metres, progress bar, operator
- Action buttons:
  - `start_job` (if queued + checked-in)
  - `log_progress` (if in_progress): opens numeric input sheet
  - `pause_job` / `resume_job`
  - `report_breakdown` (dropdown reason codes + estimated repair time)
- QR scan button (assigns self to machine)

**API (mount):**
- `GET /machines/:id`

**API (actions):**
- `POST /jobs/:id/start`
- `POST /jobs/:id/progress` [idem]
- `POST /jobs/:id/pause` / `/resume`
- `POST /machines/:id/breakdown`

**Loading:** skeleton  
**Error:** `Toast` MACHINE_BUSY / NOT_ON_SHIFT with translated messages

---

### `/w/job/:id` — Job Detail (Worker)
**Perm:** `production.operate`  
**Layout:** scrollable single column.  
**Components:**
- Job header: stage badge, status pill, order code, machine
- Progress ring: actual / planned cm
- Timeline of recent progress logs (last 5)
- `BolButton` (Ripple/Bol lane) pre-filled with job context
- Action buttons: `log_progress`, `handover`, `finish`
- Handover card if pending handover

**API:**
- `GET /jobs/:id`
- `POST /jobs/:id/progress`, `/handover`, `/accept-handover`, `/finish`

**Empty:** n/a (direct nav by id)  
**Error:** 404 → "Job not found"

---

### `/w/batch/:id` — Yarn Batch (Worker)
**Perm:** `inventory.view`  
**Layout:** single card.  
**Components:**
- Batch code, yarn type, supplier
- Remaining bar: remaining_grams / received_grams (colour: green / amber if < 20% / red if 0)
- Issue yarn button (opens grams input + order select)
- QR code to share

**API:**
- `GET /inventory/batches/:id`
- `POST /inventory/stock/issue` (storekeeper permission gate in UI)

**Error:** 404 → "Batch not found"

---

### `/w/receive` — Receive Yarn (Worker / Storekeeper)
**Perm:** `inventory.manage`  
**Layout:** stepped flow.  
**Steps:**
1. Scan or type batch code (or mark new batch)
2. Enter received_grams, rate_paise_per_kg, received_date; pick supplier
3. Confirm summary → submit

**API:**
- `GET /inventory/batches?q=:code` (autocomplete)
- `POST /inventory/batches` (new) or `PATCH /inventory/batches/:id` (add stock)

**Loading:** spinner on submit  
**Error:** inline field errors + toast

---

### `/w/roll/:id` — Roll (Worker)
**Perm:** `rolls.passport` (or `quality.view` for lighter view)  
**Layout:** roll passport card.  
**Components:**
- Roll code + status badge
- Order + job + length
- QC decision (if inspected): pass/rework/reject + severity
- Defect notes
- Timeline: created → inspected → reworked?

**API:**
- `GET /rolls/:id`

---

### `/w/qc` — QC Inspection (Worker / QC Inspector)
**Perm:** `quality.inspect`  
**Layout:** scan-first flow (camera opens immediately).  
**Steps:**
1. Scan roll QR → fetch roll
2. Measure length input
3. Decision buttons: Pass / Rework / Reject
4. If rework/reject: defect code select (multi-select) + severity + notes
5. Confirm → submit

**API:**
- `GET /rolls/:id`
- `POST /rolls/:id/inspections`

**Error:** ROLL_ALREADY_INSPECTED → "Already inspected" banner

---

### `/w/dispatch/:id` — Dispatch Scanning (Dispatch role)
**Perm:** `dispatch.manage`  
**Layout:** scan mode; camera always ready.  
**Components:**
- Dispatch header: order code, remaining count
- Scan result strip: last scan result (ok | wrong_order | not_passed | already_dispatched)
- Scanned roll list (scrollable)
- "Confirm Dispatch" `Button` (enabled when ≥ 1 roll scanned + all passed)

**API:**
- `GET /dispatches/:id`
- `POST /dispatches/:id/scan` [idem]
- `DELETE /dispatches/:id/items/:roll_id`
- `POST /dispatches/:id/confirm`

**Error:** business errors are HTTP 200 with `result` field — shown as coloured banners (green=ok, red=not_passed, amber=wrong_order)

---

## Console Shell (`/app/*`) — Desktop/Tablet

All `/app` routes require a JWT with role ≠ buyer. Navigation: top nav bar (logo + bell + user menu) + left sidebar per section.

---

### `/app/dashboard` — Owner Dashboard
**Perm:** `dashboard.owner`  
**Layout:** 3-column KPI grid at top; 2-column charts + widgets below.  
**Components:**
- KPI tiles: Orders due 7 d | At-risk count | Today's output (m) | Cash in MTD | Receivables outstanding | Low-stock alerts
- `<LeakMeterWidget compact />` (Ripple lane)
- `<RippleInboxWidget limit={5} />` (Ripple lane)
- `<RippleFloor compact onMachineClick={...} />` (Ripple lane)
- Daily brief modal (morning: auto-opens once per day if `dashboard.owner` role)

**API:**
- `GET /dashboard/owner`
- `GET /dashboard/daily-brief` (brief modal)

**Loading:** skeleton KPI tiles  
**Error:** partial failure — individual widgets show `EmptyState` if their call fails

---

### `/app/floor` — Factory Floor Map
**Perm:** `production.view`  
**Layout:** full-area canvas (12×8 grid) with sidebar for selected machine.  
**Components:**
- `<RippleFloor />` (Ripple lane) — full size; machine cells show status colour, progress %, operator
- Clicking a machine → side drawer with machine detail + active job
- Zone labels (Receiving, Spinning, Weaving, Dyeing, Finishing, QC, Dispatch)

**API (via RippleFloor):**
- `GET /production/floor`
- `GET /ripple/forecast` (for health colours)

**Loading:** skeleton grid  
**Error:** toast "Could not load floor state"

---

### `/app/orders` — Orders List
**Perm:** `orders.view`  
**Layout:** full-width table with filter toolbar.  
**Components:**
- Filter bar: status multi-select | buyer select | due_before date | search (q)
- Table columns: Code | Buyer | Fabric | Qty (m) | Status badge | Priority badge | Health badge (Ripple) | Due date | Actions
- `<OrderHealthBadge />` (Ripple lane) per row
- "New Order" button → `/app/orders/new`

**API:**
- `GET /orders?status=&buyer_id=&due_before=&q=&limit=50&offset=0`

**Empty:** `EmptyState` "No orders match filters"  
**Loading:** skeleton table rows  
**Error:** toast

---

### `/app/orders/new` — New Order (Draft)
**Perm:** `orders.manage`  
**Layout:** centered form card, 700 px max.  
**Components:**
- `Select` buyer (searchable)
- `Select` fabric type
- `NumberInput` quantity (metres, converts to cm internally)
- `Input` price per metre (pre-fills fabric default)
- `Select` priority
- `Input` due date
- `Textarea` notes
- `<PromiseDatePanel />` (Ripple lane) — updates as fields change
- "Check Feasibility" → shows yarn_needed/available/shortage inline
- "Save Draft" / "Confirm Order"

**API:**
- `GET /fabric-types`
- `GET /buyers`
- `POST /orders/feasibility` (on "Check Feasibility")
- `POST /orders` → draft
- `POST /orders/:id/confirm`
- `GET /ripple/promise-date` (via PromiseDatePanel)

**Error:** YARN_INSUFFICIENT → shows shortage with suggested batches

---

### `/app/orders/:id` — Order Detail
**Perm:** `orders.view`  
**Layout:** 2-column: left (order info + tabs) | right (Ripple health + timeline).  
**Tabs:** Overview | Jobs | Rolls | Dispatches | Invoices | Cost (finance.view_costs only)  
**Components:**
- Header: code, buyer, fabric, qty, status badge, health badge, due date, actions dropdown
- Overview tab: stage progress stepper, `<PromiseDatePanel />` if draft
- Jobs tab: table of jobs with stage, machine, status, progress bars, operator
- Rolls tab: table + aggregate pass/rework/reject counts
- Dispatches tab: dispatch list with confirmed/in-transit/delivered
- Invoices tab (finance.view only): amount, paid, balance, due date, status
- Cost tab (finance.view_costs only): itemised breakdown with `is_estimate` label if open
- Actions: Confirm | Cancel | Edit (if draft/confirmed)
- `<BolButton />` pre-filled with order context

**API:**
- `GET /orders/:id`
- `GET /jobs?order_id=:id`
- `GET /rolls?order_id=:id`
- `GET /dispatches?order_id=:id`
- `GET /orders/:id/timeline`
- `GET /ripple/orders/:id/health`
- `GET /finance/orders/:id/cost` (cost tab, finance.view_costs)
- `POST /orders/:id/confirm`, `/cancel`

**Loading:** skeleton per tab  
**Error:** 404 → "Order not found" full-page

---

### `/app/buyers` — Buyers List
**Perm:** `buyers.view`  
**Layout:** table + search.  
**Columns:** Code | Name | Terms (days) | Late penalty | Active orders | Outstanding balance  
**API:** `GET /buyers`  
**Empty:** "No buyers yet"

---

### `/app/buyers/:id` — Buyer Detail
**Perm:** `buyers.view` (outstanding needs `finance.view`)  
**Layout:** 2-column: info card + order history table + outstanding invoices table.  
**Components:**
- Buyer info card + edit (if `buyers.manage`)
- Orders table (recent 20)
- Outstanding invoices with ageing buckets (0–30 / 31–60 / 61–90 / 90+ days)

**API:**
- `GET /buyers/:id`
- `GET /orders?buyer_id=:id`
- `GET /buyers/:id/outstanding`

---

### `/app/inventory` — Stock Overview
**Perm:** `inventory.view`  
**Layout:** 4 yarn-type KPI cards at top; batch list table below.  
**Components:**
- KPI cards: yarn type name, on-hand (kg), reorder level, below-reorder `Badge` (red if true)
- Batch table: code, yarn type, supplier, received date, remaining bar, status
- "Receive Yarn" button → `/app/inventory/receive`
- "View Movements" link → movements drawer

**API:**
- `GET /inventory/stock-levels`
- `GET /inventory/batches?limit=50`

**Empty:** "No batches received yet"  
**Loading:** skeleton cards + skeleton table

---

### `/app/inventory/batches/:id` — Batch Detail
**Perm:** `inventory.view`  
**Layout:** single card + movements table.  
**Components:**
- Batch info: code, yarn type, supplier, received date, received/remaining bars, rate
- Movement history table: date, kind badge, qty (g), order/job ref, actor
- Issue / Return / Adjust buttons (inventory.manage)

**API:**
- `GET /inventory/batches/:id`
- `GET /inventory/stock-movements?batch_id=:id`

---

### `/app/inventory/receive` — Receive Yarn (Console)
**Perm:** `inventory.manage`  
**Layout:** same stepped flow as `/w/receive` but in a modal/drawer from inventory page.  
**API:** same as `/w/receive`

---

### `/app/suppliers` — Suppliers List
**Perm:** `inventory.view`  
**Layout:** table.  
**Columns:** Code | Name | Terms | Yarns supplied | Outstanding bills  
**API:** `GET /suppliers`  
**Empty:** "No suppliers"

---

### `/app/purchase-orders` — Purchase Orders
**Perm:** `inventory.view`  
**Layout:** table with "New PO" button.  
**Columns:** Code | Supplier | Yarn type | Qty (kg) | Expected date | Status | Bill status  
**API:**
- `GET /purchase-orders`
- `POST /purchase-orders`
- `PATCH /purchase-orders/:id`

**Empty:** "No purchase orders"

---

### `/app/production` — Production Overview
**Perm:** `production.view`  
**Layout:** 3-pane: today's output totals bar + jobs table + alerts sidebar.  
**Components:**
- Today's output KPIs per stage (m or kg)
- Jobs table: code, order, stage, machine, operator, status, progress bar, health badge
- Breakdown / at-risk alerts from Ripple

**API:**
- `GET /production/today`
- `GET /jobs?status=in_progress,queued`
- `GET /ripple/forecast`

---

### `/app/machines` — Machines List
**Perm:** `production.view`  
**Layout:** grid of machine cards (matches floor grid layout).  
**Components:**
- Machine card: code, name, stage badge, status pill (colour), progress ring, operator name, "Since" duration
- Clicking → `/app/machines/:id`

**API:** `GET /production/floor`  
**Loading:** skeleton cards

---

### `/app/machines/:id` — Machine Detail
**Perm:** `production.view`  
**Layout:** 2-column: left (machine info + actions) | right (current job + queue + events).  
**Components:**
- Machine header: code, name, stage, status pill, grid position
- Current job card with progress bar + operator
- Job queue list (queued jobs, drag-to-reorder if `production.plan`)
- "Report Breakdown" / "Start Maintenance" buttons
- Event history table (last 20)
- `<BolButton />` pre-filled with machine context

**API:**
- `GET /machines/:id`
- `GET /jobs?machine_id=:id`
- `GET /machines/:id/events`
- `POST /machines/:id/breakdown`, `/repaired`, `/maintenance`
- `POST /jobs/reorder` (drag-to-reorder queue)

---

### `/app/quality` — Quality Overview
**Perm:** `quality.view`  
**Layout:** 4 KPI cards + tabs.  
**Components:**
- KPIs: Pending QC | Passed (today) | Rework | Rejected (today)
- Tabs: Queue | Defect Detective
- Queue tab: table of pending_qc rolls — code, order, length, created at, "Inspect" action
- Defect Detective tab: bar chart by machine/shift/batch; flagged patterns (≥ 2× average)

**API:**
- `GET /quality/queues`
- `GET /quality/defect-patterns`

**Empty:** Queue empty → "No rolls awaiting inspection"  
**Loading:** skeleton

---

### `/app/rolls/:id` — Roll Detail
**Perm:** `quality.view`  
**Layout:** single card.  
**Components:**
- Roll code, order, job, length
- QC decision badge + defect list
- Timeline: created → inspected → reworked?
- "Inspect" button if pending_qc (quality.inspect)
- "Rework Complete" if rework (quality.inspect)
- Link → passport

**API:**
- `GET /rolls/:id`
- `POST /rolls/:id/inspections`
- `POST /rolls/:id/rework-complete`

---

### `/app/rolls/:id/passport` — Roll Passport
**Perm:** `rolls.passport`  
**Layout:** printable-friendly single scroll; print button at top.  
**Components:**
- Mill header (name + logo area)
- Roll code + QR
- Full provenance chain: yarn batch → job start → weaving → dyeing → finishing → QC
- Each step: actor, timestamp, qty, machine
- Cost breakdown (if `finance.view_costs`): yarn cost, machine time cost, overhead, total
- Defect record (if any)
- "Print" / "Download PDF" button

**API:**
- `GET /rolls/:id/passport`

---

### `/app/dispatch` — Dispatch Overview
**Perm:** `dispatch.view`  
**Layout:** 2-column: finished stock list (left) | dispatch list (right).  
**Components:**
- Finished stock table: order, fabric, passed rolls count, total metres, shelf — "Start Dispatch" per order
- Aged stock banner (rolls > aged_stock_days unpicked)
- Dispatch list: code, order, status, roll count, dispatched at

**API:**
- `GET /dispatch/finished-stock`
- `GET /dispatch/aged-stock`
- `GET /dispatches`
- `POST /dispatches`

**Empty:** "No passed rolls ready to dispatch"

---

### `/app/dispatch/:id` — Dispatch Detail
**Perm:** `dispatch.view`  
**Layout:** 2-column: info + scanned rolls table | scan input.  
**Components:**
- Dispatch header: order code, vehicle no, transporter
- Roll scan panel: input + camera scan + instant feedback strip
- Scanned rolls table: code, length, status icon
- Remove roll button per row
- "Confirm Dispatch" button + `ConfirmDialog` (warns if pending QC)
- "Download Packing List PDF" link (post-confirm)
- Status update: in_transit → delivered

**API:**
- `GET /dispatches/:id`
- `POST /dispatches/:id/scan` [idem]
- `DELETE /dispatches/:id/items/:roll_id`
- `POST /dispatches/:id/confirm`
- `POST /dispatches/:id/status`
- `GET /dispatches/:id/packing-list.pdf`

---

### `/app/workers` — Workers List
**Perm:** `workers.view`  
**Layout:** searchable table.  
**Columns:** Code | Name | Skills (badges) | Shift | Wage type | Status (checked in?)  
**Wage fields** only shown if `payroll.view`.  
**API:**
- `GET /workers`

**Empty:** "No workers added"

---

### `/app/attendance` — Attendance
**Perm:** `attendance.view`  
**Layout:** date picker at top; per-shift grid of workers × status.  
**Components:**
- Date selector (default today)
- Grid: row = worker, col = A/B/C shift, cell = present/absent/half_day badge + edit icon
- "Check in" action for supervisor (`attendance.manage`)
- Summary row: total present / absent / half_day

**API:**
- `GET /attendance?date=`
- `PATCH /attendance/:id`
- `POST /attendance/check-in`, `/check-out`

---

### `/app/payroll` — Payroll Runs List
**Perm:** `payroll.view`  
**Layout:** table of payroll runs.  
**Columns:** Period | Status (draft/approved/paid) | Total wages | Computed at | Actions  
**Actions:** View | Approve (`payroll.approve`) | Mark Paid  
**API:**
- `GET /payroll/runs`
- `POST /payroll/runs` (compute run)

**Empty:** "No payroll runs yet"

---

### `/app/payroll/:id` — Payroll Run Detail
**Perm:** `payroll.view`  
**Layout:** summary KPIs + worker breakdown table.  
**Components:**
- Period header + status badge
- KPIs: Total workers | Total wages | Advances deducted | Net payout
- Worker table: code, name, shift, days present, wage type, gross, advance, net
- "Approve" / "Mark Paid" / "Download Payslips PDF" buttons

**API:**
- `GET /payroll/runs/:id`
- `POST /payroll/runs/:id/approve`
- `POST /payroll/runs/:id/mark-paid`
- `GET /payroll/runs/:id/payslips.pdf`

---

### `/app/finance` — Finance Overview
**Perm:** `finance.view`  
**Layout:** KPI cards + 2-column tables.  
**Components:**
- KPIs: Cash in MTD | Receivables | Payables | Expenses MTD
- Receivables table (top overdue): buyer, amount, ageing bucket, days overdue
- Supplier bills table: pending / unpaid
- Quick links: Invoices | Payments | Supplier Bills | Expenses | Month Close

**API:**
- `GET /finance/receivables`
- `GET /finance/payables`

---

### `/app/finance/month-close` — Month Close
**Perm:** `finance.view`  
**Layout:** single-page report.  
**Components:**
- Month selector
- P&L summary: Revenue | Yarn cost | Machine cost | Labour (wages) | Overhead | Expenses | Profit
- Per-order margin table
- Per-machine output table
- "Export" button

**API:**
- `GET /finance/month-close?month=YYYY-MM`

**Loading:** skeleton report  
**Empty:** "No data for this month"

---

### `/app/invoices/:id` — Invoice Detail
**Perm:** `finance.view`  
**Layout:** invoice card (print-friendly).  
**Components:**
- INV number, buyer, dispatch, issued date, due date
- Line items (fabric type, qty, unit price, subtotal)
- GST breakdown
- Total in Indian lakh/crore + "Rupees [amount] only" in words
- Payments received timeline
- Status badge + "Record Payment" button (`finance.record_payment`)
- "Download PDF" link

**API:**
- `GET /invoices/:id`
- `GET /invoices/:id.pdf`
- `POST /payments`

---

### `/app/payments` — Payment Records
**Perm:** `finance.view`  
**Layout:** table + "Record Payment" button.  
**Columns:** Date | Buyer | Amount | Method | Reference | Invoices allocated  
**API:**
- `GET /payments` (if endpoint exists; else derived from invoices)
- `POST /payments`

---

### `/app/supplier-bills` — Supplier Bills
**Perm:** `finance.view`  
**Layout:** table.  
**Columns:** Code | Supplier | Batch | Amount | Due date | Status | Actions  
**API:**
- `GET /supplier-bills`
- `POST /supplier-bills`
- `POST /supplier-bills/:id/payments`

---

### `/app/expenses` — Expenses
**Perm:** `finance.view`  
**Layout:** table + "Add Expense" button.  
**Columns:** Date | Category | Amount | Description | Recorded by  
**API:**
- `GET /expenses`
- `POST /expenses`

---

## Ripple Lane Routes (owned by Lane B, mounted via `rippleRoutes`)

---

### `/app/ripple` — Ripple Inbox
**Perm:** `ripple.view`  
**Layout:** list of open Ripple events + summary KPI bar.  
**Components:**
- KPI bar: open events | at-risk orders | total at-risk paise
- Event list: each card shows event code, type, affected orders (with health badges), slack minutes, created at, top fix preview
- Resolve / Dismiss per event
- `<RippleLiveToaster />` (subscribes to `ripple.created` WS events)

**API:**
- `GET /ripple/events?status=open`
- `GET /ripple/forecast`

**Empty:** "No open issues — all orders on track" (green banner)

---

### `/app/ripple/:id` — Ripple Event Detail
**Perm:** `ripple.view`  
**Layout:** 2-column: event summary (left) | ranked fixes (right).  
**Components:**
- Event header: code, type, triggered at, affected jobs/machines/orders
- Impact summary: at-risk paise breakdown (idle + penalty)
- Fix cards ranked 1, 2, 3:
  - Description, outcome (orders on time Y/N), cost estimate
  - "Apply Fix" button (`ripple.apply`) + `ConfirmDialog` (shows `expected_state_version` warning)
- "Dismiss" with reason input
- "What-If" link → `/app/what-if` pre-populated

**API:**
- `GET /ripple/events/:id`
- `POST /ripple/events/:id/fixes/:fix_id/apply`
- `POST /ripple/events/:id/dismiss`

**Error:** 409 STALE_SNAPSHOT → "The situation has changed since you opened this page. Reload to see the latest fixes."

---

### `/app/leak` — Leak Meter
**Perm:** `leak.view`  
**Layout:** 2-column: today's total + category breakdown (left) | daily trend chart (right).  
**Components:**
- `<LeakMeterWidget />` full size
- Category cards: Idle | Rework | Waste | Overtime — each with ₹ amount + contributing items (top 3)
- Date-range bar chart (recharts): daily leak by category, 14-day window
- Drill-down drawer: click category → line items (machine/roll/worker, amount, timestamp)

**API:**
- `GET /leak/today`
- `GET /leak?from=D-13&to=D`
- `GET /leak/breakdown?date=&category=`

**Loading:** skeleton chart  
**Empty:** "No leaks recorded today"

---

### `/app/what-if` — What-If Simulator
**Perm:** `ripple.view`  
**Layout:** form on left + diff panel on right.  
**Components:**
- Scenario type selector: breakdown | yarn_delay | rush_order | absence
- Params form (dynamic by type):
  - breakdown: machine select + duration minutes
  - yarn_delay: yarn type + delay days
  - rush_order: fabric type + qty + due date
  - absence: worker select + date
- "Run Simulation" button
- Diff panel: before/after table of affected orders (health colour change, slack delta), estimated cost
- `is_estimate` disclaimer banner

**API:**
- `POST /ripple/what-if`

**Loading:** spinner (engine runs in ~2 s)  
**Error:** toast "Simulation failed"

---

## Admin Routes

---

### `/app/settings` — Mill Settings
**Perm:** `owner` role  
**Layout:** vertical tabs: General | Shifts | Costs | Machines | Roles  
**Components:**
- General: mill name, timezone, GST default, order tolerance
- Shifts: A/B/C start/end times, break duration
- Costs: machine rates, rework cost, overhead, waste norms, health amber threshold
- Machines: table — code, name, stage, default speed, idle cost; add/edit
- Roles: read-only RBAC matrix display

**API:**
- `GET /mill-settings`
- `PATCH /mill-settings`

---

### `/app/users` — Users & Roles
**Perm:** `owner` role  
**Layout:** table.  
**Columns:** Name | Email / Phone | Role badge | Language | Last login | Active toggle  
**Actions:** Invite | Reset PIN | Edit role  
**API:**
- `GET /users`
- `POST /users`
- `PATCH /users/:id`

---

### `/app/audit` — Audit Log
**Perm:** `owner` role  
**Layout:** filterable table.  
**Columns:** Timestamp | Actor | Action | Entity | Entity ID | Before → After (expandable)  
**Filters:** actor, action, entity, date range  
**API:**
- `GET /audit-log?actor_id=&action=&entity=&from=&to=&limit=100`

**Empty:** "No audit events in this range"

---

## Global States

### Loading (all routes)
React Query `isLoading`: show `Skeleton` components matched to the page layout — never a full-page blank.

### Error (all routes)
- Network error (no response): `EmptyState` with retry button + "Check your connection"
- 401: redirect to `/login` (handled in `lib/api.ts` after one refresh attempt)
- 403: `EmptyState` "You don't have permission to view this page"
- 404: `EmptyState` "Not found" + back link
- 500: `EmptyState` "Something went wrong" + retry
- `Toast` for mutation errors (non-blocking)

### WS events → auto-invalidation (via `lib/ws.ts`)
| Event type | Invalidated queries |
|---|---|
| `machine.status_changed` | `production/floor`, `machines/:id` |
| `job.progress` / `job.started` / `job.finished` | `jobs`, `jobs/:id`, `orders/:id` |
| `stock.received` / `stock.issued` | `inventory/stock-levels`, `inventory/batches` |
| `stock.low` | `inventory/stock-levels` + show `Toast` notification |
| `roll.inspected` | `quality/queues`, `rolls/:id` |
| `dispatch.confirmed` | `dispatches`, `dispatch/finished-stock` |
| `forecast.updated` | `ripple/forecast`, `ripple/events` |
| `leak.updated` | `leak/today` |
| `notification.created` | notification bell count |
