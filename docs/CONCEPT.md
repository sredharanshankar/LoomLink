> **Note for engineers:** this is the product concept. The team split in §8.2 is superseded by `docs/OWNERSHIP.md` (3 lanes), and all technical details are superseded by `docs/CONTRACT.md`. When they conflict, CONTRACT.md wins.

**LOOMLINK**

The mill that sees ahead

A QR-traced textile manufacturing platform for Everest Textile Mills, with **Ripple** — a live consequence engine that turns every event on the factory floor into its impact on orders, buyers and rupees, and the best fix.

| **Layer**         | **What it does**                                                                                                       | **Question it answers**                                      |
|-------------------|------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------|
| **LoomLink Core** | QR backbone: yarn batches, machines and rolls carry identities; every movement is recorded once, correctly             | What is happening right now?                                 |
| **Ripple Engine** | Live forecast of the whole mill; recomputes the moment anything changes; prices the impact; proposes and applies fixes | What does it mean, what will it cost, and what should we do? |

Hackathon concept document \| Problem statement: Textile Manufacturing System — "Build one system to replace notebooks and phone calls."

**Contents**

1\. The idea on one page

2\. Understanding the problem completely

3\. Layer 1 — LoomLink Core: the QR backbone

4\. Layer 2 — Ripple: the signature idea

5\. Supporting differentiators

6\. A day at Everest — before and after

7\. How it is built

8\. Hackathon execution plan

9\. The 7-minute demo

10\. Questions judges will ask

11\. Expected impact

12\. After the hackathon

13\. Final pitch

1\. The idea on one page

Everest Textile Mills runs on notebooks, paper slips, registers, phone calls and walking the floor. The brief names the result in one sentence: **orders get delayed, machines sit idle, and nobody knows the real cost of a single roll of fabric.**

Most teams will digitise the notebooks: a stock screen, a machine screen, a QC form, a dashboard. That fixes recording. It does not fix the real failure. Even with perfect screens, when a loom breaks at 11:20 the manager still has to work out in his head which orders are now late, which buyer to call, what it will cost and what to move where. That mental arithmetic is exactly where delays, idle time and hidden cost come from today.

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<tbody>
<tr class="odd">
<td><p><strong>Our answer: two layers</strong></p>
<p><strong>Layer 1 — LoomLink Core (the present).</strong> Every yarn batch, machine and fabric roll gets a QR identity. Workers scan instead of writing. Stock, production, quality, dispatch, attendance and money live in one database. This is the complete QR plan, kept intact and sharpened against the brief.</p>
<p><strong>Layer 2 — Ripple (the future and the money).</strong> A live forecast of the entire mill that recomputes in milliseconds whenever anything changes. Every event becomes a Ripple: which orders move, by how many hours, which buyers are affected, how many rupees are at stake — and the three best fixes, each already simulated. One tap applies the fix, updates workers' phones and tells buyers only when their promise actually changes.</p></td>
</tr>
</tbody>
</table>

The signature moment

In the demo we break a loom. A ripple spreads across the floor map from the broken machine to two orders, which turn red. A Ripple Card shows "2 orders late, ₹7,700 at risk" and three ranked fixes. The manager taps one. The orders turn green, the next operator's phone shows his new job, and the owner's Leak Meter records what the breakdown really cost. Fifteen seconds, no phone call, no walk.

Why this wins

- **Directly on the brief.** Every one of the six scenes is covered end to end, and Ripple attacks all three named failures: delays (predicted and recovered), idle machines (detected and filled), unknown cost (every roll and every event priced).

- **Genuinely different.** Trackers show state. Ripple shows consequences and decisions. That is a category jump, not a feature.

- **Buildable in a hackathon.** Ripple is a deterministic, explainable scheduling engine over a small mill (tens of machines, hundreds of jobs) — a few hundred lines of Python, recomputing in well under a second.

- **Honest.** No fake sensors, no "AI" label on rules. Forecasts show their confidence; costs show their assumptions.

- **Realistic for an Indian mill.** Phones and printed labels only. Workers scan or speak in Telugu, Tamil, Hindi or English. Buyers get a link or a WhatsApp reply instead of a callback.

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<tbody>
<tr class="odd">
<td><p><strong>One line</strong></p>
<p>"Every other system tells Everest what happened. LoomLink tells them what it means — and what to do next."</p></td>
</tr>
</tbody>
</table>

2\. Understanding the problem completely

2.1 The five broken practices

| **Today at Everest**                          | **What it causes**                                                            | **LoomLink replacement**                                                                                    |
|-----------------------------------------------|-------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| Raw material stock in a notebook              | Nobody knows true stock; orders start without enough yarn; surprise shortages | Batch QR + stock ledger; reorder levels; yarn check on every new order; automatic "to buy" list             |
| Machine and order status by walking the floor | Idle machines go unnoticed; status is always stale; delays found late         | Machine QR scans; live floor map; progress in metres; Idle Hunter alerts                                    |
| Quality checks on paper slips                 | Defects cannot be traced to a machine, shift or yarn batch; repeated defects  | Roll QR + digital inspection; full roll history; Defect Detective patterns                                  |
| Buyer updates by phone call                   | Office staff walk the floor and call back; inconsistent answers; angry buyers | Instant order lookup; buyer tracking link / WhatsApp reply; proactive updates only when the promise changes |
| Attendance and wages in a register            | Labour cost unknown per order; payroll errors; no link to output              | Shift check-in, job-time logging, wage calculation, labour cost per order and roll                          |

2.2 The three failures and their real root cause

The brief ends its "How things run today" section with three outcomes. Looking at them closely, they share one root cause.

| **Failure named in brief**           | **Surface cause**                | **Root cause**                                                              |
|--------------------------------------|----------------------------------|-----------------------------------------------------------------------------|
| Orders get delayed                   | Breakdowns, shortages, rework    | Nobody connects an event to its downstream impact until a buyer complains   |
| Machines sit idle                    | No one knows a machine is free   | Nobody sees that an idle machine could absorb work that is about to be late |
| Nobody knows the real cost of a roll | Costs are in different registers | Nobody prices events (idle hours, rework, wastage) or adds up a roll's life |

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<tbody>
<tr class="odd">
<td><p><strong>Key insight</strong></p>
<p>Everest does not just have a <strong>data problem</strong>. It has a <strong>consequence problem</strong>. Digitising records fixes the first. Only a system that continuously computes consequences fixes the second.</p>
<p>LoomLink Core solves the data problem. Ripple solves the consequence problem. Together they deliver what the brief actually asks: a mill where orders are not delayed, machines are not idle, and every roll has a known cost.</p></td>
</tr>
</tbody>
</table>

