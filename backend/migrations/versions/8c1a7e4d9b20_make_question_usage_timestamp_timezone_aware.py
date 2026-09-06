"""make question usage timestamp timezone aware

Revision ID: 8c1a7e4d9b20
Revises: 2f6c8f1f0d31
Create Date: 2026-09-06 21:42:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "8c1a7e4d9b20"
down_revision: str | Sequence[str] | None = "2f6c8f1f0d31"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("user_question_usage") as batch_op:
        batch_op.alter_column(
            "first_used_at",
            existing_type=sa.DateTime(),
            type_=sa.DateTime(timezone=True),
            existing_nullable=False,
            postgresql_using="first_used_at AT TIME ZONE 'UTC'",
        )


def downgrade() -> None:
    with op.batch_alter_table("user_question_usage") as batch_op:
        batch_op.alter_column(
            "first_used_at",
            existing_type=sa.DateTime(timezone=True),
            type_=sa.DateTime(),
            existing_nullable=False,
            postgresql_using="first_used_at AT TIME ZONE 'UTC'",
        )
