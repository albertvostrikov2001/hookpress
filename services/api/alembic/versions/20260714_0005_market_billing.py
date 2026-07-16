"""Market, billing, and dispute tables."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260714_0005"
down_revision: Union[str, None] = "20260714_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "kwork_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("skills", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_kwork_profiles_user_id"),
    )
    op.create_index(op.f("ix_kwork_profiles_user_id"), "kwork_profiles", ["user_id"], unique=False)

    op.create_table(
        "kworks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("price_minor", sa.BigInteger(), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="DRAFT", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["kwork_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_kworks_category"), "kworks", ["category"], unique=False)
    op.create_index(op.f("ix_kworks_profile_id"), "kworks", ["profile_id"], unique=False)
    op.create_index(op.f("ix_kworks_status"), "kworks", ["status"], unique=False)

    op.create_table(
        "market_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kwork_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("buyer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("seller_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount_minor", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="CREATED", nullable=False),
        sa.Column("payment_idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["buyer_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["kwork_id"], ["kworks.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["seller_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_market_orders_buyer_id"), "market_orders", ["buyer_id"], unique=False)
    op.create_index(op.f("ix_market_orders_kwork_id"), "market_orders", ["kwork_id"], unique=False)
    op.create_index(op.f("ix_market_orders_seller_id"), "market_orders", ["seller_id"], unique=False)
    op.create_index(op.f("ix_market_orders_status"), "market_orders", ["status"], unique=False)

    op.create_table(
        "ledger_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("account_type", sa.String(length=32), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="RUB", nullable=False),
        sa.Column("reference_type", sa.String(length=64), nullable=True),
        sa.Column("reference_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "owner_id",
            "account_type",
            "reference_type",
            "reference_id",
            name="uq_ledger_accounts_owner_type_ref",
        ),
    )
    op.create_index(op.f("ix_ledger_accounts_owner_id"), "ledger_accounts", ["owner_id"], unique=False)

    op.create_table(
        "ledger_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("transaction_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount_minor", sa.BigInteger(), nullable=False),
        sa.Column("entry_type", sa.String(length=8), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("reference_type", sa.String(length=64), nullable=True),
        sa.Column("reference_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["ledger_accounts.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key", name="uq_ledger_entries_idempotency_key"),
    )
    op.create_index(op.f("ix_ledger_entries_account_id"), "ledger_entries", ["account_id"], unique=False)
    op.create_index(op.f("ix_ledger_entries_transaction_id"), "ledger_entries", ["transaction_id"], unique=False)

    op.create_table(
        "disputes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("opened_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="OPEN", nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column("refund_amount_minor", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["opened_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["order_id"], ["market_orders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_id", name="uq_disputes_order_id"),
    )
    op.create_index(op.f("ix_disputes_status"), "disputes", ["status"], unique=False)

    op.create_table(
        "order_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sender_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("frozen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["market_orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sender_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_order_messages_order_id"), "order_messages", ["order_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_order_messages_order_id"), table_name="order_messages")
    op.drop_table("order_messages")
    op.drop_index(op.f("ix_disputes_status"), table_name="disputes")
    op.drop_table("disputes")
    op.drop_index(op.f("ix_ledger_entries_transaction_id"), table_name="ledger_entries")
    op.drop_index(op.f("ix_ledger_entries_account_id"), table_name="ledger_entries")
    op.drop_table("ledger_entries")
    op.drop_index(op.f("ix_ledger_accounts_owner_id"), table_name="ledger_accounts")
    op.drop_table("ledger_accounts")
    op.drop_index(op.f("ix_market_orders_status"), table_name="market_orders")
    op.drop_index(op.f("ix_market_orders_seller_id"), table_name="market_orders")
    op.drop_index(op.f("ix_market_orders_kwork_id"), table_name="market_orders")
    op.drop_index(op.f("ix_market_orders_buyer_id"), table_name="market_orders")
    op.drop_table("market_orders")
    op.drop_index(op.f("ix_kworks_status"), table_name="kworks")
    op.drop_index(op.f("ix_kworks_profile_id"), table_name="kworks")
    op.drop_index(op.f("ix_kworks_category"), table_name="kworks")
    op.drop_table("kworks")
    op.drop_index(op.f("ix_kwork_profiles_user_id"), table_name="kwork_profiles")
    op.drop_table("kwork_profiles")