2.3 The six scenes and the question each one really asks

| **Scene in the brief**      | **Who**               | **The real question**                                                                     | **Must-have answer**                                                                               |
|-----------------------------|-----------------------|-------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| Yarn arrives at the gate    | Storekeeper, planner  | How much do we have, for which order, and can we start the new order?                     | Batch receipt with order link; live stock; low-stock warning; yarn check per order; "to buy" list  |
| Production floor, mid-shift | Supervisor, operators | Which order is on which machine, how far along, what is idle, what did we make today?     | Live floor map; progress in metres; idle list; output today per machine; shift handover            |
| Checking fabric             | QC inspector          | Did it pass, and if not, why — which machine, which yarn?                                 | Pass / rework / reject; roll history to order and machine; waiting-for-QC queue; defect patterns   |
| Buyer calls                 | Office, buyer         | Where is my order and when will it ship?                                                  | Instant status by order ID; honest ship date; buyer self-service link                              |
| Loading the truck           | Dispatch clerk        | Right rolls, right quantity, right buyer, matching invoice, nothing twice?                | Scan-verified dispatch; blocked wrong/rejected/duplicate rolls; invoice; finished-stock shelf view |
| Owner closes the books      | Owner, accounts       | What did each order cost, what did each machine make, what were wages, did we make money? | Order and roll cost; machine output; wages; month profit on one screen                             |

2.4 Who uses LoomLink

| **Person**                      | **Reality on the ground**                                         | **What LoomLink gives them**                                 |
|---------------------------------|-------------------------------------------------------------------|--------------------------------------------------------------|
| Owner                           | Wants answers, not screens; checks the phone in the morning       | Daily Brief, month profit, Leak Meter, Roll Passport         |
| Production manager / supervisor | Firefights breakdowns, shortages and shift gaps all day           | Floor map, Ripple Cards, one-tap fixes, order health         |
| Storekeeper                     | Weighs and stacks yarn, writes in a notebook                      | Receive-and-print in under a minute; scan to issue           |
| Machine operator                | Phone in pocket, gloves, noise; may prefer Telugu, Tamil or Hindi | Scan machine, big buttons, or just speak; sees only his jobs |
| QC inspector                    | Checks rolls at a table, writes slips                             | Scan roll, tap defect type, pass / rework / reject           |
| Dispatch clerk                  | Counts rolls onto a truck                                         | Scan each roll; the system stops mistakes                    |
| Accounts                        | Reconciles bills, wages and payments in separate books            | One place for bills, wages, invoices, receipts               |
| Buyer                           | Calls repeatedly for updates                                      | A link or WhatsApp reply with live status and ship date      |

2.5 Design principles

- **Scan first, speak second, type last.** Every frequent action is a scan or a sentence, never a long form.

- **No new hardware.** Phones the mill already has, printed QR labels and one label printer. Machine sensors are an optional later add-on.

- **One source of truth.** Every screen, forecast and report reads the same ledger. Nothing is entered twice.

- **Every number explains itself.** Tap any cost, date or total to see what it is made of.

- **Never claim what we do not measure.** Forecasts show confidence; costs show assumptions; simulated data is labelled.

3\. Layer 1 — LoomLink Core: the QR backbone

This is the original QR plan, kept as one complete part, simplified for a real small mill and closed against every requirement in the brief. It is the foundation Ripple stands on: Ripple can only forecast what Core records truthfully.

3.1 Four physical identities

| **QR label**           | **Created when**                          | **Identifies**                                                            | **Used for**                                                             |
|------------------------|-------------------------------------------|---------------------------------------------------------------------------|--------------------------------------------------------------------------|
| **Yarn batch QR**      | A yarn delivery is received at the gate   | One received lot: supplier, type, count, colour, kg, cost, intended order | Receiving, stock, issuing yarn to jobs, tracing defects back to supplier |
| **Machine QR**         | A machine is registered (once, permanent) | One physical spinning frame, loom or dyeing machine                       | Starting, logging and finishing jobs; breakdown reports; floor map       |
| **Roll QR**            | A finished roll is formed                 | One physical fabric roll with its length                                  | QC, finished stock, dispatch, Roll Passport                              |
| **WIP tag (optional)** | Material is split between machines        | An intermediate lot moving between stages                                 | Keeping history correct when one order runs on two machines              |

A QR code only carries an ID. It never holds prices, names or status, and scanning it never changes anything by itself. Only a logged-in worker confirming an action changes the record.

3.2 The seven required modules

Module names and order match the problem statement's "What exactly should you build?" table exactly. Items marked **NEW** close gaps found when the earlier plan was checked line by line against the brief.

