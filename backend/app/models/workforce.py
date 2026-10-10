from __future__ import annotations
import datetime as dt
import uuid
from sqlalchemy import String, Boolean, DateTime, ForeignKey, BigInteger, Text, Integer, Date, Time, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base
from app.models.enums import Stage, WageType, AttendanceStatus, AttendanceSource


class Worker(Base):
    __tablename__ = "workers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    skill_stages: Mapped[list | None] = mapped_column(ARRAY(String), nullable=True)
    wage_type: Mapped[str] = mapped_column(SAEnum(WageType, name="wage_type"), nullable=False)
    wage_rate_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    piece_rate_paise_per_m: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    default_shift: Mapped[str] = mapped_column(String(1), default="A", nullable=False)
    joined_on: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    preferred_language: Mapped[str] = mapped_column(String(2), default="en", nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Shift(Base):
    __tablename__ = "shifts"

    code: Mapped[str] = mapped_column(String(1), primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    start_time: Mapped[dt.time] = mapped_column(Time, nullable=False)
    end_time: Mapped[dt.time] = mapped_column(Time, nullable=False)
    break_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_overtime: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ShiftAssignment(Base):
    __tablename__ = "shift_assignments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workers.id"), nullable=False, index=True)
    shift_code: Mapped[str] = mapped_column(String(1), ForeignKey("shifts.code"), nullable=False)
    date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    machine_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("machines.id"), nullable=True)
    is_overtime: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Attendance(Base):
    __tablename__ = "attendance"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workers.id"), nullable=False, index=True)
    date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    shift_code: Mapped[str] = mapped_column(String(1), ForeignKey("shifts.code"), nullable=False)
    check_in_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    check_out_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(SAEnum(AttendanceStatus, name="attendance_status"), nullable=False)
    overtime_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    source: Mapped[str] = mapped_column(SAEnum(AttendanceSource, name="attendance_source"), default="app", nullable=False)
    corrected_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    correction_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PayrollRun(Base):
    __tablename__ = "payroll_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    period: Mapped[str] = mapped_column(String(7), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    computed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    approved_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PayrollLine(Base):
    __tablename__ = "payroll_lines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("payroll_runs.id"), nullable=False, index=True)
    worker_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workers.id"), nullable=False)
    days_present: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    hours_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    overtime_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    piece_cm: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    gross_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    deductions_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    net_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    paid_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class WageAdvance(Base):
    __tablename__ = "wage_advances"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workers.id"), nullable=False, index=True)
    amount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    recovered_in_run_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)