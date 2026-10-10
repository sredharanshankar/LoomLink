# LoomLink — Demo Mill Seed Data

The seed builds a believable, internally consistent mill. **All names are fictional.**
Every date is relative to **D = demo day** (the mill-local date of `DEMO_CLOCK_START`, or today if that is empty). The demo "now" is **D 11:00 IST**.

Ownership:
- `backend/app/seed/base.py` (Lane A): master data, users, settings.
- `backend/app/seed/history.py` (Lane A): the past 14 days of operations, completed orders, finance.
- `backend/app/seed/scenario_demo.py` (Lane B): today's live state at D 11:00, tuned so the Ripple demo story plays out exactly (§9). It runs **after** base and history.
- `backend/app/seed/run.py`: `python -m app.seed.run --reset` drops and recreates the schema (`alembic downgrade base && upgrade head`), then runs base → history → scenario. `make demo-reset` calls it.

Seed must be **deterministic** (`random.Random(42)`), idempotent with `--reset`, and finish in under 20 seconds.

---

## 1. Mill settings
- mill_name: **Everest Textile Mills**; timezone Asia/Kolkata.
- Shifts: A 06:00–14:00 (30 min break), B 14:00–22:00 (30 min break), C 22:00–06:00 (overtime only).
- gst_default_bp 500 · overtime_multiplier_bp 15000 · order_tolerance_bp 200 · aged_stock_days 7.
- qc_packing_paise_per_roll 18000 (₹180) · overhead_paise_per_m 530 (₹5.30/m).
- machine_rate_paise_per_hour: spinning 25000, weaving 45000, dyeing 60000, finishing 40000.
- rework_cost_paise_per_m 1650 · rework_minutes_per_roll 45 · qc_buffer_minutes 240 · dispatch_buffer_minutes 120.
- waste_norm_bp: spinning 300, weaving 200, dyeing 150, finishing 100.
- health_amber_minutes 1440 · ripple_slip_threshold_minutes 60.

## 2. People

### Staff users (see `docs/RBAC.md` §5 for credentials)
| Name | Role |
|---|---|
| Rajendran (owner) | owner |
| Meenakshi (production manager) | manager |
| Balu (storekeeper) | storekeeper |
| Kavitha (QC inspector) | qc_inspector |
| Saravanan (dispatch) | dispatch |
| Lalitha (accounts) | accounts |
| Kaveri Garments buyer user | buyer |

### Workers (operators; each also has a user with PIN 1234)
| Code | Name | Skill stages | Wage | Default shift | Language |
|---|---|---|---|---|---|
| EMP-001 | Ravi | weaving | daily ₹800 | A | te |
| EMP-002 | Murugan | weaving | daily ₹800 | A | ta |
| EMP-003 | Lakshmi | weaving | daily ₹780 | A | ta |
| EMP-004 | Suresh | weaving | daily ₹800 | B | hi |
| EMP-005 | Priya | weaving | daily ₹780 | B | te |
| EMP-006 | Karthik | weaving, finishing | daily ₹820 | B | ta |
| EMP-007 | Anitha | dyeing | daily ₹850 | A | te |
| EMP-008 | Ganesh | dyeing | daily ₹850 | B | hi |
| EMP-009 | Selvi | finishing | daily ₹760 | A | ta |
| EMP-010 | Arjun | finishing | piece ₹1.20/m | B | hi |
| EMP-011 | Meena | spinning | daily ₹740 | A | te |
| EMP-012 | Prakash | weaving, dyeing | hourly ₹105 | A (overtime-willing) | hi |

## 3. Suppliers & yarn
| Supplier | Code | Supplies | Terms |
|---|---|---|---|
| Vel Spinners | SUP-001 | cotton 40s white, cotton 40s blue | 30 days |
| Annapoorna Yarns | SUP-002 | poly-cotton 2/40s grey, cotton 30s navy | 45 days |
| Kongu Cotton Traders | SUP-003 | cotton 40s white, cotton 30s navy | 30 days |

| Yarn type | Code | Reorder level | Std rate |
|---|---|---|---|
| Cotton 40s white | YT-COT-40S-WHT | 150 kg | ₹210/kg |
| Cotton 40s blue | YT-COT-40S-BLU | 120 kg | ₹245/kg |
| Poly-cotton 2/40s grey | YT-PC-240S-GRY | 100 kg | ₹190/kg |
| Cotton 30s navy | YT-COT-30S-NVY | 100 kg | ₹260/kg |