<table>
<colgroup>
<col style="width: 18%" />
<col style="width: 63%" />
<col style="width: 17%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>Module</strong></th>
<th><strong>What it does</strong></th>
<th><strong>Brief scene</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><strong>1. Raw Material Inventory</strong></td>
<td><p>Receive batch: supplier, type, count, colour, kg, rate, location; print QR</p>
<p><strong>NEW:</strong> supplier directory: contact, yarn types supplied, past deliveries, rates, bills</p>
<p><strong>NEW:</strong> link the batch to the order it is for at receipt (optional, editable)</p>
<p>Stock = on hand, reserved, available; ledger of every movement</p>
<p><strong>NEW:</strong> reorder level per yarn type with low-stock alert</p>
<p>Yarn check on every new order; <strong>NEW:</strong> automatic "to buy" list for shortages</p></td>
<td>Yarn arrives</td>
</tr>
<tr class="even">
<td><strong>2. Production Management</strong></td>
<td><p>Which order is on which machine: scan machine QR → see eligible jobs → start</p>
<p><strong>NEW:</strong> production progress: metres logged during the job, shown as done vs target</p>
<p><strong>NEW:</strong> output today per machine and per shift</p>
<p>Machine availability: running, idle, breakdown, maintenance, changeover — live on the floor map</p>
<p><strong>NEW:</strong> shift handover; breakdown reporting with reason</p></td>
<td>Production floor</td>
</tr>
<tr class="odd">
<td><strong>3. Quality Control</strong></td>
<td><p>Scan roll → inspect: length, defects (hole, colour mismatch, uneven weave, stain)</p>
<p>Classify as passed / rework / rejected</p>
<p>Roll history to order, machine, operator, shift, yarn batch</p>
<p>Queues: waiting for QC, passed, rework, rejected</p>
<p><strong>NEW:</strong> defects grouped by machine, shift and yarn batch (Defect Detective)</p></td>
<td>Checking fabric</td>
</tr>
<tr class="even">
<td><strong>4. Order Management</strong></td>
<td><p>Buyer orders: buyer, fabric specification (type, construction, width, colour), quantity in metres, deadline, price</p>
<p><strong>NEW:</strong> simple yarn rule per fabric (kg per 100 m) to check yarn needs</p>
<p>Route per fabric (e.g. spinning → weaving → dyeing → finishing → QC) and jobs per stage</p>
<p>Production status derived from real events: planned, in production (stage), QC, ready, partly shipped, shipped</p></td>
<td>Yarn arrives, buyer calls</td>
</tr>
<tr class="odd">
<td><strong>5. Dispatch Management</strong></td>
<td><p>Finished fabric: passed rolls by order and shelf location</p>
<p>Scan each roll onto the truck; system blocks wrong buyer, unpassed and already-dispatched rolls</p>
<p>Quantities: rolls and metres per dispatch; <strong>NEW:</strong> partial deliveries with remaining balance</p>
<p>Invoice and packing list generated from the scanned rolls</p>
<p><strong>NEW:</strong> delivery tracking: dispatched → in transit → delivered (vehicle, transporter, delivery date)</p>
<p><strong>NEW:</strong> aged-stock alert for passed rolls not dispatched after N days</p></td>
<td>Loading the truck</td>
</tr>
<tr class="even">
<td><strong>6. Worker Management</strong></td>
<td><p>Worker profiles and shift rosters (morning / evening / night)</p>
<p>Attendance: check-in / check-out, leave, overtime</p>
<p>Wages: daily / hourly / piece-rate calculation for the month, paid / unpaid status</p>
<p>Job time from scans links people to orders → labour cost per order and per roll</p></td>
<td>Production floor, owner</td>
</tr>
<tr class="odd">
<td><strong>7. Financial Management</strong></td>
<td><p>Raw material costs: supplier bills and the cost of yarn actually used per order</p>
<p>Wages: payroll totals and labour cost per order</p>
<p>Customer payments: invoices, payments received, <strong>NEW:</strong> outstanding dues per buyer</p>
<p>Profitability: cost and margin per order and <strong>NEW:</strong> per roll; <strong>NEW:</strong> one-screen monthly profit</p></td>
<td>Owner closes the books</td>
</tr>
</tbody>
</table>

3.3 The operator's flow: scan first, sensors optional

The earlier plan made a machine completion signal the centre of production. Everest has no such signals today, so the primary flow is now the operator's phone. Machine signals remain a supported plug-in for later.

| **Step**     | **Operator does**                                                 | **System does**                                                                                 |
|--------------|-------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| 1\. Start    | Scans the machine QR, taps the job shown                          | Checks machine fits the stage, yarn has been issued, operator is on shift; machine goes RUNNING |
| 2\. Progress | Every few hours taps "+ metres" or says "200 metres done"         | Updates progress bar, output today and Ripple's forecast                                        |
| 3\. Handover | At shift end taps "Hand over" ; the next operator scans to accept | Keeps one continuous job with both operators' time recorded for wages                           |
| 4\. Problem  | Taps "Breakdown" and picks a reason, or speaks it                 | Machine goes BREAKDOWN; Ripple fires instantly                                                  |
| 5\. Finish   | Taps "Finish", confirms final metres and waste                    | Job closes; output moves to the next stage queue; next machine's operator is notified           |

3.4 Trust rules the system never breaks

- Stock never goes below zero; two people issuing the last yarn at once cannot both succeed.

- A scan alone never changes stock; only a confirmed action does.

- Corrections are new entries, never edits to history.

- One machine runs one job at a time.

- A breakdown never counts as a finished job.

- Only passed rolls can be dispatched; no roll can be dispatched twice.

- A buyer sees only their own orders, never costs or worker data.

- Every cost and profit figure says what it includes and what it leaves out.

3.5 Machine signals as an optional plug-in

The hybrid design from the original plan is kept as an extension, not a dependency: where a machine controller can genuinely report "operation complete", an adapter sends that event; the job moves to "awaiting confirmation" and the operator still confirms actual metres and waste. A machine stopping is never treated as a job finishing. In the hackathon, a small simulator can demonstrate this path, clearly labelled as simulated.

4\. Layer 2 — Ripple: the signature idea

Ripple is a live consequence engine. It keeps a forecast of the entire mill — every job, machine, order and promised date — and recomputes it the instant anything changes. Every change becomes a Ripple: what moved, who is affected, what it costs, and what to do.

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<tbody>
<tr class="odd">
<td><p><strong>The Ripple loop</strong></p>
<p><strong>Event</strong> — something happens: a loom breaks, yarn arrives short, a roll fails QC, a worker is absent, a rush order arrives.</p>
<p><strong>Ripple</strong> — the forecast reruns and compares itself to the previous one: which orders moved and by how much.</p>
<p><strong>Rupees</strong> — every effect is priced: idle hours, late penalties, overtime, rework.</p>
<p><strong>Fix</strong> — candidate fixes are generated and each is simulated; the best three are shown with their results.</p>
<p><strong>Tell</strong> — one tap applies the fix, updates operators' job lists and notifies buyers only if their promised date really changed.</p></td>
</tr>
</tbody>
</table>

4.1 Why it is out of the box

| **A typical factory tracker** | **LoomLink with Ripple**                                                                            |
|-------------------------------|-----------------------------------------------------------------------------------------------------|
| Shows a machine is down       | Shows which two orders that breakdown makes late, by how many hours                                 |
| Shows a list of idle machines | Shows which idle machine could rescue which late order                                              |
| Shows stock is low            | Shows which future job will stop, on which day, unless yarn arrives by a specific date              |
| Sales guesses a delivery date | Sales quotes a date computed from real stock, real queues and real machine speeds                   |
| Buyer calls to ask for status | Buyer is told automatically, and only when their date actually changes                              |
| Month-end shows total cost    | Every day shows money leaked to idle time, rework, waste and overtime — while it can still be fixed |
| Manager decides from memory   | Manager picks from three simulated fixes with known outcomes                                        |

Large manufacturers buy this kind of capability as advanced planning software, priced and built for big plants. Small and mid-sized mills like Everest — the ones still using notebooks — have never had it. Ripple brings it to them on a phone, built on top of the simplest possible data capture: a QR scan.

