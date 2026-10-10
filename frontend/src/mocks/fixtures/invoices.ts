import type { Invoice } from "./types";

// ORD-101: 1800 m × ₹160/m = ₹2,88,000 → 28800000 paise. Nilgiri 60-day terms.
// ORD-103: 1000 m × ₹125/m = ₹1,25,000 → 12500000 paise. Kaveri 30-day terms. Half paid.
// ORD-105: 1500 m × ₹98/m  = ₹1,47,000 → 14700000 paise. Coastal 30-day terms. Unpaid.
// ORD-106:  600 m × ₹98/m  = ₹58,800  →  5880000 paise. Deccan — overdue (short-agreed terms).
export const invoices: Invoice[] = [
  {
    id: "inv-101",
    order_id: "ord-101",
    buyer_id: "buy-004",
    dispatch_id: "disp-101",
    amount_paise: 28800000,
    paid_paise: 28800000,
    status: "paid",
    issued_date: "2026-10-01",
    due_date: "2026-11-30",
  },
  {
    id: "inv-103",
    order_id: "ord-103",
    buyer_id: "buy-001",
    dispatch_id: "disp-103",
    amount_paise: 12500000,
    paid_paise: 6250000,
    status: "partial",
    issued_date: "2026-10-05",
    due_date: "2026-11-04",
  },
  {
    id: "inv-105",
    order_id: "ord-105",
    buyer_id: "buy-003",
    dispatch_id: "disp-105",
    amount_paise: 14700000,
    paid_paise: 0,
    status: "unpaid",
    issued_date: "2026-10-07",
    due_date: "2026-11-06",
  },
  {
    // Short agreed payment terms; overdue at D 11:00 to demonstrate receivables ageing
    id: "inv-106",
    order_id: "ord-106",
    buyer_id: "buy-002",
    dispatch_id: "disp-106",
    amount_paise: 5880000,
    paid_paise: 0,
    status: "overdue",
    issued_date: "2026-09-28",
    due_date: "2026-10-08",
  },
];
