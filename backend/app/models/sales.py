from __future__ import annotations
import datetime as dt
import uuid
from sqlalchemy import String, Boolean, DateTime, ForeignKey, BigInteger, Text, Integer, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base
from app.models.enums import OrderStatus, OrderPriority


class Buyer(Base):
    __tablename__ = "buyers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    contact_person: Mapped[str | None] = mapped_column(String(200), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    whatsapp: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    gstin: Mapped[str | None] = mapped_column(String(20), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    payment_terms_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    default_late_penalty_paise_per_day: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RouteTemplate(Base):
    __tablename__ = "route_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RouteStep(Base):
    __tablename__ = "route_steps"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("route_templates.id"), nullable=False)
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    stage: Mapped[str] = mapped_column(String(20), nullable=False)
    buffer_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class FabricType(Base):
    __tablename__ = "fabric_types"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    construction: Mapped[str | None] = mapped_column(String(200), nullable=True)
    width_cm: Mapped[int] = mapped_column(Integer, nullable=False)
    gsm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    colour: Mapped[str] = mapped_column(String(50), nullable=False)
    yarn_type_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("yarn_types.id"), nullable=False)
    yarn_g_per_100m: Mapped[int] = mapped_column(BigInteger, nullable=False)
    route_template_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("route_templates.id"), nullable=True)
    default_price_paise_per_m: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    gst_bp: Mapped[int] = mapped_column(Integer, default=500, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    buyer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("buyers.id"), nullable=False)
    fabric_type_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fabric_types.id"), nullable=False)
    quantity_cm: Mapped[int] = mapped_column(BigInteger, nullable=False)
    price_paise_per_m: Mapped[int] = mapped_column(BigInteger, nullable=False)
    due_date: Mapped[dt.date] = mapped_column(nullable=False)
    promised_date: Mapped[dt.date | None] = mapped_column(nullable=True)
    priority: Mapped[str] = mapped_column(SAEnum(OrderPriority, name="order_priority"), default="normal", nullable=False)
    status: Mapped[str] = mapped_column(SAEnum(OrderStatus, name="order_status"), default="draft", nullable=False, index=True)
    late_penalty_paise_per_day: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    tracking_token: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    confirmed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False, index=True)
    from_status: Mapped[str] = mapped_column(String(30), nullable=False)
    to_status: Mapped[str] = mapped_column(String(30), nullable=False)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)