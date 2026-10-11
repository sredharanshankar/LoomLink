"""B-M1: Add pending_approval to order_status enum

Revision ID: b0001pendingapproval
Revises: a0002indexes
Create Date: 2026-10-11
"""
from __future__ import annotations
from alembic import op

revision = "b0001pendingapproval"
down_revision = "a0002indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE order_status ADD VALUE IF NOT EXISTS 'pending_approval' BEFORE 'draft'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values; downgrade is a no-op
    pass
