"""A-M1: add overtime_willing, hsn_code, state_code missing columns

Revision ID: a0001mastdata
Revises: f0001
Create Date: 2026-10-10
"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa

revision = "a0001mastdata"
down_revision = "f0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("workers", sa.Column("overtime_willing", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("fabric_types", sa.Column("hsn_code", sa.String(10), nullable=False, server_default="5208"))
    op.add_column("buyers", sa.Column("state_code", sa.String(10), nullable=True))
    op.add_column("mill_settings", sa.Column("state_code", sa.String(10), nullable=True))


def downgrade() -> None:
    op.drop_column("mill_settings", "state_code")
    op.drop_column("buyers", "state_code")
    op.drop_column("fabric_types", "hsn_code")
    op.drop_column("workers", "overtime_willing")
