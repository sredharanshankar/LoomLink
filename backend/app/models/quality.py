from __future__ import annotations
import datetime as dt
import uuid
from sqlalchemy import String, Boolean, DateTime, ForeignKey, BigInteger, Text, Integer, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base
from app.models.enums import RollStatus, QcDecision, DefectSeverity, DispatchStatus


class DefectCode(Base):
    __tablename__ = "defect_codes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    label_en: Mapped[str] = mapped_column(String(100), nullable=False)
    label_hi: Mapped[str | None] = mapped_column(String(100), nullable=True)
    label_te: Mapped[str | None] = mapped_column(String(100), nullable=True)
    label_ta: Mapped[str | None] = mapped_column(String(100), nullable=True)
    default_severity: Mapped[str] = mapped_column(SAEnum(DefectSeverity, name="defect_severity"), nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Roll(Base):
    __tablename__ = "rolls"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False, index=True)
    finishing_job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=True)
    length_cm: Mapped[int] = mapped_column(BigInteger, nullable=False)
    weight_g: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    status: Mapped[str] = mapped_column(SAEnum(RollStatus, name="roll_status"), default="pending_qc", nullable=False, index=True)
    shelf_location: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Inspection(Base):
    __tablename__ = "inspections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    roll_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("rolls.id"), nullable=False, index=True)
    inspector_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    decision: Mapped[str] = mapped_column(SAEnum(QcDecision, name="qc_decision"), nullable=False)
    measured_length_cm: Mapped[int] = mapped_column(BigInteger, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class InspectionDefect(Base):
    __tablename__ = "inspection_defects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    inspection_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("inspections.id"), nullable=False)
    defect_code: Mapped[str] = mapped_column(String(30), nullable=False)
    position_cm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    severity: Mapped[str] = mapped_column(SAEnum(DefectSeverity, name="defect_severity"), nullable=False)
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Dispatch(Base):
    __tablename__ = "dispatches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False, index=True)
    buyer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("buyers.id"), nullable=False)
    status: Mapped[str] = mapped_column(SAEnum(DispatchStatus, name="dispatch_status"), default="draft", nullable=False)
    vehicle_no: Mapped[str | None] = mapped_column(String(20), nullable=True)
    transporter: Mapped[str | None] = mapped_column(String(100), nullable=True)
    driver_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    dispatched_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class DispatchItem(Base):
    __tablename__ = "dispatch_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dispatch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("dispatches.id"), nullable=False)
    roll_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("rolls.id"), nullable=False)
    length_cm: Mapped[int] = mapped_column(BigInteger, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)