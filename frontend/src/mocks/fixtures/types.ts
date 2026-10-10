// Replace with generated src/lib/api-types.ts once the backend is running: npm run gen:api

// ── Enums ──────────────────────────────────────────────────────────────────

export type Role =
  | "owner"
  | "manager"
  | "storekeeper"
  | "operator"
  | "qc_inspector"
  | "dispatch"
  | "accounts"
  | "buyer";

export type Language = "en" | "hi" | "te" | "ta";

export type Stage = "spinning" | "weaving" | "dyeing" | "finishing";

export type Unit = "kg" | "m" | "roll" | "piece";

export type MachineStatus = "idle" | "running" | "breakdown" | "maintenance";

export type JobStatus =
  | "queued"
  | "in_progress"
  | "paused"
  | "completed"
  | "cancelled";

export type OrderStatus =
  | "draft"
  | "confirmed"
  | "in_production"
  | "completed"
  | "dispatched"
  | "closed"
  | "cancelled";

export type OrderPriority = "low" | "normal" | "high" | "urgent";

export type RollStatus =
  | "pending_qc"
  | "passed"
  | "rework"
  | "rejected";

export type QcDecision = "pass" | "rework" | "reject";

export type DefectSeverity = "minor" | "major" | "critical";

export type DispatchStatus = "pending" | "dispatched" | "delivered";

export type InvoiceStatus = "unpaid" | "partial" | "paid" | "overdue";

export type MovementKind =
  | "receive"
  | "issue"
  | "return"
  | "adjust_in"
  | "adjust_out";

export type AttendanceStatus = "present" | "absent" | "half_day";

export type WageType = "daily" | "piece" | "hourly";

export type Health = "green" | "amber" | "red";

export type BatchStatus = "in_use" | "exhausted";

export type Shift = "A" | "B" | "C";

// ── Interfaces ─────────────────────────────────────────────────────────────

export interface Machine {
  id: string;
  code: string;
  name: string;
  stage: Stage;
  /** paise/hour */
  idle_cost_paise_per_hour: number;
  /** m/h for weaving/finishing/dyeing; kg/h for spinning */
  default_speed: number;
  speed_unit: "m/h" | "kg/h";
  status: MachineStatus;
  grid_x: number;
  grid_y: number;
}

export interface YarnType {
  id: string;
  code: string;
  name: string;
  /** grams */
  reorder_level_grams: number;
  /** paise/kg */
  std_rate_paise_per_kg: number;
}

export interface Supplier {
  id: string;
  code: string;
  name: string;
  /** days */
  payment_terms_days: number;
  yarn_type_ids: string[];
}

export interface FabricType {
  id: string;
  code: string;
  name: string;
  /** centimetres */
  width_cm: number;
  /** grams per square metre */
  gsm: number;
  yarn_type_id: string;
  /** grams per 100 m */
  yarn_per_100m_grams: number;
  /** paise/m */
  default_price_paise_per_m: number;
  route_template_id: string;
}

export interface Buyer {
  id: string;
  code: string;
  name: string;
  /** days */
  payment_terms_days: number;
  /** paise/day */
  late_penalty_paise_per_day: number;
  user_id: string | null;
}

export interface Worker {
  id: string;
  emp_code: string;
  name: string;
  skill_stages: Stage[];
  wage_type: WageType;
  /** paise/day OR paise/m OR paise/hour depending on wage_type */
  wage_rate_paise: number;
  default_shift: Shift;
  language: Language;
  user_id: string;
}

export interface User {
  id: string;
  email: string | null;
  phone: string | null;
  name: string;
  role: Role;
  language: Language;
}

export interface Order {
  id: string;
  code: string;
  buyer_id: string;
  fabric_type_id: string;
  /** centimetres */
  quantity_cm: number;
  /** paise/m */
  price_paise_per_m: number;
  status: OrderStatus;
  priority: OrderPriority;
  /** ISO 8601 date string */
  due_date: string;
  /** ISO 8601 datetime string */
  created_at: string;
  notes: string | null;
}

export interface Job {
  id: string;
  order_id: string;
  machine_id: string;
  stage: Stage;
  status: JobStatus;
  /** centimetres planned */
  planned_quantity_cm: number;
  /** centimetres actually completed */
  actual_quantity_cm: number;
  operator_id: string | null;
  /** ISO 8601 datetime */
  started_at: string | null;
  /** ISO 8601 datetime */
  completed_at: string | null;
  health: Health;
}

export interface YarnBatch {
  id: string;
  code: string;
  yarn_type_id: string;
  supplier_id: string;
  /** grams received */
  received_grams: number;
  /** grams remaining */
  remaining_grams: number;
  /** paise/kg on this batch */
  rate_paise_per_kg: number;
  /** ISO 8601 date */
  received_date: string;
  status: BatchStatus;
}

export interface Roll {
  id: string;
  code: string;
  order_id: string;
  job_id: string;
  /** centimetres */
  length_cm: number;
  status: RollStatus;
  qc_decision: QcDecision | null;
  defect_severity: DefectSeverity | null;
  defect_notes: string | null;
  /** ISO 8601 datetime */
  created_at: string;
  /** ISO 8601 datetime */
  inspected_at: string | null;
  self_inspected: boolean;
}

export interface Dispatch {
  id: string;
  order_id: string;
  roll_ids: string[];
  status: DispatchStatus;
  /** ISO 8601 datetime */
  dispatched_at: string | null;
  /** ISO 8601 datetime */
  delivered_at: string | null;
  tracking_ref: string | null;
}

export interface Invoice {
  id: string;
  order_id: string;
  buyer_id: string;
  dispatch_id: string;
  /** paise total */
  amount_paise: number;
  /** paise paid so far */
  paid_paise: number;
  status: InvoiceStatus;
  /** ISO 8601 date */
  due_date: string;
  /** ISO 8601 date */
  issued_date: string;
}

export interface StockLevel {
  yarn_type_id: string;
  /** grams on hand */
  on_hand_grams: number;
  /** grams reorder threshold */
  reorder_level_grams: number;
  below_reorder: boolean;
}

export interface StockMovement {
  id: string;
  yarn_type_id: string;
  batch_id: string | null;
  kind: MovementKind;
  /** grams (always positive; kind determines direction) */
  quantity_grams: number;
  order_id: string | null;
  actor_id: string;
  reason: string | null;
  /** ISO 8601 datetime */
  recorded_at: string;
}

export interface RouteTemplate {
  id: string;
  code: string;
  name: string;
  stages: Stage[];
}