4.2 How Ripple thinks (in plain words)

The mill clock — a live forecast

For every machine, Ripple knows what it is doing, how fast it usually runs for each fabric (learned from the metres operators log), and what is queued next. For every order it knows the remaining metres at each stage. It plays the factory forward in time — stage by stage, job by job, respecting shifts, yarn availability and the order of operations — and produces a predicted finish time for every job and a predicted ship date for every order.

The ripple — comparing two futures

When an event arrives, Ripple plays the factory forward again with the new reality and compares the two futures. The difference is the ripple: orders that slipped, orders that are now late against their due date, machines that will now sit idle, jobs that will now be blocked by missing yarn.

The rupee lens — pricing the ripple

Each effect is converted to money using simple, visible rates the owner sets once: machine idle cost per hour, late penalty per day (from buyer terms), overtime premium, rework cost per metre, yarn cost per kg. The ripple becomes a single figure — "₹7,700 at risk" — that anyone can tap to see how it was calculated.

The fix finder — trying solutions before choosing one

Ripple generates sensible candidate fixes and simulates every one of them in the same way:

- Move a waiting job to a compatible idle machine.

- Run an overtime shift on a machine once it is repaired.

- Split an order across two machines.

- Swap the order of two jobs in a queue.

- Bring a yarn purchase forward, or use a compatible batch reserved for a later order.

Fixes are ranked by **orders kept on time first, then extra cost, then how few changes they need**. Each comes with a plain explanation, such as "WV-01 runs the same fabric and is free at 14:00".

Apply and tell

The manager taps a fix. Ripple re-checks that nothing changed in the meantime, applies the job moves, pushes the new job to the right operator's phone, and refreshes every screen. Buyers are notified only if their promised date moved — so buyers learn to trust LoomLink's messages.

4.3 The five faces of Ripple

Ripple is one engine, but people meet it in five places.

| **Feature**      | **Who sees it**                       | **What it shows**                                                                                               | **Brief failure it attacks** |
|------------------|---------------------------------------|-----------------------------------------------------------------------------------------------------------------|------------------------------|
| **Promise Date** | Sales / owner, when an order comes in | Earliest realistic ship date from real stock, queues and speeds — plus what would make an earlier date possible | Delays, buyer calls          |
| **Order Health** | Everyone, on every order              | Green / amber / red with "slack" — hours to spare before the due date                                           | Delays                       |
| **Ripple Card**  | Manager, on any disruption            | Affected orders, hours lost, rupees at risk, three simulated fixes, one-tap apply                               | Delays, idle machines, cost  |
| **Idle Hunter**  | Supervisor                            | "WV-01 is idle and can take ORD-107, which is at risk" — idle capacity matched to work that needs it            | Idle machines                |
| **Leak Meter**   | Owner                                 | Today's money lost to idle hours, rework, extra yarn waste and overtime, live                                   | Unknown cost                 |

4.4 Worked example: a loom breaks at 11:20

Illustrative data for the demo mill (names are fictional). Weaving has three air-jet looms: WV-01, WV-02, WV-03.

| **Order** | **Buyer**       | **Situation at 11:00**                   | **Due** | **Forecast ship**     |
|-----------|-----------------|------------------------------------------|---------|-----------------------|
| ORD-104   | Kaveri Garments | 1,200 m blue poplin on WV-02, 500 m done | 14 Oct  | 13 Oct (1 day spare)  |
| ORD-107   | Deccan Linens   | 800 m grey poplin, queued next on WV-02  | 15 Oct  | 14 Oct (1 day spare)  |
| ORD-109   | Coastal Exports | 1,500 m white sheeting on WV-03          | 18 Oct  | 16 Oct (2 days spare) |
| ORD-102   | Kaveri Garments | Finishing on WV-01, free at 14:00        | 12 Oct  | 12 Oct                |

**11:20** — the WV-02 operator taps Breakdown → "warp break, motor fault", estimated repair six hours. Within a second the floor map pulses outward from WV-02 and the Ripple Card appears:

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<tbody>
<tr class="odd">
<td><p><strong>Ripple Card — WV-02 breakdown</strong></p>
<p><strong>ORD-104</strong> Kaveri Garments: ship moves 13 Oct → 14 Oct evening. <strong>Now late.</strong></p>
<p><strong>ORD-107</strong> Deccan Linens: ship moves 14 Oct → 16 Oct. <strong>Late by 1 day</strong> (contract penalty ₹5,000 per day).</p>
<p>ORD-109: not affected.</p>
<p><strong>At risk: ₹7,700</strong> = WV-02 idle 6 h × ₹450 (₹2,700) + ORD-107 late penalty (₹5,000), plus buyer goodwill.</p></td>
</tr>
</tbody>
</table>

| **Rank** | **Fix (each simulated)**                                                                                      | **Orders on time** | **Extra cost**           | **Why**                                                         |
|----------|---------------------------------------------------------------------------------------------------------------|--------------------|--------------------------|-----------------------------------------------------------------|
| **1**    | Move ORD-104's remaining 700 m to WV-01 at 14:00 + one overtime night shift on WV-02 after repair for ORD-107 | **3 of 3**         | ₹1,200 overtime          | WV-01 runs the same fabric; one overtime shift recovers ORD-107 |
| 2        | Move ORD-104 to WV-01 and split ORD-107 between WV-01 and WV-03                                               | 3 of 3             | ₹1,800 (two changeovers) | Works, but costs more and cuts ORD-109's spare time to 1.5 days |
| 3        | Move ORD-104 to WV-01 only                                                                                    | 2 of 3             | ₹0                       | ORD-107 still ships one day late                                |

**11:21** — the manager taps Fix 1. The WV-01 operator's phone shows "Next: ORD-104, 700 m, from 14:00". The night-shift operator gets an overtime request. Both orders turn green. No buyer is messaged, because no promised date changed. The Leak Meter records the real cost of the breakdown: **₹3,900** (₹2,700 idle + ₹1,200 overtime) instead of **₹7,700**.

Today this would have been discovered when Deccan Linens called on 15 October.

4.5 Promise Date in action

