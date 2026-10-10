from __future__ import annotations
import datetime as dt
import uuid
from sqlalchemy import String, Boolean, DateTime, ForeignKey, BigInteger, Text, Integer, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base
from app.models.enums import MachineStatus, JobStatus, Stage, Unit, MachineEventKind, MachineEventSource, ProgressSource, JobEndReason


class Machine(Base):
    __tablename__ = "machines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    stage: Mapped[str] = mapped_column(SAEnum(Stage, name="stage"), nullable=False)
    make_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    zone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    floor_x: Mapped[int | None] = mapped_column(Integer, nullable=True)
    floor_y: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(SAEnum(MachineStatus, name="machine_status"), default="idle", nullable=False)
    default_speed_per_hour: Mapped[int | None] = mapped_column(Integer, nullable=True)
    unit: Mapped[str] = mapped_column(SAEnum(Unit, name="unit"), nullable=False)
    idle_cost_paise_per_hour: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    current_job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    status_changed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MachineCapability(Base):
    __tablename__ = "machine_capabilities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    machine_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("machines.id"), nullable=False)
    fabric_type_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fabric_types.id"), nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class MachineSpeed(Base):
    __tablename__ = "machine_speeds"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    machine_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("machines.id"), nullable=False)
    fabric_type_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fabric_types.id"), nullable=False)
    avg_per_hour: Mapped[int] = mapped_column(Integer, nullable=False)
    stddev_per_hour: Mapped[int | None] = mapped_column(Integer, nullable=True)
    samples: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False, index=True)
    stage: Mapped[str] = mapped_column(SAEnum(Stage, name="stage"), nullable=False)
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    unit: Mapped[str] = mapped_column(SAEnum(Unit, name="unit"), nullable=False)
    planned_qty: Mapped[int] = mapped_column(BigInteger, nullable=False)
    produced_qty: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    waste_qty: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    machine_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("machines.id"), nullable=True)
    queue_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(SAEnum(JobStatus, name="job_status"), default="planned", nullable=False, index=True)
    planned_start_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_operator_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    blocked_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    split_from_job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class JobProgressLog(Base):
    __tablename__ = "job_progress_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False, index=True)
    worker_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    delta_qty: Mapped[int] = mapped_column(BigInteger, nullable=False)
    total_qty: Mapped[int] = mapped_column(BigInteger, nullable=False)
    source: Mapped[str] = mapped_column(SAEnum(ProgressSource, name="progress_source"), nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class JobOperatorSession(Base):
    __tablename__ = "job_operator_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False, index=True)
    worker_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    started_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_reason: Mapped[str | None] = mapped_column(SAEnum(JobEndReason, name="job_end_reason"), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class MachineEvent(Base):
    __tablename__ = "machine_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    machine_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("machines.id"), nullable=False, index=True)
    job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    kind: Mapped[str] = mapped_column(SAEnum(MachineEventKind, name="machine_event_kind"), nullable=False)
    reason_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    estimated_repair_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    source: Mapped[str] = mapped_column(SAEnum(MachineEventSource, name="machine_event_source"), default="app", nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class JobMaterialConsumption(Base):
    __tablename__ = "job_material_consumption"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False, index=True)
    batch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("yarn_batches.id"), nullable=False)
    qty_g: Mapped[int] = mapped_column(BigInteger, nullable=False)
    stock_movement_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("stock_movements.id"), nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class WipLot(Base):
    __tablename__ = "wip_lots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    qty: Mapped[int] = mapped_column(BigInteger, nullable=False)
    unit: Mapped[str] = mapped_column(SAEnum(Unit, name="unit"), nullable=False)
    parent_lot_ids: Mapped[list | None] = mapped_column(ARRAY(UUID(as_uuid=True)), nullable=True)
    status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)