# LoomLink — Demo Script (D = 2026-10-10, 11:00 IST)

## Setup (before demo)

```bash
docker compose up -d
docker compose exec api python -m app.seed.run --reset
# Wait ~10 s for seed to finish
```

Open `http://localhost:5173` in a browser.

---

## Scene 1: Owner login + Dashboard (1 min)

1. Go to `/login` → employee code `OWN-001`, password `demo1234` → **Login**
2. Dashboard opens: active orders, Leak Meter widget, Ripple inbox widget, floor overview
3. Point out: **ORD-112 blocked** (blue yarn short) visible in the orders list

---

## Scene 2: Inventory — yarn shortage (1 min)

1. Click **Inventory** → Yarn tab
2. Show **YT-COT-40S-BLU** (Cotton 40s blue): stock ≈ 78 kg, reorder level 120 kg → **⚠ LOW** badge
3. Show batch YB-2610-02 details
4. Mention: 40 kg truck "at the gate" — will receive it in Scene 6

---

## Scene 3: Floor view + active jobs (1 min)

1. Click **Floor** → machine grid
2. WV-01 green (ORD-102 running), WV-02 green (ORD-104 running), WV-03 green (ORD-109 running)
3. DY-02 **amber/idle** — Idle Hunter alert
4. SP-01 green (ORD-110 spinning)

---

## Scene 4: Quality — defect patterns (1 min)

1. Click **Quality** → show roll list
2. Filter by machine WV-03: recent rolls show UNEVEN_WEAVE flag
3. Show roll passport for a passed roll: all stages green

---

## Scene 5: Ripple — WV-02 breakdown (3 min) ★ main demo

1. Click **Production** → WV-02 → **Report breakdown** → reason MOTOR_FAULT, repair 360 min → Submit
2. Ripple fires automatically → go to `/app/ripple`
3. **Ripple Inbox** shows: "WV-02 motor fault — ORD-104 and ORD-107 at risk"
4. At-risk value ≈ ₹7,700 (idle cost + late penalty)
5. Click the event → order health: ORD-104 **RED**, ORD-107 **RED**, ORD-109 unchanged (green)
6. Ranked fixes:
   - **Fix #1**: Move ORD-104 to WV-01 at 14:00 + overtime night shift on WV-02 for ORD-107 → cost ≈ ₹1,200
   - **Fix #2**: Split across WV-01/WV-03 → ≈ ₹1,800, ORD-109 slack shrinks
   - **Fix #3**: Move ORD-104 to WV-01 only → 2/3 on time, ₹0
7. Click **Apply** on Fix #1 → all three orders turn green/amber
8. Leak Meter updates: overtime ≈ ₹1,200 added; WV-02 idle cost visible

---

## Scene 6: Receive yarn + unblock ORD-112 (1 min)

1. Click **Inventory** → **Receive Yarn**
2. Supplier: Vel Spinners, yarn: Cotton 40s blue, qty: 40 kg, rate: ₹245/kg → **Receive**
3. Stock updates → LOW badge clears
4. **Orders** → ORD-112 → status changes from "blocked" to "confirmed"

---

## Scene 7: Worker PIN app (30 s)

1. New tab → `/pin` → PIN `1234` → any of EMP-001..EMP-012 logs in
2. Worker home: My Jobs, Check-in button, language auto-set to worker's preference

---

## Scene 8: Buyer portal (30 s)

1. Go to `/buyer-line`
2. Enter tracking token for ORD-102 → delivery timeline visible
3. Kaveri Garments sees order status without a console login

---

## Scene 9: Finance — Leak Meter end of day (30 s)

1. `/app/leak` → breakdown: Idle ₹6,300 · Rework ₹4,850 · Waste ₹2,000 · Overtime ₹1,200 ≈ **₹14,350/day**
2. "Every ₹14K/day saved = ₹50 lakh/year"

---

## Cleanup

```bash
docker compose down -v
```