A new enquiry arrives: Kaveri Garments wants 2,000 m of navy twill by 20 October. The salesperson enters it as a draft. Ripple places it into the forecast without saving anything and replies:

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<tbody>
<tr class="odd">
<td><p><strong>Promise Date — draft order</strong></p>
<p>Earliest realistic ship date: <strong>22 Oct</strong>.</p>
<p>Limiting factor: navy 2/40s yarn short by 180 kg. If the purchase arrives by 13 Oct, <strong>20 Oct is possible</strong>.</p>
<p>If prioritised ahead of ORD-109, the order makes 20 Oct but ORD-109 loses one of its two spare days (still on time).</p>
<p>Suggested quote: "22 Oct confirmed; 20 Oct if we confirm yarn by Monday."</p></td>
</tr>
</tbody>
</table>

The mill stops promising dates it cannot keep — the starting point of most delays.

4.6 The Leak Meter

A live counter on the owner's screen that answers a question no register can: how much money is the mill losing today, and where?

| **Today's leak**                 | **Amount**  | **Source**                                                 |
|----------------------------------|-------------|------------------------------------------------------------|
| Idle machines (14 machine-hours) | ₹6,300      | Machine states × idle rate                                 |
| Rework (3 rolls)                 | ₹4,850      | QC decisions × rework cost                                 |
| Yarn waste above normal          | ₹2,000      | Logged waste vs expected for the fabric                    |
| Overtime                         | ₹1,200      | Approved overtime shifts                                   |
| **Total leaked today**           | **₹14,350** | Tap any line to see the machines, rolls and jobs behind it |

Every line is a lever. Over a month, the Leak Meter turns "nobody knows the real cost" into a ranked list of where profit is escaping.

4.7 What-if mode and the floor view

Two features from the original plan become parts of Ripple instead of separate builds:

- **The disruption simulator becomes Ripple's what-if mode.** The same engine that reacts to real events can be asked hypothetical questions: "What if WV-03 is down tomorrow?", "What if we accept this 3,000 m rush order?", "What if the yarn truck is two days late?" Nothing is saved until the manager applies a plan.

- **The factory view becomes the Ripple Floor.** A 2D floor map of departments and machines, colour-coded by state, where a ripple visibly spreads from a broken machine to the orders it affects. A 3D version is a stretch goal on the same data; the 2D map is the primary view because it is faster, clearer and works on any phone.

4.8 What Ripple does not claim

- It is not artificial intelligence. It is a transparent, rules-based engine; every result can be explained step by step. That is a strength in a factory.

- Forecasts are estimates. They improve as operators log real metres, and they show a confidence range ("16 Oct ± 4 h").

- Rupee figures use rates the owner sets. They are management estimates, not audited accounts.

- Ripple never controls a machine. It only changes the plan, after a person approves.

5\. Supporting differentiators

Four smaller ideas around Core and Ripple make LoomLink practical for the people at Everest and memorable for judges. Each one maps to a specific line in the brief.

5.1 Bol — speak in your own language

"Bol" means "speak". Operators and storekeepers can talk to LoomLink instead of typing. The phone turns the sentence into a structured entry and shows a confirmation card with big Yes / Edit buttons. Nothing is saved until the person confirms.

| **Worker says**                                       | **LoomLink understands**                           | **Result**                               |
|-------------------------------------------------------|----------------------------------------------------|------------------------------------------|
| "Loom chaar band ho gaya, belt toot gaya" (Hindi)     | Machine WV-04 · breakdown · reason: belt           | Breakdown recorded → Ripple fires        |
| "Loom naalugu aagipoyindi" (Telugu)                   | Machine WV-04 · stopped · reason needed            | Asks for the reason with picture buttons |
| "Two hundred metres done on ORD-104"                  | Job ORD-104 · +200 m                               | Progress and forecast updated            |
| "40 kilo blue cotton from Vel Spinners for order 112" | Receipt · 40 kg · blue cotton · supplier · ORD-112 | Batch created, QR ready to print         |

It replaces the notebook for people who will never fill in a form, which is the difference between a system that is installed and a system that is used.

5.2 Buyer Line — no more callbacks

The brief says the factory should tell a buyer where their order stands "without anyone having to go and look". LoomLink does it in three ways, from simplest to richest:

- **Office lookup:** type or scan an order ID and get the full status in one second — the answer to every phone call.

- **Tracking link:** each order has a private link the buyer can open any time: stage, metres ready, rolls passed, promised date, shipments.

- **WhatsApp reply:** the buyer messages the order number and gets the same status back automatically. When Ripple changes a promised date, the buyer gets one short message with the new date and the reason.

Buyers never see internal costs, workers or machine details.

5.3 Roll Passport — every roll tells its own story

Scan any roll and see its full life and its true cost. This answers the brief's headline problem in one screen.

| **ROLL-104-07** | **98 m · blue cotton poplin · Kaveri Garments, ORD-104**                                                              |
|-----------------|-----------------------------------------------------------------------------------------------------------------------|
| Yarn            | Batch YB-2610-03, Vel Spinners, received 2 Oct, 14 kg used                                                            |
| Weaving         | WV-01, operator Ravi, 10 Oct, shift A                                                                                 |
| Dyeing          | DY-02, dye lot DL-55, 11 Oct                                                                                          |
| Quality         | Passed 12 Oct, one minor defect logged at 41 m                                                                        |
| Cost            | Yarn ₹6,860 + weaving ₹1,170 + dyeing ₹1,470 + QC & packing ₹180 + overhead share ₹520 = **₹10,200** (₹104 per metre) |
| Price & margin  | 98 m × ₹125 = ₹12,250 → **margin ₹2,050 (16.7%)**                                                                     |

A buyer-safe version of the passport (origin, process and quality, without costs) can be shared with the buyer. This is also a step towards export traceability requirements, such as the digital product passports the European Union plans for textiles.

5.4 Owner's Daily Brief and Month Close

- **Morning brief (one screen, or one message):** yesterday's metres by machine, orders at risk, today's dispatches, yarn to buy, yesterday's leak, cash received.

- **Month close (one screen):** revenue invoiced, cash received, yarn cost, wages paid, other costs, **profit for the month** — with every figure drillable to orders, rolls, machines and workers. This is the exact question in the brief's final scene: "did the mill make money this month?"

5.5 Defect Detective

Because every roll is traced, defects can be grouped by machine, operator, shift and yarn batch. LoomLink highlights patterns automatically: "WV-03: 6 of the last 10 rolls had uneven weave — three times the mill average. Check the loom." or "Colour mismatch appears only in rolls from yarn batch YB-2609-11." This turns the brief's "a defect can be tracked to its cause" from a lookup into an alert.

6\. A day at Everest — before and after

