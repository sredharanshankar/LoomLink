from __future__ import annotations
import datetime as dt
import uuid
from sqlalchemy import String, Boolean, DateTime, ForeignKey, BigInteger, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base
from app.models.enums import Role, Language


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str | None] = mapped_column(String(200), unique=True, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    role: Mapped[str] = mapped_column(SAEnum(Role, name="role"), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    pin_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    worker_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("workers.id"), nullable=True)
    buyer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("buyers.id"), nullable=True)
    preferred_language: Mapped[str] = mapped_column(SAEnum(Language, name="language"), default="en", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    refresh_tokens: Mapped[list[RefreshToken]] = relationship("RefreshToken", back_populates="user", lazy="noload")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped[User] = relationship("User", back_populates="refresh_tokens", lazy="noload")


class MillSettings(Base):
    __tablename__ = "mill_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    mill_name: Mapped[str] = mapped_column(String(200), nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Kolkata", nullable=False)
    shift_definitions: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    gst_default_bp: Mapped[int] = mapped_column(BigInteger, default=500, nullable=False)
    overtime_multiplier_bp: Mapped[int] = mapped_column(BigInteger, default=15000, nullable=False)
    qc_packing_paise_per_roll: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    overhead_paise_per_m: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    machine_rate_paise_per_hour: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    rework_cost_paise_per_m: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    rework_minutes_per_roll: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    qc_buffer_minutes: Mapped[int] = mapped_column(BigInteger, default=30, nullable=False)
    dispatch_buffer_minutes: Mapped[int] = mapped_column(BigInteger, default=30, nullable=False)
    waste_norm_bp: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    order_tolerance_bp: Mapped[int] = mapped_column(BigInteger, default=200, nullable=False)
    aged_stock_days: Mapped[int] = mapped_column(BigInteger, default=7, nullable=False)
    health_amber_minutes: Mapped[int] = mapped_column(BigInteger, default=1440, nullable=False)
    ripple_slip_threshold_minutes: Mapped[int] = mapped_column(BigInteger, default=60, nullable=False)
    state_version: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    gst_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    address_line1: Mapped[str | None] = mapped_column(String(200), nullable=True)
    address_line2: Mapped[str | None] = mapped_column(String(200), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pincode: Mapped[str | None] = mapped_column(String(10), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    bank_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    bank_account: Mapped[str | None] = mapped_column(String(30), nullable=True)
    bank_ifsc: Mapped[str | None] = mapped_column(String(15), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CodeSequence(Base):
    __tablename__ = "code_sequences"

    prefix: Mapped[str] = mapped_column(String(20), primary_key=True)
    last_value: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(128), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    endpoint: Mapped[str] = mapped_column(String(200), nullable=False)
    status_code: Mapped[int] = mapped_column(nullable=False)
    response_body: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    before: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    after: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ip: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class DomainEvent(Base):
    __tablename__ = "domain_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    actor_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    dispatched_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    role: Mapped[str | None] = mapped_column(String(20), nullable=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    title_key: Mapped[str] = mapped_column(String(100), nullable=False)
    params: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    link: Mapped[str | None] = mapped_column(String(300), nullable=True)
    read_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)