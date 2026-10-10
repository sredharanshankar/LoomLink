from __future__ import annotations

import datetime as dt
from collections import defaultdict
from statistics import median
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.time import now
from app.models.identity import MillSettings
from app.models.materials import (
    PurchaseOrder,
    PurchaseOrderLine,
    StockMovement,
    StockReservation,
    YarnBatch,
    YarnType,
)
from app.models.production import Job, Machine, MachineCapability, MachineEvent, MachineSpeed
from app.models.quality import Roll
from app.models.sales import Buyer, FabricType, Order
from app.models.workforce import Shift, ShiftAssignment, Worker
from app.ripple.model import EngineSettings, JobState, MachineState, MillState, OrderState, Window, YarnState

ACTIVE_ORDER_STATUSES = {"confirmed", "in_production", "qc", "ready", "partly_dispatched"}
INACTIVE_JOB_STATUSES = {"done", "cancelled"}
OPEN_PO_STATUSES = {"sent", "partly_received"}


def _value(value: object) -> str:
    enum_value = getattr(value, "value", None)
    return enum_value if isinstance(enum_value, str) else str(value)


def _local_window(local_date: dt.date, starts: dt.time, ends: dt.time, zone: ZoneInfo) -> Window:
    start = dt.datetime.combine(local_date, starts, zone)
    end_date = local_date + dt.timedelta(days=1) if ends <= starts else local_date
    end = dt.datetime.combine(end_date, ends, zone)
    return Window(start.astimezone(dt.UTC), end.astimezone(dt.UTC))


def _regular_shifts(settings: MillSettings) -> tuple[tuple[dt.time, dt.time], ...]:
    definitions = settings.shift_definitions or {}
    result: list[tuple[dt.time, dt.time]] = []
    for code in ("A", "B"):
        item = definitions.get(code)
        if not isinstance(item, dict):
            continue
        try:
            result.append(
                (dt.time.fromisoformat(str(item["start"])), dt.time.fromisoformat(str(item["end"])))
            )
        except (KeyError, ValueError):
            continue
    return tuple(result) or EngineSettings().regular_shifts


def _engine_settings(row: MillSettings, workers: list[Worker]) -> EngineSettings:
    daily_wages = sorted(
        worker.wage_rate_paise
        for worker in workers
        if worker.is_active and _value(worker.wage_type) == "daily" and worker.wage_rate_paise > 0
    )
    overtime_hourly = int(median(daily_wages)) // 8 if daily_wages else EngineSettings().overtime_hourly_paise
    return EngineSettings(
        timezone=row.timezone,
        regular_shifts=_regular_shifts(row),
        qc_buffer_minutes=int(row.qc_buffer_minutes),
        dispatch_buffer_minutes=int(row.dispatch_buffer_minutes),
        health_amber_minutes=int(row.health_amber_minutes),
        slip_threshold_minutes=int(row.ripple_slip_threshold_minutes),
        overtime_hourly_paise=overtime_hourly,
        overtime_multiplier_bp=int(row.overtime_multiplier_bp),
    )


