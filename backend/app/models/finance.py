from __future__ import annotations
import datetime as dt
import uuid
from sqlalchemy import String, DateTime, ForeignKey, BigInteger, Text, Integer, Date, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base
from app.models.enums import InvoiceStatus


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    buyer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("buyers.id"), nullable=False)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    dispatch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("dispatches.id"), nullable=False)
    issue_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    due_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    subtotal_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    gst_bp: Mapped[int] = mapped_column(Integer, nullable=False)
    gst_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    total_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    amount_paid_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    status: Mapped[str] = mapped_column(SAEnum(InvoiceStatus, name="invoice_status"), default="issued", nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class InvoiceLine(Base):
    __tablename__ = "invoice_lines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    quantity_cm: Mapped[int] = mapped_column(BigInteger, nullable=False)
    rate_paise_per_m: Mapped[int] = mapped_column(BigInteger, nullable=False)
    amount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PaymentReceived(Base):
    __tablename__ = "payments_received"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    buyer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("buyers.id"), nullable=False)
    amount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    method: Mapped[str] = mapped_column(String(20), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    received_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    recorded_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PaymentAllocation(Base):
    __tablename__ = "payment_allocations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("payments_received.id"), nullable=False, index=True)
    invoice_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False)
    amount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SupplierBill(Base):
    __tablename__ = "supplier_bills"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    bill_no: Mapped[str] = mapped_column(String(100), nullable=False)
    bill_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    due_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    amount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    gst_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    po_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=True)
    batch_ids: Mapped[list | None] = mapped_column(ARRAY(UUID(as_uuid=True)), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="unpaid", nullable=False)
    amount_paid_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SupplierPayment(Base):
    __tablename__ = "supplier_payments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_bill_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("supplier_bills.id"), nullable=False, index=True)
    amount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    method: Mapped[str] = mapped_column(String(20), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    paid_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    amount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)