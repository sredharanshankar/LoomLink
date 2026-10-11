"""A-M8: Financial management — invoices, payments, supplier bills, expenses, month close."""
from __future__ import annotations
import uuid
import datetime as dt
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.errors import AppError
from app.core.ids import next_code
from app.core import time as app_time
from app.core import events as ev
from app.core.audit import audit


def _actor(user: dict) -> uuid.UUID | None:
    raw = user.get("sub") or user.get("id")
    return uuid.UUID(str(raw)) if raw else None


# ---------------------------------------------------------------------------
# invoices
# ---------------------------------------------------------------------------

def list_invoices(session: Session, filters: dict | None = None) -> tuple[list[dict], int]:
    filters = filters or {}
    page = int(filters.get("page", 1))
    size = int(filters.get("size", 50))
    offset = (page - 1) * size

    where_clauses: list[str] = []
    params: dict = {}
    if filters.get("status"):
        where_clauses.append("i.status = :status")
        params["status"] = filters["status"]
    if filters.get("buyer_id"):
        where_clauses.append("i.buyer_id = :buyer_id")
        params["buyer_id"] = str(filters["buyer_id"])

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    total = session.execute(
        text(f"SELECT COUNT(*) FROM invoices i {where_sql}"), params
    ).scalar() or 0

    rows = session.execute(text(f"""
        SELECT i.id, i.number, i.order_id, i.buyer_id,
               b.name AS buyer_name, o.code AS order_code,
               i.issue_date, i.due_date, i.subtotal_paise, i.gst_bp, i.gst_paise,
               i.total_paise, i.amount_paid_paise, i.status, i.created_at
        FROM invoices i
        JOIN buyers b ON b.id = i.buyer_id
        JOIN orders o ON o.id = i.order_id
        {where_sql}
        ORDER BY i.issue_date DESC
        LIMIT :limit OFFSET :offset
    """), {**params, "limit": size, "offset": offset}).fetchall()

    items = [
        {
            "id": str(r.id), "number": r.number,
            "order_id": str(r.order_id), "order_code": r.order_code,
            "buyer_id": str(r.buyer_id), "buyer_name": r.buyer_name,
            "issue_date": r.issue_date.isoformat(), "due_date": r.due_date.isoformat(),
            "subtotal_paise": r.subtotal_paise, "gst_bp": r.gst_bp,
            "gst_paise": r.gst_paise, "total_paise": r.total_paise,
            "amount_paid_paise": r.amount_paid_paise,
            "balance_paise": r.total_paise - r.amount_paid_paise,
            "status": r.status, "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]
    return items, int(total)


def get_invoice(session: Session, invoice_id: uuid.UUID) -> dict:
    from app.models.finance import Invoice

    inv = session.get(Invoice, invoice_id)
    if inv is None:
        raise AppError("NOT_FOUND", f"Invoice {invoice_id} not found")

    lines = session.execute(text("""
        SELECT il.id, il.description, il.quantity_cm, il.rate_paise_per_m, il.amount_paise
        FROM invoice_lines il WHERE il.invoice_id = :iid ORDER BY il.id
    """), {"iid": invoice_id}).fetchall()

    payments = session.execute(text("""
        SELECT pa.amount_paise, pr.code AS payment_code, pr.method, pr.received_at
        FROM payment_allocations pa
        JOIN payments_received pr ON pr.id = pa.payment_id
        WHERE pa.invoice_id = :iid ORDER BY pr.received_at
    """), {"iid": invoice_id}).fetchall()

    buyer_row = session.execute(
        text("SELECT name, gstin, address_line1 FROM buyers WHERE id = :bid"), {"bid": inv.buyer_id}
    ).fetchone()
    order_row = session.execute(
        text("SELECT code FROM orders WHERE id = :oid"), {"oid": inv.order_id}
    ).fetchone()

    return {
        "id": str(inv.id), "number": inv.number,
        "order_id": str(inv.order_id), "order_code": order_row.code if order_row else None,
        "buyer_id": str(inv.buyer_id),
        "buyer_name": buyer_row.name if buyer_row else None,
        "buyer_gstin": buyer_row.gstin if buyer_row else None,
        "buyer_address": buyer_row.address_line1 if buyer_row else None,
        "issue_date": inv.issue_date.isoformat(), "due_date": inv.due_date.isoformat(),
        "subtotal_paise": inv.subtotal_paise, "gst_bp": inv.gst_bp,
        "gst_paise": inv.gst_paise, "total_paise": inv.total_paise,
        "amount_paid_paise": inv.amount_paid_paise,
        "balance_paise": inv.total_paise - inv.amount_paid_paise,
        "status": inv.status, "created_at": inv.created_at.isoformat(),
        "lines": [
            {
                "id": str(l.id), "description": l.description,
                "quantity_cm": l.quantity_cm, "rate_paise_per_m": l.rate_paise_per_m,
                "amount_paise": l.amount_paise,
            }
            for l in lines
        ],
        "payments": [
            {
                "code": p.payment_code, "amount_paise": p.amount_paise,
                "method": p.method, "received_at": p.received_at.isoformat(),
            }
            for p in payments
        ],
    }


# ---------------------------------------------------------------------------
# record payment  [idem]
# ---------------------------------------------------------------------------

def record_payment(session: Session, body: dict, user: dict) -> dict:
    from app.models.finance import PaymentReceived, PaymentAllocation

    actor_id = _actor(user)
    buyer_id = uuid.UUID(str(body["buyer_id"]))
    amount_paise = int(body["amount_paise"])
    method = body["method"]
    reference = body.get("reference")
    idempotency_key = body.get("idempotency_key")

    if amount_paise <= 0:
        raise AppError("VALIDATION_ERROR", "amount_paise must be positive")

    if idempotency_key:
        existing = session.execute(text("""
            SELECT id FROM payments_received WHERE reference = :ref AND buyer_id = :bid
        """), {"ref": idempotency_key, "bid": buyer_id}).fetchone()
        if existing:
            return _get_payment(session, existing.id)

    now = app_time.now()
    code = next_code(session, "payment")
    payment = PaymentReceived(
        id=uuid.uuid4(),
        code=code,
        buyer_id=buyer_id,
        amount_paise=amount_paise,
        method=method,
        reference=reference or idempotency_key,
        received_at=now,
        recorded_by=actor_id,
        created_at=now,
    )
    session.add(payment)
    session.flush()

    # Auto-allocate FIFO to oldest outstanding invoices
    outstanding = session.execute(text("""
        SELECT id, total_paise, amount_paid_paise
        FROM invoices
        WHERE buyer_id = :bid AND status IN ('issued', 'partial')
        ORDER BY due_date, issue_date
        FOR UPDATE
    """), {"bid": buyer_id}).fetchall()

    remaining = amount_paise
    for inv in outstanding:
        if remaining <= 0:
            break
        balance = inv.total_paise - inv.amount_paid_paise
        if balance <= 0:
            continue
        allocate = min(balance, remaining)
        remaining -= allocate
        new_paid = inv.amount_paid_paise + allocate
        new_status = "paid" if new_paid >= inv.total_paise else "partial"

        session.add(PaymentAllocation(
            id=uuid.uuid4(),
            payment_id=payment.id,
            invoice_id=inv.id,
            amount_paise=allocate,
            created_at=now,
        ))
        session.execute(text("""
            UPDATE invoices SET amount_paid_paise = :paid, status = :status, updated_at = :now
            WHERE id = :iid
        """), {"paid": new_paid, "status": new_status, "now": now, "iid": inv.id})

    audit(session, actor_id, "record_payment", "buyer", str(buyer_id),
          before=None, after={"amount_paise": amount_paise, "method": method})

    ev.publish(session, "payment.received", {
        "payment_id": str(payment.id), "buyer_id": str(buyer_id),
        "amount_paise": amount_paise,
    }, actor_id=actor_id)

    return _get_payment(session, payment.id)


def _get_payment(session: Session, payment_id: uuid.UUID) -> dict:
    row = session.execute(text("""
        SELECT p.id, p.code, p.buyer_id, b.name AS buyer_name,
               p.amount_paise, p.method, p.reference, p.received_at
        FROM payments_received p
        JOIN buyers b ON b.id = p.buyer_id
        WHERE p.id = :pid
    """), {"pid": payment_id}).fetchone()
    if row is None:
        raise AppError("NOT_FOUND", "Payment not found")
    return {
        "id": str(row.id), "code": row.code,
        "buyer_id": str(row.buyer_id), "buyer_name": row.buyer_name,
        "amount_paise": row.amount_paise, "method": row.method,
        "reference": row.reference, "received_at": row.received_at.isoformat(),
    }


def get_buyer_outstanding(session: Session, buyer_id: uuid.UUID) -> dict:
    rows = session.execute(text("""
        SELECT i.id, i.number, i.total_paise, i.amount_paid_paise,
               i.due_date, i.status, o.code AS order_code
        FROM invoices i JOIN orders o ON o.id = i.order_id
        WHERE i.buyer_id = :bid AND i.status IN ('issued', 'partial')
        ORDER BY i.due_date
    """), {"bid": buyer_id}).fetchall()

    total_outstanding = sum(r.total_paise - r.amount_paid_paise for r in rows)
    today = dt.date.today()
    overdue = [r for r in rows if r.due_date < today]

    return {
        "buyer_id": str(buyer_id),
        "total_outstanding_paise": total_outstanding,
        "overdue_count": len(overdue),
        "overdue_paise": sum(r.total_paise - r.amount_paid_paise for r in overdue),
        "invoices": [
            {
                "id": str(r.id), "number": r.number, "order_code": r.order_code,
                "total_paise": r.total_paise, "amount_paid_paise": r.amount_paid_paise,
                "balance_paise": r.total_paise - r.amount_paid_paise,
                "due_date": r.due_date.isoformat(), "status": r.status,
            }
            for r in rows
        ],
    }


# ---------------------------------------------------------------------------
# supplier bills
# ---------------------------------------------------------------------------

def create_supplier_bill(session: Session, body: dict, user: dict) -> dict:
    from app.models.finance import SupplierBill

    actor_id = _actor(user)
    supplier_id = uuid.UUID(str(body["supplier_id"]))
    amount_paise = int(body["amount_paise"])
    gst_paise = int(body.get("gst_paise", 0))

    if not session.execute(
        text("SELECT id FROM suppliers WHERE id = :sid"), {"sid": supplier_id}
    ).fetchone():
        raise AppError("NOT_FOUND", "Supplier not found")

    now = app_time.now()
    bill = SupplierBill(
        id=uuid.uuid4(),
        code=next_code(session, "supplier_bill"),
        supplier_id=supplier_id,
        bill_no=body["bill_no"],
        bill_date=dt.date.fromisoformat(body["bill_date"]),
        due_date=dt.date.fromisoformat(body["due_date"]),
        amount_paise=amount_paise,
        gst_paise=gst_paise,
        po_id=uuid.UUID(str(body["po_id"])) if body.get("po_id") else None,
        status="unpaid",
        amount_paid_paise=0,
        created_at=now,
        updated_at=now,
    )
    session.add(bill)
    session.flush()

    return _get_supplier_bill(session, bill.id)


def list_supplier_bills(session: Session, filters: dict | None = None) -> list[dict]:
    filters = filters or {}
    where_clauses: list[str] = []
    params: dict = {}
    if filters.get("status"):
        where_clauses.append("sb.status = :status")
        params["status"] = filters["status"]
    if filters.get("supplier_id"):
        where_clauses.append("sb.supplier_id = :supplier_id")
        params["supplier_id"] = str(filters["supplier_id"])

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    rows = session.execute(text(f"""
        SELECT sb.id, sb.code, sb.supplier_id, s.name AS supplier_name,
               sb.bill_no, sb.bill_date, sb.due_date, sb.amount_paise,
               sb.gst_paise, sb.amount_paid_paise, sb.status
        FROM supplier_bills sb
        JOIN suppliers s ON s.id = sb.supplier_id
        {where_sql}
        ORDER BY sb.due_date
    """), params).fetchall()

    return [
        {
            "id": str(r.id), "code": r.code,
            "supplier_id": str(r.supplier_id), "supplier_name": r.supplier_name,
            "bill_no": r.bill_no, "bill_date": r.bill_date.isoformat(),
            "due_date": r.due_date.isoformat(), "amount_paise": r.amount_paise,
            "gst_paise": r.gst_paise, "amount_paid_paise": r.amount_paid_paise,
            "balance_paise": r.amount_paise - r.amount_paid_paise, "status": r.status,
        }
        for r in rows
    ]


def _get_supplier_bill(session: Session, bill_id: uuid.UUID) -> dict:
    from app.models.finance import SupplierBill

    bill = session.get(SupplierBill, bill_id)
    if bill is None:
        raise AppError("NOT_FOUND", "Supplier bill not found")

    sup_row = session.execute(
        text("SELECT name FROM suppliers WHERE id = :sid"), {"sid": bill.supplier_id}
    ).fetchone()
    return {
        "id": str(bill.id), "code": bill.code,
        "supplier_id": str(bill.supplier_id),
        "supplier_name": sup_row.name if sup_row else None,
        "bill_no": bill.bill_no, "bill_date": bill.bill_date.isoformat(),
        "due_date": bill.due_date.isoformat(), "amount_paise": bill.amount_paise,
        "gst_paise": bill.gst_paise, "amount_paid_paise": bill.amount_paid_paise,
        "balance_paise": bill.amount_paise - bill.amount_paid_paise,
        "status": bill.status, "created_at": bill.created_at.isoformat(),
    }


def pay_supplier_bill(session: Session, bill_id: uuid.UUID, body: dict, user: dict) -> dict:
    from app.models.finance import SupplierBill, SupplierPayment

    actor_id = _actor(user)
    bill = session.get(SupplierBill, bill_id)
    if bill is None:
        raise AppError("NOT_FOUND", "Supplier bill not found")
    if bill.status == "paid":
        raise AppError("CONFLICT", "Bill already fully paid")

    amount_paise = int(body["amount_paise"])
    if amount_paise <= 0:
        raise AppError("VALIDATION_ERROR", "amount_paise must be positive")

    balance = bill.amount_paise - bill.amount_paid_paise
    if amount_paise > balance:
        raise AppError("VALIDATION_ERROR",
                       f"Payment {amount_paise} exceeds balance {balance}")

    now = app_time.now()
    sp = SupplierPayment(
        id=uuid.uuid4(),
        supplier_bill_id=bill_id,
        amount_paise=amount_paise,
        method=body["method"],
        reference=body.get("reference"),
        paid_at=now,
        created_at=now,
    )
    session.add(sp)

    new_paid = bill.amount_paid_paise + amount_paise
    bill.amount_paid_paise = new_paid
    bill.status = "paid" if new_paid >= bill.amount_paise else "partial"
    bill.updated_at = now

    audit(session, actor_id, "pay_supplier_bill", "supplier_bill", str(bill_id),
          before={"amount_paid_paise": bill.amount_paid_paise - amount_paise},
          after={"amount_paid_paise": new_paid, "status": bill.status})

    return _get_supplier_bill(session, bill_id)


# ---------------------------------------------------------------------------
# expenses
# ---------------------------------------------------------------------------

def create_expense(session: Session, body: dict, user: dict) -> dict:
    from app.models.finance import Expense

    actor_id = _actor(user)
    amount_paise = int(body["amount_paise"])
    if amount_paise <= 0:
        raise AppError("VALIDATION_ERROR", "amount_paise must be positive")

    now = app_time.now()
    exp = Expense(
        id=uuid.uuid4(),
        category=body["category"],
        amount_paise=amount_paise,
        date=dt.date.fromisoformat(body["date"]) if body.get("date") else app_time.today_local(),
        note=body.get("note"),
        recorded_by=actor_id,
        created_at=now,
    )
    session.add(exp)
    session.flush()

    return {
        "id": str(exp.id), "category": exp.category,
        "amount_paise": exp.amount_paise, "date": exp.date.isoformat(),
        "note": exp.note, "created_at": exp.created_at.isoformat(),
    }


def list_expenses(session: Session, filters: dict | None = None) -> list[dict]:
    filters = filters or {}
    where_clauses: list[str] = []
    params: dict = {}
    if filters.get("category"):
        where_clauses.append("category = :category")
        params["category"] = filters["category"]
    if filters.get("date_from"):
        where_clauses.append("date >= :date_from")
        params["date_from"] = filters["date_from"]
    if filters.get("date_to"):
        where_clauses.append("date <= :date_to")
        params["date_to"] = filters["date_to"]

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    rows = session.execute(text(f"""
        SELECT id, category, amount_paise, date, note, created_at
        FROM expenses {where_sql} ORDER BY date DESC
    """), params).fetchall()

    return [
        {
            "id": str(r.id), "category": r.category,
            "amount_paise": r.amount_paise, "date": r.date.isoformat(),
            "note": r.note, "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# order / roll cost breakdown
# ---------------------------------------------------------------------------

def get_order_cost(session: Session, order_id: uuid.UUID, user: dict) -> dict:
    settings_row = session.execute(
        text("SELECT overhead_paise_per_m, rework_cost_paise_per_m FROM mill_settings LIMIT 1")
    ).fetchone()
    overhead_ppm = settings_row.overhead_paise_per_m if settings_row else 0
    rework_ppm = settings_row.rework_cost_paise_per_m if settings_row else 0

    order_row = session.execute(
        text("SELECT code, quantity_cm FROM orders WHERE id = :oid"), {"oid": order_id}
    ).fetchone()
    if order_row is None:
        raise AppError("NOT_FOUND", "Order not found")

    yarn_cost = session.execute(text("""
        SELECT COALESCE(SUM(sm.qty_g::numeric * yt.price_paise_per_kg::numeric / 1000), 0)
        FROM stock_movements sm
        JOIN yarn_batches yb ON yb.id = sm.batch_id
        JOIN yarn_types yt ON yt.id = yb.yarn_type_id
        WHERE sm.order_id = :oid AND sm.direction = 'out'
    """), {"oid": order_id}).scalar() or 0

    qty_m = order_row.quantity_cm // 100
    overhead_cost = overhead_ppm * qty_m

    rework_cm = session.execute(text("""
        SELECT COALESCE(SUM(r.length_cm), 0)
        FROM rolls r WHERE r.order_id = :oid AND r.status = 'rework'
    """), {"oid": order_id}).scalar() or 0
    rework_cost = rework_ppm * int(rework_cm) // 100

    total = int(yarn_cost) + overhead_cost + rework_cost

    return {
        "order_id": str(order_id), "order_code": order_row.code,
        "yarn_cost_paise": int(yarn_cost),
        "overhead_cost_paise": overhead_cost,
        "rework_cost_paise": rework_cost,
        "total_cost_paise": total,
    }


def get_roll_cost(session: Session, roll_id: uuid.UUID, user: dict) -> dict:
    roll_row = session.execute(text("""
        SELECT r.length_cm, r.order_id, r.code, o.quantity_cm AS order_qty_cm
        FROM rolls r JOIN orders o ON o.id = r.order_id
        WHERE r.id = :rid
    """), {"rid": roll_id}).fetchone()
    if roll_row is None:
        raise AppError("NOT_FOUND", "Roll not found")

    order_cost = get_order_cost(session, roll_row.order_id, user)
    share_bp = roll_row.length_cm * 10000 // max(roll_row.order_qty_cm, 1)

    return {
        "roll_id": str(roll_id), "roll_code": roll_row.code,
        "length_cm": roll_row.length_cm,
        "share_bp": share_bp,
        "cost_paise": order_cost["total_cost_paise"] * share_bp // 10000,
    }


# ---------------------------------------------------------------------------
# receivables / payables
# ---------------------------------------------------------------------------

def get_receivables(session: Session) -> dict:
    rows = session.execute(text("""
        SELECT b.name AS buyer_name, b.id AS buyer_id,
               COUNT(i.id) AS invoice_count,
               COALESCE(SUM(i.total_paise - i.amount_paid_paise), 0) AS outstanding_paise,
               COALESCE(SUM(CASE WHEN i.due_date < CURRENT_DATE
                            THEN i.total_paise - i.amount_paid_paise ELSE 0 END), 0) AS overdue_paise
        FROM invoices i
        JOIN buyers b ON b.id = i.buyer_id
        WHERE i.status IN ('issued', 'partial')
        GROUP BY b.id, b.name
        ORDER BY outstanding_paise DESC
    """)).fetchall()

    return {
        "total_outstanding_paise": int(sum(r.outstanding_paise for r in rows)),
        "total_overdue_paise": int(sum(r.overdue_paise for r in rows)),
        "by_buyer": [
            {
                "buyer_id": str(r.buyer_id), "buyer_name": r.buyer_name,
                "invoice_count": r.invoice_count,
                "outstanding_paise": int(r.outstanding_paise),
                "overdue_paise": int(r.overdue_paise),
            }
            for r in rows
        ],
    }


def get_payables(session: Session) -> dict:
    rows = session.execute(text("""
        SELECT s.name AS supplier_name, s.id AS supplier_id,
               COUNT(sb.id) AS bill_count,
               COALESCE(SUM(sb.amount_paise - sb.amount_paid_paise), 0) AS outstanding_paise,
               COALESCE(SUM(CASE WHEN sb.due_date < CURRENT_DATE
                            THEN sb.amount_paise - sb.amount_paid_paise ELSE 0 END), 0) AS overdue_paise
        FROM supplier_bills sb
        JOIN suppliers s ON s.id = sb.supplier_id
        WHERE sb.status IN ('unpaid', 'partial')
        GROUP BY s.id, s.name
        ORDER BY outstanding_paise DESC
    """)).fetchall()

    return {
        "total_outstanding_paise": int(sum(r.outstanding_paise for r in rows)),
        "total_overdue_paise": int(sum(r.overdue_paise for r in rows)),
        "by_supplier": [
            {
                "supplier_id": str(r.supplier_id), "supplier_name": r.supplier_name,
                "bill_count": r.bill_count,
                "outstanding_paise": int(r.outstanding_paise),
                "overdue_paise": int(r.overdue_paise),
            }
            for r in rows
        ],
    }


# ---------------------------------------------------------------------------
# month close (read-only)
# ---------------------------------------------------------------------------

def get_month_close(session: Session, period: str) -> dict:
    try:
        year_s, month_s = period.split("-")
        year, month = int(year_s), int(month_s)
        period_start = dt.date(year, month, 1)
        if month == 12:
            period_end = dt.date(year + 1, 1, 1) - dt.timedelta(days=1)
        else:
            period_end = dt.date(year, month + 1, 1) - dt.timedelta(days=1)
    except (ValueError, AttributeError):
        raise AppError("VALIDATION_ERROR", "period must be YYYY-MM")

    revenue = session.execute(text("""
        SELECT COALESCE(SUM(subtotal_paise), 0) AS subtotal,
               COALESCE(SUM(gst_paise), 0) AS gst,
               COALESCE(SUM(total_paise), 0) AS total
        FROM invoices
        WHERE issue_date >= :from AND issue_date <= :to
    """), {"from": period_start, "to": period_end}).fetchone()

    payments_in = session.execute(text("""
        SELECT COALESCE(SUM(amount_paise), 0)
        FROM payments_received
        WHERE received_at::date >= :from AND received_at::date <= :to
    """), {"from": period_start, "to": period_end}).scalar() or 0

    yarn_cost = session.execute(text("""
        SELECT COALESCE(SUM(sb.amount_paise), 0)
        FROM supplier_bills sb WHERE sb.bill_date >= :from AND sb.bill_date <= :to
    """), {"from": period_start, "to": period_end}).scalar() or 0

    expenses = session.execute(text("""
        SELECT COALESCE(SUM(amount_paise), 0)
        FROM expenses WHERE date >= :from AND date <= :to
    """), {"from": period_start, "to": period_end}).scalar() or 0

    payroll = session.execute(text("""
        SELECT COALESCE(SUM(pl.net_paise), 0)
        FROM payroll_lines pl
        JOIN payroll_runs pr ON pr.id = pl.run_id
        WHERE pr.period = :period
    """), {"period": period}).scalar() or 0

    total_cost = int(yarn_cost) + int(expenses) + int(payroll)
    gross_profit = (int(revenue.subtotal) if revenue else 0) - total_cost

    return {
        "period": period,
        "revenue_subtotal_paise": int(revenue.subtotal) if revenue else 0,
        "revenue_gst_paise": int(revenue.gst) if revenue else 0,
        "revenue_total_paise": int(revenue.total) if revenue else 0,
        "payments_received_paise": int(payments_in),
        "yarn_cost_paise": int(yarn_cost),
        "expenses_paise": int(expenses),
        "payroll_paise": int(payroll),
        "total_cost_paise": total_cost,
        "gross_profit_paise": gross_profit,
    }