def load_mill_state(session: Session) -> MillState:
    """Map the current database state into the pure Ripple engine contract."""
    current = now()
    settings_row = session.scalar(select(MillSettings).limit(1))
    if settings_row is None:
        raise RuntimeError("Mill settings are required before Ripple can forecast")
    zone = ZoneInfo(settings_row.timezone)
    today = current.astimezone(zone).date()

    workers = list(session.scalars(select(Worker).where(Worker.is_active.is_(True))))
    engine_settings = _engine_settings(settings_row, workers)

    machine_rows = list(
        session.scalars(select(Machine).where(Machine.is_active.is_(True)).order_by(Machine.code))
    )
    machine_ids = [row.id for row in machine_rows]
    capabilities: dict[object, set[str]] = defaultdict(set)
    speeds: dict[object, dict[str, tuple[int, int]]] = defaultdict(dict)
    overtime: dict[object, list[Window]] = defaultdict(list)
    latest_estimate: dict[object, MachineEvent] = {}
    if machine_ids:
        for capability in session.scalars(
            select(MachineCapability).where(MachineCapability.machine_id.in_(machine_ids))
        ):
            capabilities[capability.machine_id].add(str(capability.fabric_type_id))
        for speed in session.scalars(select(MachineSpeed).where(MachineSpeed.machine_id.in_(machine_ids))):
            speeds[speed.machine_id][str(speed.fabric_type_id)] = (
                speed.avg_per_hour,
                speed.stddev_per_hour or 0,
            )
        events = session.scalars(
            select(MachineEvent)
            .where(
                MachineEvent.machine_id.in_(machine_ids),
                MachineEvent.estimated_repair_minutes.is_not(None),
            )
            .order_by(MachineEvent.created_at.desc())
        )
        for event in events:
            latest_estimate.setdefault(event.machine_id, event)
        assignment_rows = session.execute(
            select(ShiftAssignment, Shift)
            .join(Shift, Shift.code == ShiftAssignment.shift_code)
            .where(
                ShiftAssignment.machine_id.in_(machine_ids),
                ShiftAssignment.is_overtime.is_(True),
                ShiftAssignment.date.in_((today, today + dt.timedelta(days=1))),
            )
        )
        for assignment, shift in assignment_rows:
            overtime[assignment.machine_id].append(
                _local_window(assignment.date, shift.start_time, shift.end_time, zone)
            )

    machines: list[MachineState] = []
    for machine_row in machine_rows:
        status = _value(machine_row.status)
        available_from = current
        if status == "changeover":
            available_from = current + dt.timedelta(minutes=engine_settings.changeover_minutes)
        elif status in {"breakdown", "maintenance"}:
            event = latest_estimate.get(machine_row.id)
            if event is not None and event.estimated_repair_minutes is not None:
                estimate_started_at = machine_row.status_changed_at or event.created_at
                available_from = estimate_started_at + dt.timedelta(minutes=event.estimated_repair_minutes)
                if available_from <= current:
                    available_from = current + dt.timedelta(minutes=15)
            elif status == "maintenance":
                available_from = current + dt.timedelta(days=engine_settings.horizon_days + 1)
            else:
                available_from = current + dt.timedelta(minutes=15)
        machines.append(
            MachineState(
                id=str(machine_row.id),
                code=machine_row.code,
                stage=_value(machine_row.stage),
                unit=_value(machine_row.unit),
                status=status,
                available_from=available_from,
                default_speed_per_hour=machine_row.default_speed_per_hour or 0,
                speeds=speeds[machine_row.id],
                capabilities=(
                    frozenset(capabilities[machine_row.id]) if capabilities[machine_row.id] else None
                ),
                idle_cost_paise_per_hour=machine_row.idle_cost_paise_per_hour,
                overtime_windows=tuple(sorted(overtime[machine_row.id], key=lambda item: item.start)),
            )
        )

    order_rows = list(
        session.execute(
            select(Order, Buyer, FabricType)
            .join(Buyer, Buyer.id == Order.buyer_id)
            .join(FabricType, FabricType.id == Order.fabric_type_id)
            .where(Order.status.in_(ACTIVE_ORDER_STATUSES))
            .order_by(Order.code)
        )
    )
    order_ids = [order.id for order, _, _ in order_rows]
    all_jobs = (
        list(session.scalars(select(Job).where(Job.order_id.in_(order_ids)).order_by(Job.code)))
        if order_ids
        else []
    )
    issued_by_order: dict[object, int] = defaultdict(int)
    reserved_by_type: dict[object, int] = defaultdict(int)
    if order_ids:
        for order_id, quantity in session.execute(
            select(StockMovement.order_id, func.coalesce(func.sum(StockMovement.qty_g), 0))
            .where(StockMovement.order_id.in_(order_ids), StockMovement.kind == "issue")
            .group_by(StockMovement.order_id)
        ):
            issued_by_order[order_id] = abs(int(quantity))
        for yarn_type_id, quantity in session.execute(
            select(StockReservation.yarn_type_id, func.coalesce(func.sum(StockReservation.qty_g), 0))
            .where(
                StockReservation.order_id.in_(order_ids),
                StockReservation.status == "active",
            )
            .group_by(StockReservation.yarn_type_id)
        ):
            reserved_by_type[yarn_type_id] = int(quantity)

    pending_rolls: dict[object, int] = defaultdict(int)
    if order_ids:
        for order_id, count in session.execute(
            select(Roll.order_id, func.count(Roll.id))
            .where(Roll.order_id.in_(order_ids), Roll.status.in_(("pending_qc", "rework")))
            .group_by(Roll.order_id)
        ):
            pending_rolls[order_id] = int(count)

    orders: list[OrderState] = []
    fabric_by_order: dict[object, FabricType] = {}
    for order_row, buyer, fabric in order_rows:
        fabric_by_order[order_row.id] = fabric
        relevant_jobs = [
            job for job in all_jobs if job.order_id == order_row.id and _value(job.status) != "cancelled"
        ]
        yarn_need = order_row.quantity_cm * fabric.yarn_g_per_100m // 10_000
        orders.append(
            OrderState(
                id=str(order_row.id),
                code=order_row.code,
                buyer_id=str(order_row.buyer_id),
                buyer_name=buyer.name,
                due_at=dt.datetime.combine(order_row.due_date, dt.time(18), zone).astimezone(dt.UTC),
                priority=_value(order_row.priority),
                penalty_paise_per_day=order_row.late_penalty_paise_per_day,
                quantity_cm=order_row.quantity_cm,
                fabric_type_id=str(order_row.fabric_type_id),
                yarn_type_id=str(fabric.yarn_type_id),
                yarn_needed_remaining_g=max(0, yarn_need - issued_by_order[order_row.id]),
                status=_value(order_row.status),
                promised_date=order_row.promised_date,
                rolls_pending_qc=pending_rolls[order_row.id],
                production_done=bool(relevant_jobs)
                and all(_value(job.status) == "done" for job in relevant_jobs),
            )
        )

    jobs = tuple(
        JobState(
            id=str(row.id),
            code=row.code,
            order_id=str(row.order_id),
            stage=_value(row.stage),
            seq=row.seq,
            unit=_value(row.unit),
            fabric_type_id=str(fabric_by_order[row.order_id].id),
            remaining_qty=max(0, row.planned_qty - row.produced_qty),
            status=_value(row.status),
            machine_id=str(row.machine_id) if row.machine_id else None,
            queue_position=row.queue_position,
            is_running=_value(row.status) == "running",
        )
        for row in all_jobs
        if _value(row.status) not in INACTIVE_JOB_STATUSES
    )

    yarn_type_ids = {fabric.yarn_type_id for fabric in fabric_by_order.values()}
    yarn_rows = (
        list(session.scalars(select(YarnType).where(YarnType.id.in_(yarn_type_ids)))) if yarn_type_ids else []
    )
    on_hand: dict[object, int] = defaultdict(int)
    total_reserved: dict[object, int] = defaultdict(int)
    arrivals: dict[object, list[tuple[dt.datetime, int]]] = defaultdict(list)
    if yarn_type_ids:
        for yarn_type_id, quantity in session.execute(
            select(YarnBatch.yarn_type_id, func.coalesce(func.sum(StockMovement.qty_g), 0))
            .join(StockMovement, StockMovement.batch_id == YarnBatch.id)
            .where(YarnBatch.yarn_type_id.in_(yarn_type_ids), YarnBatch.status == "active")
            .group_by(YarnBatch.yarn_type_id)
        ):
            on_hand[yarn_type_id] = int(quantity)
        for yarn_type_id, quantity in session.execute(
            select(StockReservation.yarn_type_id, func.coalesce(func.sum(StockReservation.qty_g), 0))
            .where(StockReservation.yarn_type_id.in_(yarn_type_ids), StockReservation.status == "active")
            .group_by(StockReservation.yarn_type_id)
        ):
            total_reserved[yarn_type_id] = int(quantity)
        for yarn_type_id, expected_date, quantity in session.execute(
            select(
                PurchaseOrderLine.yarn_type_id,
                PurchaseOrder.expected_date,
                PurchaseOrderLine.qty_g - PurchaseOrderLine.received_g,
            )
            .join(PurchaseOrder, PurchaseOrder.id == PurchaseOrderLine.po_id)
            .where(
                PurchaseOrderLine.yarn_type_id.in_(yarn_type_ids),
                PurchaseOrder.status.in_(OPEN_PO_STATUSES),
                PurchaseOrder.expected_date.is_not(None),
                PurchaseOrderLine.qty_g > PurchaseOrderLine.received_g,
            )
        ):
            assert expected_date is not None
            arrivals[yarn_type_id].append(
                (dt.datetime.combine(expected_date, dt.time(10), zone).astimezone(dt.UTC), int(quantity))
            )
    yarn = tuple(
        YarnState(
            yarn_type_id=str(row.id),
            available_g=max(0, on_hand[row.id] - total_reserved[row.id] + reserved_by_type[row.id]),
            arrivals=tuple(sorted(arrivals[row.id], key=lambda item: item[0])),
        )
        for row in sorted(yarn_rows, key=lambda item: item.code)
    )

    return MillState(
        now=current,
        version=settings_row.state_version,
        settings=engine_settings,
        machines=tuple(machines),
        jobs=jobs,
        orders=tuple(orders),
        yarn=yarn,
    )
