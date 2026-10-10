from __future__ import annotations
import enum


class Role(str, enum.Enum):
    owner = "owner"
    manager = "manager"
    storekeeper = "storekeeper"
    operator = "operator"
    qc_inspector = "qc_inspector"
    dispatch = "dispatch"
    accounts = "accounts"
    buyer = "buyer"


class Language(str, enum.Enum):
    en = "en"
    hi = "hi"
    te = "te"
    ta = "ta"


class Stage(str, enum.Enum):
    spinning = "spinning"
    weaving = "weaving"
    dyeing = "dyeing"
    finishing = "finishing"


class Unit(str, enum.Enum):
    cm = "cm"
    g = "g"


class MachineStatus(str, enum.Enum):
    idle = "idle"
    running = "running"
    breakdown = "breakdown"
    maintenance = "maintenance"
    changeover = "changeover"
    offline = "offline"


class JobStatus(str, enum.Enum):
    planned = "planned"
    ready = "ready"
    queued = "queued"
    running = "running"
    paused = "paused"
    blocked = "blocked"
    done = "done"
    completed = "completed"
    cancelled = "cancelled"


class OrderStatus(str, enum.Enum):
    pending_approval = "pending_approval"
    draft = "draft"
    confirmed = "confirmed"
    in_production = "in_production"
    qc = "qc"
    ready = "ready"
    partly_dispatched = "partly_dispatched"
    dispatched = "dispatched"
    closed = "closed"
    cancelled = "cancelled"


class OrderPriority(str, enum.Enum):
    normal = "normal"
    high = "high"
    rush = "rush"


class RollStatus(str, enum.Enum):
    pending_qc = "pending_qc"
    passed = "passed"
    rework = "rework"
    rejected = "rejected"
    dispatched = "dispatched"


class QcDecision(str, enum.Enum):
    passed = "passed"
    rework = "rework"
    rejected = "rejected"


class DefectSeverity(str, enum.Enum):
    minor = "minor"
    major = "major"
    critical = "critical"


class DispatchStatus(str, enum.Enum):
    draft = "draft"
    loading = "loading"
    dispatched = "dispatched"
    in_transit = "in_transit"
    delivered = "delivered"
    cancelled = "cancelled"


class InvoiceStatus(str, enum.Enum):
    issued = "issued"
    partly_paid = "partly_paid"
    paid = "paid"
    cancelled = "cancelled"


class MovementKind(str, enum.Enum):
    receipt = "receipt"
    issue = "issue"
    return_ = "return"
    adjustment = "adjustment"
    scrap = "scrap"


class AttendanceStatus(str, enum.Enum):
    present = "present"
    absent = "absent"
    half_day = "half_day"
    leave = "leave"
    holiday = "holiday"


class WageType(str, enum.Enum):
    daily = "daily"
    hourly = "hourly"
    monthly = "monthly"
    piece = "piece"


class Health(str, enum.Enum):
    green = "green"
    amber = "amber"
    red = "red"


class PurchaseOrderStatus(str, enum.Enum):
    draft = "draft"
    sent = "sent"
    partly_received = "partly_received"
    received = "received"
    cancelled = "cancelled"


class YarnBatchStatus(str, enum.Enum):
    active = "active"
    depleted = "depleted"
    quarantined = "quarantined"


class StockReservationStatus(str, enum.Enum):
    active = "active"
    consumed = "consumed"
    released = "released"


class RippleTriggerKind(str, enum.Enum):
    breakdown = "breakdown"
    stock_short = "stock_short"
    qc_rework = "qc_rework"
    absence = "absence"
    rush_order = "rush_order"
    slip = "slip"
    manual = "manual"


class RippleStatus(str, enum.Enum):
    open = "open"
    resolved = "resolved"
    dismissed = "dismissed"


class LeakCategory(str, enum.Enum):
    idle = "idle"
    rework = "rework"
    waste = "waste"
    overtime = "overtime"
    late_penalty = "late_penalty"


class MessageChannel(str, enum.Enum):
    whatsapp = "whatsapp"
    simulator = "simulator"
    link = "link"


class MessageDirection(str, enum.Enum):
    inbound = "in"
    outbound = "out"


class MessageStatus(str, enum.Enum):
    queued = "queued"
    sent = "sent"
    failed = "failed"
    received = "received"


class AttendanceSource(str, enum.Enum):
    app = "app"
    badge = "badge"
    supervisor = "supervisor"


class MachineEventKind(str, enum.Enum):
    start = "start"
    progress = "progress"
    pause = "pause"
    resume = "resume"
    breakdown = "breakdown"
    repaired = "repaired"
    finish = "finish"
    maintenance_start = "maintenance_start"
    maintenance_end = "maintenance_end"
    changeover_start = "changeover_start"
    changeover_end = "changeover_end"


class MachineEventSource(str, enum.Enum):
    app = "app"
    voice = "voice"
    simulator = "simulator"


class ProgressSource(str, enum.Enum):
    tap = "tap"
    voice = "voice"
    machine = "machine"


class JobEndReason(str, enum.Enum):
    handover = "handover"
    finish = "finish"
    pause = "pause"
    breakdown = "breakdown"
    shift_end = "shift_end"