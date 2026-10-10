import type { Job } from "./types";

// Live job state at D 11:00 IST (2026-10-10T05:30:00Z)
export const jobs: Job[] = [
  // ORD-102: grey poplin on WV-01 (shift A started 06:00 IST = 00:30 UTC)
  {
    id: "job-102-wv",
    order_id: "ord-102",
    machine_id: "mach-wv-01",
    stage: "weaving",
    status: "in_progress",
    planned_quantity_cm: 90000,
    actual_quantity_cm: 20250,  // ~4.5 h × 45 m/h = 202.5 m
    operator_id: "wkr-emp-001",
    started_at: "2026-10-10T00:30:00Z",
    completed_at: null,
    health: "amber",
  },
  // ORD-102: earlier woven lot being dyed on DY-01
  {
    id: "job-102-dy",
    order_id: "ord-102",
    machine_id: "mach-dy-01",
    stage: "dyeing",
    status: "in_progress",
    planned_quantity_cm: 45000,
    actual_quantity_cm: 30000,
    operator_id: "wkr-emp-007",
    started_at: "2026-10-09T23:00:00Z",
    completed_at: null,
    health: "green",
  },
  // ORD-104: blue poplin on WV-02, 500 m done
  {
    id: "job-104-wv",
    order_id: "ord-104",
    machine_id: "mach-wv-02",
    stage: "weaving",
    status: "in_progress",
    planned_quantity_cm: 120000,
    actual_quantity_cm: 50000,
    operator_id: "wkr-emp-002",
    started_at: "2026-10-09T00:30:00Z",
    completed_at: null,
    health: "green",
  },
  // ORD-104: earlier rolls on FN-01 (finishing)
  {
    id: "job-104-fn",
    order_id: "ord-104",
    machine_id: "mach-fn-01",
    stage: "finishing",
    status: "in_progress",
    planned_quantity_cm: 45000,
    actual_quantity_cm: 27000,
    operator_id: "wkr-emp-009",
    started_at: "2026-10-10T01:00:00Z",
    completed_at: null,
    health: "green",
  },
  // ORD-109: white sheeting on WV-03
  {
    id: "job-109-wv",
    order_id: "ord-109",
    machine_id: "mach-wv-03",
    stage: "weaving",
    status: "in_progress",
    planned_quantity_cm: 150000,
    actual_quantity_cm: 18000,  // ~4.5 h × 40 m/h = 180 m
    operator_id: "wkr-emp-003",
    started_at: "2026-10-10T00:30:00Z",
    completed_at: null,
    health: "green",
  },
  // ORD-110: navy twill spinning on SP-01 (R2 route, first stage)
  {
    id: "job-110-sp",
    order_id: "ord-110",
    machine_id: "mach-sp-01",
    stage: "spinning",
    status: "in_progress",
    planned_quantity_cm: 100000,  // proxy for 275 kg yarn needed
    actual_quantity_cm: 54000,    // ~4.5 h × 12 kg/h → proportional progress
    operator_id: "wkr-emp-011",
    started_at: "2026-10-10T00:30:00Z",
    completed_at: null,
    health: "green",
  },
];
