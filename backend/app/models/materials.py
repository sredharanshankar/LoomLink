from __future__ import annotations
import datetime as dt
import uuid
from sqlalchemy import String, Boolean, DateTime, ForeignKey, BigInteger, Text, Integer, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base
from app.models.enums import PurchaseOrderStatus, YarnBatchStatus, StockReservationStatus, MovementKind


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    contact_person: Mapped[str | None] = mapped_column(String(200), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    gstin: Mapped[str | None] = mapped_column(String(20), nullable=True)
    payment_terms_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class YarnType(Base):
    __tablename__ = "yarn_types"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    material: Mapped[str] = mapped_column(String(30), nullable=False)
    count_label: Mapped[str] = mapped_column(String(20), nullable=False)
    colour: Mapped[str] = mapped_column(String(50), nullable=False)
    colour_hex: Mapped[str | None] = mapped_column(String(7), nullable=True)
    reorder_level_g: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    standard_rate_paise_per_kg: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SupplierYarnType(Base):
    __tablename__ = "supplier_yarn_types"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    yarn_type_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("yarn_types.id"), nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    status: Mapped[str] = mapped_column(SAEnum(PurchaseOrderStatus, name="purchase_order_status"), default="draft", nullable=False)
    expected_date: Mapped[dt.date | None] = mapped_column(nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PurchaseOrderLine(Base):
    __tablename__ = "purchase_order_lines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    po_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=False)
    yarn_type_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("yarn_types.id"), nullable=False)
    qty_g: Mapped[int] = mapped_column(BigInteger, nullable=False)
    rate_paise_per_kg: Mapped[int] = mapped_column(BigInteger, nullable=False)
    received_g: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class YarnBatch(Base):
    __tablename__ = "yarn_batches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    yarn_type_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("yarn_types.id"), nullable=False)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    po_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=True)
    intended_order_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    received_g: Mapped[int] = mapped_column(BigInteger, nullable=False)
    rate_paise_per_kg: Mapped[int] = mapped_column(BigInteger, nullable=False)
    location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    received_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    supplier_invoice_ref: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(SAEnum(YarnBatchStatus, name="yarn_batch_status"), default="active", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("yarn_batches.id"), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(SAEnum(MovementKind, name="movement_kind"), nullable=False)
    qty_g: Mapped[int] = mapped_column(BigInteger, nullable=False)
    order_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class StockReservation(Base):
    __tablename__ = "stock_reservations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    yarn_type_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("yarn_types.id"), nullable=False)
    batch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("yarn_batches.id"), nullable=True)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    qty_g: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(SAEnum(StockReservationStatus, name="stock_reservation_status"), default="active", nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)