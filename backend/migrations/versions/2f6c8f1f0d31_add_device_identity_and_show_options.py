"""add device identity and show-options lifeline

Revision ID: 2f6c8f1f0d31
Revises: dad632bd6715
Create Date: 2026-09-06 18:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "2f6c8f1f0d31"
down_revision: str | Sequence[str] | None = "dad632bd6715"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "google_subject",
            existing_type=sa.String(length=255),
            nullable=True,
        )
        batch_op.alter_column(
            "email",
            existing_type=sa.String(length=320),
            nullable=True,
        )

    op.create_table(
        "device_credentials",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("installation_id", sa.Uuid(), nullable=False),
        sa.Column("secret_hash", sa.String(length=64), nullable=False),
        sa.Column("platform", sa.String(length=32), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_device_credentials_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_device_credentials")),
        sa.UniqueConstraint("installation_id", name=op.f("uq_device_credentials_installation_id")),
        sa.UniqueConstraint("user_id", name=op.f("uq_device_credentials_user_id")),
    )
    op.create_index(
        op.f("ix_device_credentials_user_id"),
        "device_credentials",
        ["user_id"],
        unique=True,
    )
    op.execute(
        sa.text(
            "UPDATE match_lifelines SET lifeline_type = 'show_options' "
            "WHERE lifeline_type = 'two_answers'"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE match_lifelines SET lifeline_type = 'two_answers' "
            "WHERE lifeline_type = 'show_options'"
        )
    )
    op.drop_index(op.f("ix_device_credentials_user_id"), table_name="device_credentials")
    op.drop_table("device_credentials")

    # Device-only accounts have no Google values, so use deterministic placeholders
    # if a downgrade is required.
    op.execute(
        sa.text("UPDATE users SET google_subject = 'device-' || id WHERE google_subject IS NULL")
    )
    op.execute(
        sa.text("UPDATE users SET email = 'device-' || id || '@fahman.invalid' WHERE email IS NULL")
    )
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "email",
            existing_type=sa.String(length=320),
            nullable=False,
        )
        batch_op.alter_column(
            "google_subject",
            existing_type=sa.String(length=255),
            nullable=False,
        )