| **Scene**              | **Today**                                           | **With LoomLink Core**                                                        | **What Ripple adds**                                                                                |
|------------------------|-----------------------------------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| Yarn arrives           | Written in a notebook; nobody sure what is in store | Batch received, linked to order, QR printed, stock updated; low-stock warning | Shows which future jobs this yarn unblocks or which shortage remains, and by when it must be bought |
| New order              | Owner guesses a date                                | Yarn check: enough or "to buy" list                                           | Promise Date from real stock, queues and speeds                                                     |
| Production floor       | Supervisor walks the floor                          | Live floor map, progress in metres, output today, shift handover              | Order Health on every order; Idle Hunter matches idle machines to at-risk work                      |
| Breakdown              | Discovered late; impact never calculated            | Breakdown recorded with reason                                                | Ripple Card: affected orders, ₹ at risk, three simulated fixes, one tap                             |
| Checking fabric        | Paper slip                                          | Roll QR, pass / rework / reject, full history                                 | Rework added to the forecast automatically; Defect Detective flags the cause                        |
| Buyer calls            | Walk, ask, call back later                          | Instant status by order ID; tracking link                                     | Honest ship date; buyer told automatically only when it changes                                     |
| Loading the truck      | Counted by hand                                     | Scan-verified dispatch, wrong / rejected / duplicate rolls blocked, invoice   | Dispatch updates promised dates and finished-stock forecast                                         |
| Owner closes the books | Separate registers, guesswork                       | Month profit on one screen; cost per order and per roll; wages                | Leak Meter shows where profit escaped and why                                                       |

6.1 Requirement coverage matrix

Every requirement sentence in the brief, mapped to the feature that meets it and the moment it is shown in the demo.

| **Brief requirement**                                           | **Feature**                                                | **Demo moment**         |
|-----------------------------------------------------------------|------------------------------------------------------------|-------------------------|
| Note quantity, type, colour and which order yarn is for         | Batch receipt with order link + QR                         | Scene 1                 |
| Always know raw material stock                                  | Stock ledger: on hand / reserved / available               | Scene 1                 |
| Warning before it runs low                                      | Reorder levels + low-stock alert                           | Scene 1                 |
| See if there is enough yarn for a new order, or what to order   | Yarn check + "to buy" list + Promise Date                  | Scene 1                 |
| Which order is on which machine                                 | Live floor map + machine QR                                | Scene 2                 |
| How far along it is                                             | Progress in metres, done vs target                         | Scene 2                 |
| Which machines are idle                                         | Machine states + Idle Hunter                               | Scene 2                 |
| Breakdowns, shift changes, workers moving                       | Breakdown reporting, shift handover, Ripple                | Scene 2 + Ripple moment |
| Fabric produced today per machine                               | Output today per machine and shift                         | Scene 2                 |
| Record pass / rework / reject                                   | Roll QC                                                    | Scene 3                 |
| Every roll traceable to order and machine                       | Roll history / Roll Passport                               | Scenes 3 and 6          |
| Defect tracked to its cause                                     | Defect Detective                                           | Scene 3                 |
| Record of passed, failed, waiting                               | QC queues                                                  | Scene 3                 |
| Tell a buyer exactly where the order stands, any time           | Order lookup, tracking link, WhatsApp reply                | Scene 4                 |
| Right rolls, right quantity, right buyer, matching invoice      | Scan-verified dispatch + invoice from scans                | Scene 5                 |
| Finished fabric on the shelf and what has gone out              | Finished-stock view + dispatch history                     | Scene 5                 |
| Nothing dispatched twice or forgotten                           | Duplicate block + aged-stock alert                         | Scene 5                 |
| Cost of each order                                              | Order cost sheet                                           | Scene 6                 |
| How much every machine produced                                 | Machine output report                                      | Scene 6                 |
| Worker wages paid                                               | Attendance + wage calculation                              | Scene 6                 |
| Bills, wages and buyer payments in one place; did we make money | Month Close screen                                         | Scene 6                 |
| Real cost of a single roll (problem statement)                  | Roll Passport cost breakdown                               | Closing moment          |
| Orders delayed, machines idle (problem statement)               | Ripple: Promise Date, Ripple Card, Idle Hunter, Leak Meter | Ripple moment           |

7\. How it is built

7.1 Architecture

| **Part**                            | **Role**                                                                                                                           |
|-------------------------------------|------------------------------------------------------------------------------------------------------------------------------------|
| **Phone web app** (React)           | Worker screens: scan, start, log, hand over, breakdown, QC, dispatch, Bol voice entry. Works in the phone browser; no app install. |
| **Manager & owner web app** (React) | Ripple Floor map, Ripple Cards, orders and health, stock, Leak Meter, Month Close, Roll Passport                                   |
| **Backend** (FastAPI, Python)       | Business rules, QR resolution, logins and roles, the stock ledger, all seven modules                                               |
| **Ripple engine** (Python module)   | Forecast, ripple comparison, rupee lens, fix finder, what-if mode                                                                  |
| **Database** (PostgreSQL)           | Single source of truth for everything                                                                                              |
| **Live updates** (WebSockets)       | Pushes changes to every open screen instantly                                                                                      |
| **Buyer Line**                      | Tracking pages; WhatsApp through a messaging API (sandbox in the hackathon)                                                        |
| **QR labels**                       | Generated as printable labels with the readable ID underneath                                                                      |
| **Machine adapter** (optional)      | Simulator now; real controller connection later                                                                                    |

7.2 The Ripple engine, step by step

| **Step**          | **What happens**                                                                                                                                                                                                                               |
|-------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1\. Read the mill | Machines (stage, state, free time, speed per fabric), jobs (stage, remaining metres, order of operations), yarn (available now and expected), shifts, due dates                                                                                |
| 2\. Learn speeds  | Each machine's metres per hour per fabric is the running average of what operators actually logged; the spread gives the confidence range                                                                                                      |
| 3\. Play forward  | For each stage in order, each machine takes its queued jobs by priority. A job starts at the latest of: machine free, previous stage done, yarn available, shift open. Duration = remaining metres ÷ speed. QC and dispatch buffers are added. |
| 4\. Compare       | Predicted ship date per order vs due date (health) and vs the previous forecast (the ripple)                                                                                                                                                   |
| 5\. Price         | Idle hours × idle rate + days late × penalty + overtime + rework                                                                                                                                                                               |
| 6\. Find fixes    | Generate candidate moves (reassign, overtime, split, swap, expedite yarn); replay the forecast for each; rank by orders on time, then cost, then number of changes                                                                             |
| 7\. Apply         | On approval, re-check that the mill has not changed, apply job moves in one transaction, notify phones and, if dates moved, buyers                                                                                                             |

