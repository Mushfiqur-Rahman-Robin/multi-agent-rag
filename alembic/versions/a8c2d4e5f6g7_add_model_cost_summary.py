"""add_model_cost_summary_and_model_name

Revision ID: a8c2d4e5f6g7
Revises: 3611184d1964
Create Date: 2026-02-08 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a8c2d4e5f6g7"
down_revision: Union[str, None] = "617fa21b8fc9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add model_name column to messages table
    op.add_column(
        "messages",
        sa.Column("model_name", sa.String(), nullable=True),
    )
    op.create_index(op.f("ix_messages_model_name"), "messages", ["model_name"], unique=False)

    # Create model_cost_summary table
    op.create_table(
        "model_cost_summary",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("model_name", sa.String(), nullable=False),
        sa.Column("total_input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_cost", sa.Float(), nullable=False, server_default="0"),
        sa.Column("request_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_model_cost_summary_id"),
        "model_cost_summary",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_model_cost_summary_model_name"),
        "model_cost_summary",
        ["model_name"],
        unique=True,
    )


def downgrade() -> None:
    # Drop model_cost_summary table
    op.drop_index(op.f("ix_model_cost_summary_model_name"), table_name="model_cost_summary")
    op.drop_index(op.f("ix_model_cost_summary_id"), table_name="model_cost_summary")
    op.drop_table("model_cost_summary")

    # Remove model_name column from messages
    op.drop_index(op.f("ix_messages_model_name"), table_name="messages")
    op.drop_column("messages", "model_name")
