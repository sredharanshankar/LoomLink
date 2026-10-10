"""A-M10: Add performance indexes for hot query paths

Revision ID: a0002indexes
Revises: a0001mastdata
Create Date: 2026-10-10
"""
from __future__ import annotations
from alembic import op

revision = "a0002indexes"
down_revision = "a0001mastdata"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Jobs — most-queried by order + stage + status
    op.create_index("ix_jobs_order_stage", "jobs", ["order_id", "stage"])
    op.create_index("ix_jobs_machine_status", "jobs", ["machine_id", "status"])
    op.create_index("ix_jobs_status", "jobs", ["status"])

    # Rolls — quality view, dispatch
    op.create_index("ix_rolls_order_status", "rolls", ["order_id", "status"])
    op.create_index("ix_rolls_status", "rolls", ["status"])

    # Orders — buyer portal, dispatch
    op.create_index("ix_orders_buyer_status", "orders", ["buyer_id", "status"])
    op.create_index("ix_orders_tracking_token", "orders", ["tracking_token"], unique=True)
    op.create_index("ix_orders_status", "orders", ["status"])

    # Invoices — finance receivables
    op.create_index("ix_invoices_buyer_status", "invoices", ["buyer_id", "status"])
    op.create_index("ix_invoices_issue_date", "invoices", ["issue_date"])

    # Attendance — payroll computation
    op.create_index("ix_attendance_worker_date", "attendance", ["worker_id", "date"])
    op.create_index("ix_attendance_date", "attendance", ["date"])

    # Notifications — unread fetch
    op.create_index("ix_notifications_user_read", "notifications", ["user_id", "read_at"])

    # Audit log — filtered lookups
    op.create_index("ix_audit_log_entity", "audit_log", ["entity", "entity_id"])
    op.create_index("ix_audit_log_actor", "audit_log", ["actor_id"])
    op.create_index("ix_audit_log_created_at", "audit_log", ["created_at"])

    # Domain events — dispatcher polling
    op.create_index("ix_domain_events_dispatched_at", "domain_events", ["dispatched_at"])

    # Dispatch items — packing list build
    op.create_index("ix_dispatch_items_dispatch", "dispatch_items", ["dispatch_id"])

    # Payroll lines — run lookup
    op.create_index("ix_payroll_lines_run", "payroll_lines", ["run_id"])

    # Yarn stock movements — inventory valuation
    op.create_index("ix_yarn_stock_movements_batch", "yarn_stock_movements", ["batch_id"])


def downgrade() -> None:
    op.drop_index("ix_yarn_stock_movements_batch", "yarn_stock_movements")
    op.drop_index("ix_payroll_lines_run", "payroll_lines")
    op.drop_index("ix_dispatch_items_dispatch", "dispatch_items")
    op.drop_index("ix_domain_events_dispatched_at", "domain_events")
    op.drop_index("ix_audit_log_created_at", "audit_log")
    op.drop_index("ix_audit_log_actor", "audit_log")
    op.drop_index("ix_audit_log_entity", "audit_log")
    op.drop_index("ix_notifications_user_read", "notifications")
    op.drop_index("ix_attendance_date", "attendance")
    op.drop_index("ix_attendance_worker_date", "attendance")
    op.drop_index("ix_invoices_issue_date", "invoices")
    op.drop_index("ix_invoices_buyer_status", "invoices")
    op.drop_index("ix_orders_status", "orders")
    op.drop_index("ix_orders_tracking_token", "orders")
    op.drop_index("ix_orders_buyer_status", "orders")
    op.drop_index("ix_rolls_status", "rolls")
    op.drop_index("ix_rolls_order_status", "rolls")
    op.drop_index("ix_jobs_status", "jobs")
    op.drop_index("ix_jobs_machine_status", "jobs")
    op.drop_index("ix_jobs_order_stage", "jobs")
