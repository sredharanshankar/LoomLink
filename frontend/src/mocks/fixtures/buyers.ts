import type { Buyer } from "./types";

export const buyers: Buyer[] = [
  {
    id: "buy-001",
    code: "BUY-001",
    name: "Kaveri Garments",
    payment_terms_days: 30,
    late_penalty_paise_per_day: 300000,
    user_id: "user-buyer-kaveri",
  },
  {
    id: "buy-002",
    code: "BUY-002",
    name: "Deccan Linens",
    payment_terms_days: 45,
    late_penalty_paise_per_day: 500000,
    user_id: null,
  },
  {
    id: "buy-003",
    code: "BUY-003",
    name: "Coastal Exports",
    payment_terms_days: 30,
    late_penalty_paise_per_day: 400000,
    user_id: null,
  },
  {
    id: "buy-004",
    code: "BUY-004",
    name: "Nilgiri Home Textiles",
    payment_terms_days: 60,
    late_penalty_paise_per_day: 200000,
    user_id: null,
  },
];
