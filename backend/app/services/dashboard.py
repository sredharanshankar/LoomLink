"""A-M9: Dashboard and analytics service — owner, production, daily brief, public tracking."""
from __future__ import annotations
import uuid
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.errors import AppError
from app.core import time as app_time


# ---------------------------------------------------------------------------
# owner dashboard
# ---------------------------------------------------------------------------

def get_owner_dashboard(session: Session) -> dict:
    today = app_time.today_local()

    order_counts = session.execute(text("""
        SELECT status, COUNT(*) AS n FROM orders GROUP BY status
    """)).fetchall()
    pipeline = {r.status: r.n for r in order_counts}

    month_revenue = session.execute(text("""
        SELECT COALESCE(SUM(total_paise), 0) AS total,
               COALESCE(SUM(amount_paid_paise), 0) AS collected
        FROM invoices
        WHERE issue_date >= DATE_TRUNC('month', CURRENT_DATE)
    """)).fetchone()

    receivables = session.execute(text("""
        SELECT COALESCE(SUM(total_paise - amount_paid_paise), 0) AS total,
               COALESCE(SUM(CASE WHEN due_date < CURRENT_DATE
                            THEN total_paise - amount_paid_paise ELSE 0 END), 0) AS overdue
        FROM invoices WHERE status IN ('issued', 'partial')
    """)).fetchone()

    today_output = session.execute(text("""
        SELECT COALESCE(SUM(j.produced_qty), 0) AS total_cm
        FROM jobs j WHERE j.status IN ('running', 'completed')
          AND DATE(j.started_at) = :today
    """), {"today": today}).scalar() or 0

    qc_pending = session.execute(
        text("SELECT COUNT(*) FROM rolls WHERE status = 'pending_qc'")
    ).scalar() or 0

    low_stock = session.execute(text("""
        SELECT COUNT(*) FROM (
            SELECT yb.yarn_type_id,
                   COALESCE(SUM(sm.qty_g), 0) AS on_hand_g,
                   yt.reorder_level_g
            FROM yarn_types yt
            LEFT JOIN yarn_batches yb ON yb.yarn_type_id = yt.id
            LEFT JOIN stock_movements sm ON sm.batch_id = yb.id
            GROUP BY yb.yarn_type_id, yt.reorder_level_g
            HAVING COALESCE(SUM(sm.qty_g), 0) <= yt.reorder_level_g
        ) t
    """)).scalar() or 0

    workers_on_floor = session.execute(text("""
        SELECT COUNT(DISTINCT worker_id) FROM attendance
        WHERE date = :today AND check_in_at IS NOT NULL AND check_out_at IS NULL
    """), {"today": today}).scalar() or 0

    overdue_orders = session.execute(text("""
        SELECT COUNT(*) FROM orders
        WHERE due_date < :today AND status NOT IN ('closed', 'dispatched', 'cancelled')
    """), {"today": today}).scalar() or 0

    jobs_running = session.execute(
        text("SELECT COUNT(*) FROM jobs WHERE status = 'running'")
    ).scalar() or 0

    dispatches_today = session.execute(text("""
        SELECT COUNT(*) FROM dispatches WHERE DATE(created_at) = :today
    """), {"today": today}).scalar() or 0

    orders_due_7d = session.execute(text("""
        SELECT COUNT(*) FROM orders
        WHERE due_date <= :week AND status NOT IN ('closed', 'dispatched', 'cancelled')
    """), {"week": today + __import__('datetime').timedelta(days=7)}).scalar() or 0

    return {
        "as_of": app_time.now().isoformat(),
        "order_pipeline": pipeline,
        "overdue_orders": int(overdue_orders),
        "orders_due_7d": int(orders_due_7d),
        "month_revenue_paise": int(month_revenue.total) if month_revenue else 0,
        "month_collected_paise": int(month_revenue.collected) if month_revenue else 0,
        "cash_in_mtd_paise": int(month_revenue.collected) if month_revenue else 0,
        "receivables_paise": int(receivables.total) if receivables else 0,
        "overdue_receivables_paise": int(receivables.overdue) if receivables else 0,
        "today_output_cm": int(today_output),
        "qc_pending_rolls": int(qc_pending),
        "rolls_in_qc": int(qc_pending),
        "low_stock_types": int(low_stock),
        "low_stock_count": int(low_stock),
        "workers_on_floor": int(workers_on_floor),
        "jobs_running": int(jobs_running),
        "dispatches_today": int(dispatches_today),
    }


# ---------------------------------------------------------------------------
# daily brief
# ---------------------------------------------------------------------------