For a mill of this size — tens of machines and a few hundred open jobs — one forecast takes milliseconds, so Ripple can test dozens of fixes and still answer in under a second.

7.3 Main data

| **Area**           | **Main records**                                                              |
|--------------------|-------------------------------------------------------------------------------|
| People             | Users, roles, workers, shifts, attendance, wage rules                         |
| Material           | Suppliers, yarn types, batches, stock movements, reservations, purchase needs |
| Sales              | Buyers, orders, fabric specifications, routes, promised dates                 |
| Production         | Machines, speeds, jobs, progress logs, handovers, breakdowns, WIP tags        |
| Quality & dispatch | Rolls, inspections, defects, shipments, invoices                              |
| Money              | Supplier bills, buyer payments, cost rates, payroll                           |
| Ripple             | Forecast snapshots, ripple events, fix options, applied fixes, leak entries   |

7.4 Technology

| **Layer**   | **Choice**                                                                                | **Why**                                                    |
|-------------|-------------------------------------------------------------------------------------------|------------------------------------------------------------|
| Frontend    | React + TypeScript, Tailwind, html5-qrcode                                                | Fast to build; phone camera scanning in the browser        |
| Floor map   | SVG / Canvas (2D); React Three Fiber only for the 3D stretch                              | Clear on any phone; the ripple animation is simple to draw |
| Backend     | FastAPI + Pydantic                                                                        | Quick, typed, Python — the same language as Ripple         |
| Database    | PostgreSQL + SQLAlchemy                                                                   | Reliable transactions for stock and money                  |
| Voice (Bol) | Browser speech recognition + a language model or keyword parser to structure the sentence | Works in the browser; supports Indian languages            |
| Messaging   | WhatsApp Business API sandbox (or simulated chat for the demo)                            | Shows the real buyer experience                            |
| Deploy      | Docker Compose; runs on one local PC on the mill network or in the cloud                  | Works without depending on internet at the mill            |

8\. Hackathon execution plan

8.1 Scope in three tiers

<table>
<colgroup>
<col style="width: 21%" />
<col style="width: 52%" />
<col style="width: 25%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>Tier</strong></th>
<th><strong>What</strong></th>
<th><strong>Rule</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><strong>Must</strong> (the winning core)</td>
<td><p>Full QR loop: receive → order → issue → scan-start → log → finish → roll → QC → dispatch → invoice</p>
<p>Attendance, wages, Month Close, cost per roll</p>
<p>Ripple: forecast, Ripple Card with fixes, Order Health, Promise Date</p>
<p>Ripple Floor (2D)</p></td>
<td>Nothing else starts until this works end to end with demo data</td>
</tr>
<tr class="even">
<td><strong>Should</strong> (the memorable layer)</td>
<td><p>Leak Meter</p>
<p>Roll Passport screen</p>
<p>Buyer tracking link</p>
<p>Bol voice entry (one language + English)</p>
<p>Idle Hunter alert</p></td>
<td>Add in this order</td>
</tr>
<tr class="odd">
<td><strong>Could</strong> (stretch)</td>
<td><p>Live WhatsApp reply</p>
<p>Defect Detective patterns</p>
<p>What-if mode screen</p>
<p>3D floor view</p>
<p>Machine-signal simulator</p></td>
<td>Only if Must and Should are rehearsed</td>
</tr>
</tbody>
</table>

8.2 Team of four

| **Member**              | **Owns**                                                                                                                  |
|-------------------------|---------------------------------------------------------------------------------------------------------------------------|
| A — Backend core        | Database, stock ledger, orders, jobs, QC, dispatch, wages, money APIs, seed data                                          |
| B — Ripple engine       | Forecast, ripple comparison, rupee lens, fix finder, Promise Date, Ripple APIs                                            |
| C — Worker app          | Phone screens: scan flows, progress, handover, breakdown, QC, dispatch, Bol voice, buyer tracking page                    |
| D — Manager app + pitch | Ripple Floor map and animation, Ripple Card, order health, Leak Meter, Month Close, Roll Passport, demo script and slides |

8.3 Timeline (36 hours; compress or stretch proportionally)

| **Hours** | **Milestone**                                                                  | **Done when**                                                |
|-----------|--------------------------------------------------------------------------------|--------------------------------------------------------------|
| 0–2       | Agree data model, seed mill, repo, screen list                                 | Everyone builds against the same API contract                |
| 2–10      | Core: batches + QR, stock, orders, machines, jobs, scan screens                | A job can be started by scanning a printed QR                |
| 10–16     | Rolls, QC, dispatch, invoice, attendance, wages, Month Close                   | One order runs from yarn to invoice                          |
| 16–24     | Ripple engine: forecast, ripple, rupees, fixes, Promise Date                   | Breaking WV-02 in seed data produces the worked example      |
| 24–30     | Ripple Floor, Ripple Card, Order Health, Leak Meter, Roll Passport, buyer link | The signature moment works on screen                         |
| 30–33     | Bol voice, language labels, polish                                             | Breakdown can be spoken in Hindi or Telugu                   |
| 33–36     | Demo reset script, three full rehearsals, backup video                         | Demo runs in under 7 minutes, twice in a row, without errors |

8.4 Demo mill (seed data)

- 3 stages: weaving (WV-01 to WV-03), dyeing (DY-01, DY-02), finishing (FN-01); QC table; store.

- 4 fictional buyers, 6 open orders with realistic due dates and penalties, 5 yarn batches, 12 workers on 2 shifts.

- 2 weeks of fake history so machine speeds, leak figures and defect patterns look real.

- A one-command reset that returns the mill to 11:00 on demo day, so the Ripple moment is identical every time.

- Printed QR labels for two yarn batches, two machines and three rolls to scan live in front of the judges.

9\. The 7-minute demo

The demo follows the brief's own "A Day at the Mill", so judges can tick off the problem statement as they watch. The Ripple moment sits in the middle as the peak.

