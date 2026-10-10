from __future__ import annotations

import datetime as dt
import uuid

from app.models.identity import MillSettings
from app.models.materials import (
    PurchaseOrder,
    PurchaseOrderLine,
    StockMovement,
    StockReservation,
    Supplier,
    YarnBatch,
    YarnType,
)
from app.models.production import Job, Machine, MachineCapability, MachineEvent, MachineSpeed
from app.models.sales import Buyer, FabricType, Order
from app.models.workforce import Shift, ShiftAssignment, Worker
from app.ripple_service.state_loader import load_mill_state

UTC = dt.UTC
NOW = dt.datetime(2026, 10, 12, 5, 30, tzinfo=UTC)  # 11:00 Asia/Kolkata


def _id() -> uuid.UUID:
    return uuid.uuid4()


def test_load_mill_state_maps_breakdown_overtime_and_yarn_arrival(db_session, monkeypatch) -> None:
    """Catches missing repair estimates, overtime windows, or inbound yarn supply."""
    monkeypatch.setattr("app.ripple_service.state_loader.now", lambda: NOW)
    created = NOW - dt.timedelta(days=2)
    settings = MillSettings(
        id=1,
        mill_name="Everest",
        timezone="Asia/Kolkata",
        shift_definitions={
            "A": {"start": "06:00", "end": "14:00"},
            "B": {"start": "14:00", "end": "22:00"},
        },
        overtime_multiplier_bp=16_000,
        qc_buffer_minutes=35,
        dispatch_buffer_minutes=25,
        health_amber_minutes=720,
        ripple_slip_threshold_minutes=45,
        state_version=17,
        created_at=created,
    )
    supplier = Supplier(
        id=_id(),
        code="SUP-001",
        name="Vel",
        payment_terms_days=30,
        is_active=True,
        created_at=created,
    )
    yarn_type = YarnType(
        id=_id(),
        code="YT-COT-40S-BLU",
        material="cotton",
        count_label="40s",
        colour="blue",
        reorder_level_g=10_000,
        standard_rate_paise_per_kg=22_000,
        is_active=True,
        created_at=created,
    )
    buyer = Buyer(
        id=_id(),
        code="BUY-001",
        name="Kaveri",
        payment_terms_days=30,
        default_late_penalty_paise_per_day=50_000,
        is_active=True,
        created_at=created,
    )
    fabric = FabricType(
        id=_id(),
        code="FAB-POP-BLU",
        name="Blue poplin",
        width_cm=150,
        colour="blue",
        yarn_type_id=yarn_type.id,
        yarn_g_per_100m=12_000,
        default_price_paise_per_m=20_000,
        gst_bp=500,
        is_active=True,
        created_at=created,
    )
    order = Order(
        id=_id(),
        code="ORD-104",
        buyer_id=buyer.id,
        fabric_type_id=fabric.id,
        quantity_cm=100_000,
        price_paise_per_m=20_000,
        due_date=dt.date(2026, 10, 14),
        priority="high",
        status="in_production",
        late_penalty_paise_per_day=50_000,
        tracking_token="a" * 32,
        created_at=created,
    )
    machine = Machine(
        id=_id(),
        code="WV-02",
        name="Loom 2",
        stage="weaving",
        status="breakdown",
        default_speed_per_hour=5_000,
        unit="cm",
        idle_cost_paise_per_hour=12_000,
        status_changed_at=NOW - dt.timedelta(minutes=30),
        is_active=True,
        created_at=created,
    )
    job = Job(
        id=_id(),
        code="JOB-104-WV",
        order_id=order.id,
        stage="weaving",
        seq=1,
        unit="cm",
        planned_qty=100_000,
        produced_qty=20_000,
        waste_qty=0,
        machine_id=machine.id,
        queue_position=1,
        status="blocked",
        created_at=created,
    )
    worker = Worker(
        id=_id(),
        code="EMP-001",
        name="Anil",
        wage_type="daily",
        wage_rate_paise=80_000,
        default_shift="A",
        overtime_willing=True,
        is_active=True,
        preferred_language="en",
        created_at=created,
    )
    shift = Shift(
        code="C",
        name="Night overtime",
        start_time=dt.time(22),
        end_time=dt.time(6),
        break_minutes=0,
        is_overtime=True,
        created_at=created,
    )
    batch = YarnBatch(
        id=_id(),
        code="YB-2610-01",
        yarn_type_id=yarn_type.id,
        supplier_id=supplier.id,
        received_g=80_000,
        rate_paise_per_kg=22_000,
        received_at=created,
        status="active",
        created_at=created,
    )
    purchase = PurchaseOrder(
        id=_id(),
        code="PO-2610-01",
        supplier_id=supplier.id,
        status="sent",
        expected_date=dt.date(2026, 10, 13),
        created_at=created,
    )
    db_session.add_all([settings, supplier, yarn_type, buyer, machine, worker, shift])
    db_session.flush()
    db_session.add(fabric)
    db_session.flush()
    db_session.add_all([order, batch, purchase])
    db_session.flush()
    db_session.add(job)
    db_session.flush()
    db_session.add_all(
        [
            MachineCapability(id=_id(), machine_id=machine.id, fabric_type_id=fabric.id, created_at=created),
            MachineSpeed(
                id=_id(),
                machine_id=machine.id,
                fabric_type_id=fabric.id,
                avg_per_hour=6_000,
                stddev_per_hour=600,
                samples=5,
                updated_at=created,
            ),
            MachineEvent(
                id=_id(),
                machine_id=machine.id,
                job_id=job.id,
                kind="breakdown",
                estimated_repair_minutes=120,
                source="app",
                created_at=NOW - dt.timedelta(minutes=30),
            ),
            ShiftAssignment(
                id=_id(),
                worker_id=worker.id,
                shift_code="C",
                date=dt.date(2026, 10, 12),
                machine_id=machine.id,
                is_overtime=True,
                created_at=created,
            ),
            StockMovement(
                id=_id(), batch_id=batch.id, kind="receipt", qty_g=80_000, actor_id=None, created_at=created
            ),
            StockReservation(
                id=_id(),
                yarn_type_id=yarn_type.id,
                batch_id=batch.id,
                order_id=order.id,
                qty_g=30_000,
                status="active",
                created_at=created,
            ),
            PurchaseOrderLine(
                id=_id(),
                po_id=purchase.id,
                yarn_type_id=yarn_type.id,
                qty_g=50_000,
                rate_paise_per_kg=21_000,
                received_g=10_000,
                created_at=created,
            ),
        ]
    )
    db_session.flush()

    state = load_mill_state(db_session)

    assert state.version == 17
    assert state.settings.qc_buffer_minutes == 35
    assert state.settings.dispatch_buffer_minutes == 25
    assert state.settings.overtime_hourly_paise == 10_000
    loaded_machine = state.machines[0]
    assert loaded_machine.available_from == NOW + dt.timedelta(minutes=90)
    assert loaded_machine.speeds[str(fabric.id)] == (6_000, 600)
    assert loaded_machine.capabilities == frozenset({str(fabric.id)})
    assert loaded_machine.overtime_windows == (
        # 22:00 local to 06:00 next day.
        type(loaded_machine.overtime_windows[0])(
            dt.datetime(2026, 10, 12, 16, 30, tzinfo=UTC),
            dt.datetime(2026, 10, 13, 0, 30, tzinfo=UTC),
        ),
    )
    assert state.jobs[0].remaining_qty == 80_000
    assert state.orders[0].due_at == dt.datetime(2026, 10, 14, 12, 30, tzinfo=UTC)
    assert state.orders[0].yarn_needed_remaining_g == 120_000
    assert state.yarn[0].available_g == 80_000
    assert state.yarn[0].arrivals == ((dt.datetime(2026, 10, 13, 4, 30, tzinfo=UTC), 40_000),)