def get_daily_brief(session: Session) -> dict:
    today = app_time.today_local()

    urgent_orders = session.execute(text("""
        SELECT o.id, o.code, o.status, o.due_date, b.name AS buyer_name, o.quantity_cm
        FROM orders o JOIN buyers b ON b.id = o.buyer_id
        WHERE o.due_date <= :today
          AND o.status NOT IN ('closed', 'dispatched', 'cancelled')
        ORDER BY o.due_date LIMIT 10
    """), {"today": today}).fetchall()

    low_stock_items = session.execute(text("""
        SELECT (yt.material || ' ' || yt.count_label || ' ' || yt.colour) AS yarn_name,
               yt.code AS yarn_code,
               COALESCE(SUM(sm.qty_g), 0) AS on_hand_g,
               yt.reorder_level_g
        FROM yarn_types yt
        LEFT JOIN yarn_batches yb ON yb.yarn_type_id = yt.id
        LEFT JOIN stock_movements sm ON sm.batch_id = yb.id
        GROUP BY yt.id, yt.material, yt.count_label, yt.colour, yt.code, yt.reorder_level_g
        HAVING COALESCE(SUM(sm.qty_g), 0) <= yt.reorder_level_g
        LIMIT 10
    """)).fetchall()

    breakdowns = session.execute(
        text("SELECT code, stage FROM machines WHERE status = 'breakdown' LIMIT 10")
    ).fetchall()

    qc_backlog = session.execute(
        text("SELECT COUNT(*) FROM rolls WHERE status = 'pending_qc'")
    ).scalar() or 0

    return {
        "date": today.isoformat(),
        "urgent_orders": [
            {
                "id": str(o.id), "code": o.code, "buyer_name": o.buyer_name,
                "status": o.status, "due_date": o.due_date.isoformat(),
                "quantity_cm": o.quantity_cm,
            }
            for o in urgent_orders
        ],
        "low_stock_yarn": [
            {
                "code": y.yarn_code, "name": y.yarn_name,
                "on_hand_g": int(y.on_hand_g),
                "reorder_level_g": y.reorder_level_g,
            }
            for y in low_stock_items
        ],
        "machine_breakdowns": [
            {"code": m.code, "stage": m.stage} for m in breakdowns
        ],
        "qc_backlog_rolls": int(qc_backlog),
    }


# ---------------------------------------------------------------------------
# production dashboard
# ---------------------------------------------------------------------------

def get_production_dashboard(session: Session) -> dict:
    today = app_time.today_local()

    active_jobs = session.execute(text("""
        SELECT j.stage, COUNT(*) AS n,
               COUNT(CASE WHEN j.status = 'running' THEN 1 END) AS running,
               COUNT(CASE WHEN j.status = 'paused' THEN 1 END) AS paused,
               COUNT(CASE WHEN j.status = 'blocked' THEN 1 END) AS blocked
        FROM jobs j
        WHERE j.status IN ('ready', 'running', 'paused', 'blocked')
        GROUP BY j.stage
    """)).fetchall()

    machines = session.execute(text("""
        SELECT m.code, m.stage, m.status, m.floor_x, m.floor_y,
               j.code AS current_job, o.code AS order_code
        FROM machines m
        LEFT JOIN jobs j ON j.id = m.current_job_id
        LEFT JOIN orders o ON o.id = j.order_id
        ORDER BY m.stage, m.code
    """)).fetchall()

    today_output = session.execute(text("""
        SELECT m.stage, COALESCE(SUM(j.produced_qty), 0) AS produced_cm
        FROM jobs j
        JOIN machines m ON m.id = j.machine_id
        WHERE j.status IN ('running', 'completed')
          AND DATE(j.started_at) = :today
        GROUP BY m.stage
    """), {"today": today}).fetchall()

    attendance = session.execute(text("""
        SELECT status, COUNT(*) AS n FROM attendance WHERE date = :today GROUP BY status
    """), {"today": today}).fetchall()

    return {
        "as_of": app_time.now().isoformat(),
        "active_jobs": [
            {
                "stage": r.stage, "total": r.n,
                "running": r.running, "paused": r.paused, "blocked": r.blocked,
            }
            for r in active_jobs
        ],
        "floor_map": [
            {
                "code": m.code, "stage": m.stage, "status": m.status,
                "floor_x": m.floor_x, "floor_y": m.floor_y,
                "current_job": m.current_job, "order_code": m.order_code,
            }
            for m in machines
        ],
        "today_output": [
            {"stage": r.stage, "produced_cm": int(r.produced_cm)}
            for r in today_output
        ],
        "attendance": {r.status: r.n for r in attendance},
    }


# ---------------------------------------------------------------------------
# public order tracking (no auth — tracking_token is secret)
# ---------------------------------------------------------------------------

def get_public_tracking(session: Session, tracking_token: str) -> dict:
    order_row = session.execute(text("""
        SELECT id, code, status, quantity_cm, due_date, created_at
        FROM orders WHERE tracking_token = :token
    """), {"token": tracking_token}).fetchone()
    if order_row is None:
        raise AppError("NOT_FOUND", "Order not found")

    jobs = session.execute(text("""
        SELECT stage, status, started_at, finished_at
        FROM jobs WHERE order_id = :oid ORDER BY sort_order
    """), {"oid": order_row.id}).fetchall()

    rolls_summary = session.execute(text("""
        SELECT status, COUNT(*) AS n, COALESCE(SUM(length_cm), 0) AS total_cm
        FROM rolls WHERE order_id = :oid GROUP BY status
    """), {"oid": order_row.id}).fetchall()

    dispatch_row = session.execute(text("""
        SELECT code, status, dispatched_at FROM dispatches
        WHERE order_id = :oid AND status != 'cancelled'
        ORDER BY dispatched_at NULLS LAST LIMIT 1
    """), {"oid": order_row.id}).fetchone()

    return {
        "order_code": order_row.code,
        "status": order_row.status,
        "quantity_cm": order_row.quantity_cm,
        "due_date": order_row.due_date.isoformat() if order_row.due_date else None,
        "created_at": order_row.created_at.isoformat(),
        "stages": [
            {
                "stage": j.stage, "status": j.status,
                "started_at": j.started_at.isoformat() if j.started_at else None,
                "finished_at": j.finished_at.isoformat() if j.finished_at else None,
            }
            for j in jobs
        ],
        "rolls": [
            {"status": r.status, "count": r.n, "total_cm": int(r.total_cm)}
            for r in rolls_summary
        ],
        "dispatch": {
            "code": dispatch_row.code,
            "status": dispatch_row.status,
            "dispatched_at": dispatch_row.dispatched_at.isoformat() if dispatch_row.dispatched_at else None,
        } if dispatch_row else None,
    }