## 4. Fabrics & routes
Route templates: **R1 "Weave → Dye → Finish"** (default), **R2 "Spin → Weave → Dye → Finish"**.

| Fabric | Code | Width | GSM | Yarn | Yarn per 100 m | Default price | Route |
|---|---|---|---|---|---|---|---|
| Blue cotton poplin | FAB-POP-BLU | 147 cm | 110 | YT-COT-40S-BLU | 14.3 kg | ₹125/m | R1 |
| Grey poplin | FAB-POP-GRY | 147 cm | 105 | YT-PC-240S-GRY | 13.5 kg | ₹98/m | R1 |
| White sheeting | FAB-SHT-WHT | 228 cm | 140 | YT-COT-40S-WHT | 26.0 kg | ₹160/m | R1 |
| Navy twill | FAB-TWL-NVY | 150 cm | 210 | YT-COT-30S-NVY | 27.5 kg | ₹185/m | R2 |

## 5. Machines and floor layout (grid 12 × 8; x left→right, y top→bottom)
| Code | Name | Stage | Default speed | Idle cost | x,y | Notes |
|---|---|---|---|---|---|---|
| SP-01 | Ring frame 1 | spinning | 12 kg/h | ₹300/h | 2,1 | |
| WV-01 | Air-jet loom 1 | weaving | 45 m/h | ₹450/h | 4,1 | all fabrics ≤ 190 cm |
| WV-02 | Air-jet loom 2 | weaving | 45 m/h | ₹450/h | 4,3 | all fabrics ≤ 190 cm |
| WV-03 | Air-jet loom 3 | weaving | 40 m/h | ₹450/h | 4,5 | wide loom: all fabrics (sheeting too) |
| DY-01 | Jigger 1 | dyeing | 150 m/h | ₹600/h | 7,2 | |
| DY-02 | Jigger 2 | dyeing | 150 m/h | ₹600/h | 7,4 | |
| FN-01 | Stenter | finishing | 300 m/h | ₹400/h | 9,3 | |

Zones (for the map): Receiving & store x 0–1; Spinning x 2–3; Weaving x 4–6; Dyeing x 7–8; Finishing x 9; QC x 10; Dispatch x 11.
Capabilities: WV-01 and WV-02 have `machine_capabilities` rows for every fabric except FAB-SHT-WHT, so sheeting only runs on WV-03.

## 6. Buyers
| Buyer | Code | Terms | Late penalty |
|---|---|---|---|
| Kaveri Garments | BUY-001 | 30 days | ₹3,000/day |
| Deccan Linens | BUY-002 | 45 days | ₹5,000/day |
| Coastal Exports | BUY-003 | 30 days | ₹4,000/day |
| Nilgiri Home Textiles | BUY-004 | 60 days | ₹2,000/day |

## 7. History (D−14 … D−1) — Lane A, `history.py`
- **Completed orders:**
  - ORD-101: Nilgiri, white sheeting 1,800 m. Dispatched D−9, invoiced, **fully paid**, closed.
  - ORD-103: Kaveri, blue poplin 1,000 m. Dispatched D−5, invoice **half paid**.
  - ORD-105: Coastal, grey poplin 1,500 m. Dispatched D−3, **unpaid** (within terms).
  - ORD-106: Deccan, grey poplin 600 m. Dispatched D−12, **unpaid and overdue** (to show receivables ageing).
- **Progress logs** every 1–3 h per running job, with realistic jitter (±10%), so Ripple can learn machine speeds. WV-03 runs about 10% slower than its default speed.
- **Attendance** for all workers on every working day (Sundays off; 1–2 random absences; one half day). Overtime: 2 night shifts by EMP-012.
- **Rolls & QC:** about 60 rolls, 90–110 m each.
  - Pass rate about 88%.
  - **Pattern 1:** 6 of the last 10 rolls woven on WV-03 have UNEVEN_WEAVE (rework).
  - **Pattern 2:** 3 rolls whose yarn came from batch **YB-2609-11** have COLOUR_MISMATCH (1 rejected, 2 rework).
