import type { Supplier } from "./types";

export const suppliers: Supplier[] = [
  {
    id: "sup-001",
    code: "SUP-001",
    name: "Vel Spinners",
    payment_terms_days: 30,
    yarn_type_ids: ["yt-cot-40s-wht", "yt-cot-40s-blu"],
  },
  {
    id: "sup-002",
    code: "SUP-002",
    name: "Annapoorna Yarns",
    payment_terms_days: 45,
    yarn_type_ids: ["yt-pc-240s-gry", "yt-cot-30s-nvy"],
  },
  {
    id: "sup-003",
    code: "SUP-003",
    name: "Kongu Cotton Traders",
    payment_terms_days: 30,
    yarn_type_ids: ["yt-cot-40s-wht", "yt-cot-30s-nvy"],
  },
];
