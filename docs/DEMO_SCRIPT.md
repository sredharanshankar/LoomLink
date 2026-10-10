# LoomLink — 7-Minute Demo Script

> Source: docs/CONCEPT.md §9 "The 7-minute demo". Lane A extends this with actual demo steps.

## Setup
1. Run `make demo-reset` to recreate the database and seed the demo mill.
2. Open https://localhost:5173 in a desktop browser.
3. Have a mobile phone on the same LAN ready (https://<LAN-IP>:5173, accept the certificate once).

## Demo accounts
| Who | Login | Password |
|---|---|---|
| Mill owner (Rajendran) | owner@everest.test | Owner@123 |
| Production manager (Meenakshi) | manager@everest.test | Manager@123 |
| Storekeeper (Balu) | store@everest.test | Store@123 |
| QC inspector (Kavitha) | qc@everest.test | Qc@12345 |
| Dispatch clerk (Saravanan) | dispatch@everest.test | Dispatch@123 |
| Accounts (Lalitha) | accounts@everest.test | Accounts@123 |
| Buyer (Kaveri Garments) | buyer.kaveri@everest.test | Buyer@123 |
| Operator (any, e.g. Ravi) | EMP-001 + PIN 1234 | — |

## 7-Minute Flow (to be completed by Lane A/B after feature implementation)

**Minute 1 — Owner dashboard**
- Log in as owner. Show the KPI tiles: orders due this week, at-risk count (Ripple), today's output, cash in MTD.

**Minute 2 — New order + promise date**
- Create a new order for Kaveri Garments: 500 m Blue cotton poplin, due in 10 days.
- Show the Ripple promise-date panel — earliest dispatch date, limiting factor.

**Minute 3 — Floor map & Ripple**
- Navigate to /app/floor. Show machines, their live status, job progress.
- Trigger a WV-02 breakdown via the simulator. Watch Ripple surface a risk event in the inbox.

**Minute 4 — Ripple fix application**
- Open the Ripple event. Review the suggested fix (reassign to WV-03 + overtime).
- Apply the fix. Watch the floor map update and the order health flip from red to green.

**Minute 5 — Operator mobile flow**
- On a phone, log in as EMP-001 (PIN 1234). Show the worker home screen.
- Scan a machine QR. Start a job, report progress via voice ("wove 50 metres").

**Minute 6 — QC & dispatch**
- Log in as QC inspector. Inspect a roll — pass it. Navigate to dispatch and load the roll.
- Confirm the dispatch. Show the auto-generated invoice.

**Minute 7 — Buyer tracking**
- Open the public tracking link (/track/<token>) without logging in.
- Show the buyer-safe order status, predicted dispatch date, and shipment info.