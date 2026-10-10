# Problem Statement (verbatim from the hackathon brief)

```
Textile Manufacturing System
Build one system to replace notebooks and phone calls.




1) The Challenge
Your task is to build one unified software platform that solves the real, day-to-day
problems of a textile manufacturing unit. Think of it as the digital backbone of a busy
fabric factory. Read the scenes that follow as things that actually happen on an ordinary
day, and design the system that makes each of them easy.




2) Meet Everest Textile Mills
Everest Textile Mills buys yarn, turns it into fabric on spinning, weaving and dyeing
machines, checks the fabric for defects, and sells the finished rolls to buyers. Orders
come in from many buyers at once, each with its own fabric type, colour, quantity and
deadline. The factory runs in shifts, with workers on the floor, a store for raw material
and finished goods, and an office that deals with buyers, suppliers and accounts.


How Things Run Today

   ● Raw material stock: Tracked in a notebook

   ● Machine and order status: Checked by walking the floor

   ● Quality checks: Recorded on paper slips

   ● Order updates for buyers: Given over phone calls

   ● Worker attendance and wages: Marked in a register
Orders get delayed, machines sit idle, and nobody knows the real cost of a single roll of
fabric.




3) A Day at the Mill
The scenes below follow one day at Everest Textile Mills, from yarn arriving at the gate to
the owner closing the books at month-end. Every one of them is a problem someone at
the mill faces today.



Yarn arrives at the gate
A truck brings in yarn from a supplier. Someone has to note down how much came in,
what type and colour it is, and which order it is for, before it goes into the store.

The factory should always know how much raw material it has, and get a warning
before it runs low. When a new order comes in, it should be easy to see whether there is
enough yarn to start it, or whether more needs to be ordered first.



The production floor, mid-shift
Yarn moves through spinning, weaving and dyeing before it becomes finished fabric. At
any moment, someone should be able to say which order is on which machine, how far
along it is, and which machines are sitting idle.

Machines break down, shifts change, and workers move between jobs. The factory needs
a simple way to see what every machine is doing right now, and how much fabric it has
produced today.



Checking the fabric before it leaves the line
Before fabric is packed, someone checks it for defects such as holes, colour mismatch
or uneven weaving. Some rolls pass, some need rework, and a few are rejected.
Every roll should be traceable back to the order and the machine it came from, so a
defect can be tracked to its cause. The factory needs a clear record of what passed,
what failed, and what is waiting to be checked.



A buyer calls asking about their order
A buyer wants to know if their fabric is ready and when it will be delivered. Today,
someone has to walk to the floor, ask around, and call back later with an answer.

The factory should be able to tell a buyer, at any time, exactly where their order stands:
whether it is still being woven, being checked, or ready to ship, without anyone having to
go and look.



Loading the truck for dispatch
Finished rolls are packed, counted and loaded onto a truck for delivery. Someone needs
to make sure the right rolls, in the right quantity, go to the right buyer, with an invoice
that matches.

The store should always show how much finished fabric is sitting on the shelf, and what
has already gone out, so nothing is dispatched twice or forgotten in a corner.



The owner, closing the books
At the end of the month, the owner wants to know what it actually cost to make each
order, how much every machine produced, and how much was paid out in worker
wages.

Raw material bills, worker wages, and payments from buyers all need to come together
in one place, so the owner can see, clearly and quickly, whether the mill made money
this month.
```

## "What exactly should you build?" (official module table from the organisers)

| Module | What it should do |
|---|---|
| Raw Material Inventory | Track yarn quantity, type, colour, suppliers and low-stock alerts |
| Production Management | Track which order is assigned to which machine, production progress and machine availability |
| Quality Control | Inspect fabric rolls, record defects and classify them as passed, rework or rejected |
| Order Management | Manage buyer orders, fabric specifications, quantities, deadlines and production status |
| Dispatch Management | Track finished fabric, deliveries, quantities and invoices |
| Worker Management | Track worker attendance, shifts and wages |
| Financial Management | Track raw material costs, wages, customer payments and profitability |

Every one of these seven modules must be fully working end to end. Judges will tick them off.
