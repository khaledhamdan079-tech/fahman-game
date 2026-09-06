"""refresh unplayed question snapshots

Revision ID: e5a8f3c72b14
Revises: d4b7c2e91a63
Create Date: 2026-09-06 22:20:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e5a8f3c72b14"
down_revision: str | Sequence[str] | None = "d4b7c2e91a63"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

questions = sa.table(
    "questions",
    sa.column("id", sa.Uuid()),
    sa.column("prompt_ar", sa.Text()),
    sa.column("answer_ar", sa.Text()),
)
question_options = sa.table(
    "question_options",
    sa.column("question_id", sa.Uuid()),
    sa.column("text_ar", sa.Text()),
    sa.column("is_correct", sa.Boolean()),
    sa.column("sort_order", sa.Integer()),
)
match_questions = sa.table(
    "match_questions",
    sa.column("question_id", sa.Uuid()),
    sa.column("state", sa.String()),
    sa.column("prompt_snapshot", sa.Text()),
    sa.column("answer_snapshot", sa.Text()),
    sa.column("options_snapshot", sa.JSON()),
)


def upgrade() -> None:
    connection = op.get_bind()
    rows = list(
        connection.execute(
            sa.select(questions.c.id, questions.c.prompt_ar, questions.c.answer_ar)
        ).mappings()
    )

    for row in rows:
        options = [
            {
                "text_ar": option["text_ar"],
                "sort_order": option["sort_order"],
                "is_correct": option["is_correct"],
            }
            for option in connection.execute(
                sa.select(
                    question_options.c.text_ar,
                    question_options.c.sort_order,
                    question_options.c.is_correct,
                )
                .where(question_options.c.question_id == row["id"])
                .order_by(question_options.c.sort_order)
            ).mappings()
        ]
        connection.execute(
            sa.update(match_questions)
            .where(
                match_questions.c.question_id == row["id"],
                match_questions.c.state.in_(("available", "prepared")),
            )
            .values(
                prompt_snapshot=row["prompt_ar"],
                answer_snapshot=row["answer_ar"],
                options_snapshot=options,
            )
        )


def downgrade() -> None:
    # Snapshot refreshes intentionally remain aligned with the canonical questions.
    pass
