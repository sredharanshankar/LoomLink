from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.enums import (
    LeakCategory,
    MessageChannel,
    MessageDirection,
    MessageStatus,
    RippleStatus,
    RippleTriggerKind,
)


class RippleSnapshot(Base):
    __tablename__ = "ripple_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    state_version: Mapped[int] = mapped_column(BigInteger, nullable=False)
    computed_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    forecast: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    trigger_event_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RippleEvent(Base):
    __tablename__ = "ripple_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    trigger_event_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    trigger_kind: Mapped[str] = mapped_column(
        SAEnum(RippleTriggerKind, name="ripple_trigger_kind"), nullable=False
    )
    title_key: Mapped[str] = mapped_column(String(100), nullable=False)
    params: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    affected_orders: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)
    at_risk_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    at_risk_breakdown: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(
        SAEnum(RippleStatus, name="ripple_status"), default="open", nullable=False
    )
    snapshot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ripple_snapshots.id"), nullable=True
    )
    resolved_fix_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    resolved_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RippleFix(Base):
    __tablename__ = "ripple_fixes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ripple_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ripple_events.id"), nullable=False, index=True
    )
    rank: Mapped[int] = mapped_column(nullable=False)
    kind: Mapped[str] = mapped_column(String(30), nullable=False)
    title_key: Mapped[str] = mapped_column(String(100), nullable=False)
    params: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    actions: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)
    orders_on_time: Mapped[int] = mapped_column(default=0, nullable=False)
    orders_total: Mapped[int] = mapped_column(default=0, nullable=False)
    total_late_minutes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    extra_cost_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    changes_count: Mapped[int] = mapped_column(default=0, nullable=False)
    explanation_key: Mapped[str | None] = mapped_column(String(100), nullable=True)
    explanation_params: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    applied_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    applied_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class LeakEntry(Base):
    __tablename__ = "leak_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date: Mapped[dt.date] = mapped_column(nullable=False)
    category: Mapped[str] = mapped_column(SAEnum(LeakCategory, name="leak_category"), nullable=False)
    amount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    minutes: Mapped[int | None] = mapped_column(nullable=True)
    qty: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    machine_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    roll_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    order_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    source_ref: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class BuyerMessage(Base):
    __tablename__ = "buyer_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    buyer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("buyers.id"), nullable=False, index=True
    )
    order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True
    )
    channel: Mapped[str] = mapped_column(SAEnum(MessageChannel, name="message_channel"), nullable=False)
    direction: Mapped[str] = mapped_column(SAEnum(MessageDirection, name="message_direction"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        SAEnum(MessageStatus, name="message_status"), default="queued", nullable=False
    )
    provider_ref: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
