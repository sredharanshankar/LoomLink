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
    # ix_jobs_status already created in f_0001_initial

    # Rolls — quality view, dispatch
    op.create_index("ix_rolls_order_status", "rolls", ["order_id", "status"])
    # ix_rolls_status already created in f_0001_initial

    # Orders — buyer portal, dispatch
    op.create_index("ix_orders_buyer_status", "orders", ["buyer_id", "status"])
    op.create_index("ix_orders_tracking_token", "orders", ["tracking_token"], unique=True)
    # ix_orders_status already created in f_0001_initial

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

    # Stock movements — inventory valuation (table is stock_movements)
    # ix_stock_movements_batch_id already created in f_0001_initial


def downgrade() -> None:
    # ix_stock_movements_batch_id owned by f_0001_initial
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
    # ix_orders_status owned by f_0001_initial
    op.drop_index("ix_orders_tracking_token", "orders")
    op.drop_index("ix_orders_buyer_status", "orders")
    # ix_rolls_status owned by f_0001_initial
    op.drop_index("ix_rolls_order_status", "rolls")
    # ix_jobs_status owned by f_0001_initial
    op.drop_index("ix_jobs_machine_status", "jobs")
    op.drop_index("ix_jobs_order_stage", "jobs")