| **Time** | **Scene**              | **What the judges see**                                                                                                                                                                        |
|----------|------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 0:00     | **Hook**               | Hold up a printed roll label: "Everest's owner asked what this roll cost him. Nobody could answer. In seven minutes, he will scan it."                                                         |
| 0:30     | Yarn arrives           | Receive 40 kg of blue cotton for ORD-112; label prints; low-stock warning clears. Enter a new enquiry → Promise Date: "22 Oct; 20 Oct if yarn confirmed"                                       |
| 1:30     | Production floor       | Operator scans WV-01 on a real phone, starts the job, says "two hundred metres done" in Telugu; the floor map and progress bar update live                                                     |
| 2:30     | **Ripple moment**      | Operator taps Breakdown on WV-02. The ripple spreads; two orders turn red; Ripple Card: "₹7,700 at risk", three fixes. Tap Fix 1 → orders turn green, WV-01 operator's phone shows the new job |
| 4:00     | Checking fabric        | Scan two rolls: one passes, one goes to rework. Defect Detective flags WV-03's uneven-weave pattern                                                                                            |
| 4:45     | Buyer calls            | Open the buyer tracking link (or send "ORD-104" on WhatsApp): live stage, metres ready, ship date — no one walked anywhere                                                                     |
| 5:15     | Loading the truck      | Scan rolls onto the truck; the rework roll is blocked; a double scan is blocked; invoice appears                                                                                               |
| 6:00     | Owner closes the books | Month Close: profit for the month. Leak Meter: where money escaped today. Scan the roll from the hook → Roll Passport: cost ₹10,200, margin 16.7%                                              |
| 6:45     | **Close**              | "Every other system tells Everest what happened. LoomLink tells them what it means — and what to do next."                                                                                     |

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<tbody>
<tr class="odd">
<td><p><strong>Demo rules</strong></p>
<p>Use real phones and printed labels — physical scanning is far more convincing than a mouse click.</p>
<p>Reset the mill before every run; never improvise data on stage.</p>
<p>Keep a recorded backup of the full demo in case the network fails.</p>
<p>Say "simulated" whenever anything is simulated. Judges reward honesty.</p></td>
</tr>
</tbody>
</table>

10\. Questions judges will ask

| **Question**                                       | **Answer**                                                                                                                                                                                                                        |
|----------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Isn't this just a dashboard?                       | A dashboard shows the present. Ripple computes the consequences of every event and simulates the fixes. The Ripple Card is a decision, not a display.                                                                             |
| How accurate is the forecast?                      | It uses each machine's real speeds learned from operator logs and shows a confidence range. Even when the exact hour is off, it reliably shows which orders are at risk and which fix is better — that is what the manager needs. |
| Where does machine data come from without sensors? | From operators' scans and progress logs on their phones. Machine signals can be plugged in later through the adapter; the system does not depend on them.                                                                         |
| Will workers actually use it?                      | Each action is one scan and at most three taps, with large buttons, and workers can simply speak in Telugu, Tamil, Hindi or English. Workers only see their own jobs.                                                             |
| Is it AI?                                          | Ripple is deliberately rules-based and explainable — a manager can see exactly why a fix was suggested. Language models are used only where they help, such as turning a spoken sentence into an entry.                           |
| What if the internet goes down?                    | LoomLink can run on a single PC on the mill's own network; phones connect over the mill Wi-Fi. Offline queuing on the phone is on the roadmap.                                                                                    |
| How is the cost of a roll calculated?              | Yarn by the actual batch cost and kilograms used; labour from logged job time and wage rates; machine time at a set hourly rate; overhead shared by a rule the owner sets. Every line can be opened.                              |
| Why QR and not RFID or sensors?                    | QR needs only phones and printed labels — affordable for a small mill on day one. RFID and sensors fit in later without changing the data model.                                                                                  |
| How does it scale?                                 | The forecast for a mill of this size runs in milliseconds. Larger plants can split the forecast by department; the core is a standard web app and database.                                                                       |
| What stops mistakes and fraud?                     | Logins and roles on every action, a stock ledger that cannot go negative, corrections as new entries rather than edits, and a full audit trail.                                                                                   |

11\. Expected impact

Targets the system is designed to achieve; to be measured in a pilot, not claimed as results.

| **Measure**                                         | **Today**                     | **With LoomLink**                                       |
|-----------------------------------------------------|-------------------------------|---------------------------------------------------------|
| Time to answer a buyer                              | Hours (walk, ask, call back)  | Seconds — or the buyer checks the link                  |
| Time to notice a breakdown's impact on deliveries   | Days (when a buyer complains) | About one second (Ripple Card)                          |
| Time to know a machine is idle                      | Next floor walk               | Instant, with a suggested job                           |
| Delivery dates quoted                               | Guessed                       | Computed from stock, queues and speeds                  |
| Cost of a single roll                               | Unknown                       | Itemised to the rupee on scan                           |
| Daily money lost to idle time, rework and waste     | Invisible                     | Live on the Leak Meter                                  |
| Defect cause                                        | Rarely found                  | Traced to machine, shift and batch, with pattern alerts |
| Phone calls and notebook entries for routine status | Dozens a day                  | Close to none                                           |

12\. After the hackathon

| **Next step**           | **Value**                                                                                       |
|-------------------------|-------------------------------------------------------------------------------------------------|
| Machine-signal adapters | Automatic progress and completion where machines support it, with the operator still confirming |
| Defect photos           | Inspector photographs a defect; a vision model suggests the defect type                         |
| Paper bridge            | Photograph an old register or slip to import it — eases the switch from notebooks               |
| Smarter forecasting     | Learn breakdown patterns and seasonal speeds from history to tighten Ripple's confidence        |
| Export passports        | Buyer-facing Roll Passports aligned with textile traceability rules in export markets           |
| 3D floor view           | Explorable 3D view on the same live data for large plants and visitors                          |
| Multi-mill              | One owner, several units, with Ripple moving work between them                                  |

13\. Final pitch

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<tbody>
<tr class="odd">
<td><p><strong>LoomLink</strong> replaces Everest Textile Mills' notebooks, paper slips, registers and phone calls with one system built around QR identities for every yarn batch, machine and fabric roll. Workers scan or simply speak in their own language; stock, production, quality, dispatch, wages and money live in one trusted record, and every roll carries its full history and its true cost.</p>
<p>On top of that record runs <strong>Ripple</strong>, a live consequence engine. It keeps a forecast of the whole mill and recomputes it the moment anything changes. Every breakdown, shortage, rejected roll or rush order becomes a Ripple: the orders it affects, the rupees at stake and three tested fixes, applied with one tap. Sales quotes dates the mill can keep, idle machines are matched to work that needs them, buyers are told before they need to call, and the owner sees every day where profit is leaking.</p>
<p>The brief says orders get delayed, machines sit idle and nobody knows the real cost of a roll. LoomLink fixes all three — with phones and printed labels.</p></td>
</tr>
</tbody>
</table>
