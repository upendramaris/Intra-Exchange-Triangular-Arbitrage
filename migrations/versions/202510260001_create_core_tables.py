"""create opportunities and trades tables

Revision ID: 202510260001
Revises: 
Create Date: 2025-10-26 11:29:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "202510260001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "opportunities",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("triangle_hash", sa.String(length=128), nullable=False),
        sa.Column("gross_bps", sa.Float(), nullable=False),
        sa.Column("net_bps", sa.Float(), nullable=False),
        sa.Column("notional_quote", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_opportunities_triangle_hash",
        "opportunities",
        ["triangle_hash"],
    )

    op.create_table(
        "trades",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("opportunity_id", sa.Integer(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("pnl_quote", sa.Float(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_trades_opportunity_id", "trades", ["opportunity_id"])


def downgrade() -> None:
    op.drop_index("ix_trades_opportunity_id", table_name="trades")
    op.drop_table("trades")
    op.drop_index("ix_opportunities_triangle_hash", table_name="opportunities")
    op.drop_table("opportunities")
