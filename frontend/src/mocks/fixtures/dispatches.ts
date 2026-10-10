import type { Dispatch } from "./types";

export const dispatches: Dispatch[] = [
  {
    id: "disp-101",
    order_id: "ord-101",
    roll_ids: [],   // history rolls not seeded individually
    status: "delivered",
    dispatched_at: "2026-10-01T06:00:00Z",
    delivered_at: "2026-10-02T10:00:00Z",
    tracking_ref: "TRK-101-ETM",
  },
  {
    id: "disp-103",
    order_id: "ord-103",
    roll_ids: [],
    status: "delivered",
    dispatched_at: "2026-10-05T07:00:00Z",
    delivered_at: "2026-10-06T11:00:00Z",
    tracking_ref: "TRK-103-ETM",
  },
  {
    id: "disp-105",
    order_id: "ord-105",
    roll_ids: [],
    status: "delivered",
    dispatched_at: "2026-10-07T08:00:00Z",
    delivered_at: "2026-10-08T12:00:00Z",
    tracking_ref: "TRK-105-ETM",
  },
  {
    id: "disp-106",
    order_id: "ord-106",
    roll_ids: [],
    status: "delivered",
    dispatched_at: "2026-09-28T09:00:00Z",
    delivered_at: "2026-09-29T13:00:00Z",
    tracking_ref: "TRK-106-ETM",
  },
];