- **Yarn batches:** about 10 received over the period from the three suppliers, with supplier bills (some paid, some unpaid).
  - Batch codes use the month of receipt: YB-2609-xx for last month and YB-2610-xx for this month. If D is not in October 2026, generate codes from the real dates. The named batches below are aliases that history.py must create with exactly those codes.
- **Expenses this month:** electricity ₹1,85,000 · maintenance ₹22,000 · transport ₹18,500 · staff salaries ₹1,10,000.
- **Payroll:** last month approved and paid. This month: no run yet. Month Close computes wages from attendance.
- **Leak history** (written by Lane B's scenario from these events, not by A): idle, rework and overtime entries for the past days.

## 8. Live state at D 11:00 — Lane B, `scenario_demo.py`
| Order | Buyer | Fabric | Qty | Due | Status at 11:00 |
|---|---|---|---|---|---|
| ORD-102 | Kaveri | grey poplin (FAB-POP-GRY) | 900 m | D+1 | weaving on **WV-01**, finishes ≈ 14:00 today |
| ORD-104 | Kaveri | blue poplin | 1,200 m | D+3 | weaving on **WV-02**, 500 m done, 700 m left |
| ORD-107 | Deccan | grey poplin | 800 m | D+4 | confirmed, queued **next on WV-02** |
| ORD-109 | Coastal | white sheeting | 1,500 m | D+7 | weaving on **WV-03** |
| ORD-110 | Nilgiri | navy twill (R2) | 1,000 m | D+10 | spinning on SP-01 |
| ORD-112 | Kaveri | blue poplin | 600 m | D+9 | confirmed, **blocked: blue yarn short** (≈ 40 kg short) |
| draft (no code until confirmed) | Kaveri | navy twill | 2,000 m | requested D+8 | for the Promise Date demo |

Also at 11:00:
- DY-01 is dyeing ORD-102's previous lot (or is idle, whichever makes the Idle Hunter demo work). DY-02 is idle. FN-01 is finishing ORD-104's earlier rolls.
- Blue yarn stock is below the reorder level (low-stock alert active). A truck with **40 kg of blue cotton from Vel Spinners** is "at the gate" (the demo receives it live).
- Rolls ROLL-104-01 … ROLL-104-06 are passed, ROLL-104-07 is passed (its passport is the closing moment), and ROLL-104-08 is pending QC.
- Workers on shift A are checked in. EMP-012 is available for overtime.

## 9. The Ripple demo story (scenario must reproduce this; covered by an automated test)
Action: at D ≈ 11:20, the WV-02 operator reports **breakdown, MOTOR_FAULT, estimated repair 360 min**.

Expected Ripple result (B calibrates speeds, queue and buffers so that this holds):
1. **Before** the breakdown: ORD-104 has about +1 day of slack (green/amber), ORD-107 about +1 day, ORD-109 about +2 days.
2. **After:** ORD-104 becomes **late (red)**, ORD-107 becomes **late by about 1 day (red)**, ORD-109 is **unaffected**.
3. **At risk ≈ ₹7,700** = WV-02 idle 6 h × ₹450 (₹2,700) + ORD-107 late penalty 1 day × ₹5,000. ORD-104's lateness is under one day; if your penalty rule rounds it to zero, say so in the breakdown.
4. Fixes ranked:
   - **#1** Move ORD-104's remaining 700 m to WV-01 at 14:00 **+** one overtime night shift (C) on WV-02 after repair for ORD-107. Result: 3/3 orders on time, about ₹1,200 overtime.
   - **#2** Move ORD-104 to WV-01 **+** split ORD-107 across WV-01/WV-03. Result: 3/3 on time, about ₹1,800 in changeovers, and ORD-109's slack shrinks.
   - **#3** Move ORD-104 to WV-01 only. Result: 2/3 on time, ₹0.
5. Applying #1 makes all three orders green or amber. The Leak Meter then shows the breakdown's actual cost (idle + overtime ≈ ₹3,900).

Exact rupee values may differ slightly after calibration. The **ranking and the red/green outcomes must match.**

## 10. Day's Leak Meter at 11:00 (approximately)
Idle ₹6,300 (≈14 machine-hours of open-shift time since 06:00 across idle machines) · rework ₹4,850 (3 rolls) · waste ₹2,000 · overtime ₹1,200 → ≈ ₹14,350. Tune history and scenario so this is roughly right; the categories must all be non-zero.
