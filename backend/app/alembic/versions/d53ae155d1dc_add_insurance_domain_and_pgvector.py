"""add_insurance_domain_and_pgvector

Revision ID: d53ae155d1dc
Revises: fe56fa70289e
Create Date: 2026-04-23
"""
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op
from sqlalchemy.dialects import postgresql

# UPDATE these two lines to match the generated revision IDs:
revision = "d53ae155d1dc"   # ← copy from the generated file
down_revision = "fe56fa70289e"        # ← copy from the generated file
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "client",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("industry", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("annual_turnover_nzd", sa.Float(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "policy",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("insurer", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("sum_insured_nzd", sa.Float(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("embedding", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "quote",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("premium_nzd", sa.Float(), nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("policy_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["client_id"], ["client.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["policy_id"], ["policy.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("quote")
    op.drop_table("policy")
    op.drop_table("client")
    op.execute("DROP EXTENSION IF EXISTS vector")