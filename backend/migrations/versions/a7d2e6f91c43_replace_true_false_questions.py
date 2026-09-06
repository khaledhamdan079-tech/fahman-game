"""replace true/false questions

Revision ID: a7d2e6f91c43
Revises: f6c9a8e41d27
Create Date: 2026-09-06 23:05:00
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

import sqlalchemy as sa
from alembic import op

revision: str = "a7d2e6f91c43"
down_revision: str | Sequence[str] | None = "f6c9a8e41d27"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NAMESPACE = uuid.UUID("b4fc9875-d38e-4386-8df3-a207eef2b693")
EXPECTED_REPLACEMENT_COUNT = 1051

categories = sa.table(
    "categories",
    sa.column("id", sa.Uuid()),
    sa.column("name_ar", sa.String()),
)
questions = sa.table(
    "questions",
    sa.column("id", sa.Uuid()),
    sa.column("category_id", sa.Uuid()),
    sa.column("prompt_ar", sa.Text()),
    sa.column("answer_ar", sa.Text()),
    sa.column("points", sa.Integer()),
)
question_options = sa.table(
    "question_options",
    sa.column("id", sa.Uuid()),
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


def _load_replacements() -> list[dict[str, Any]]:
    path = (
        Path(__file__).resolve().parents[2]
        / "examples"
        / "questions.arabic.v3.replacements.json"
    )
    replacements = cast(
        list[dict[str, Any]],
        json.loads(path.read_text(encoding="utf-8"))["items"],
    )
    if len(replacements) != EXPECTED_REPLACEMENT_COUNT:
        raise RuntimeError(
            f"Expected {EXPECTED_REPLACEMENT_COUNT} replacements, got {len(replacements)}"
        )
    return replacements


def _stable_option_id(question_id: uuid.UUID, sort_order: int) -> uuid.UUID:
    return uuid.uuid5(NAMESPACE, f"option:{question_id}:{sort_order}")


def upgrade() -> None:
    connection = op.get_bind()
    replacements = _load_replacements()

    catalogue = {
        (str(row.name_ar), str(row.prompt_ar), int(row.points)): row.id
        for row in connection.execute(
            sa.select(
                categories.c.name_ar,
                questions.c.id,
                questions.c.prompt_ar,
                questions.c.points,
            ).join(questions, questions.c.category_id == categories.c.id)
        )
    }

    question_updates: list[dict[str, Any]] = []
    snapshot_updates: list[dict[str, Any]] = []
    option_rows: list[dict[str, Any]] = []
    for item in replacements:
        category_name = str(item["category_name_ar"])
        points = int(item["points"])
        old_key = (category_name, str(item["old_prompt_ar"]), points)
        new_key = (category_name, str(item["new_prompt_ar"]), points)
        question_id = catalogue.get(old_key)
        if question_id is None:
            if new_key in catalogue:
                continue
            raise RuntimeError(f"Could not find question to replace: {old_key}")

        prompt = str(item["new_prompt_ar"])
        answer = str(item["new_answer_ar"])
        options = list(item["new_options"])
        question_updates.append(
            {
                "target_question_id": question_id,
                "replacement_prompt": prompt,
                "replacement_answer": answer,
            }
        )
        snapshot_updates.append(
            {
                "target_question_id": question_id,
                "replacement_prompt": prompt,
                "replacement_answer": answer,
                "replacement_options": options,
            }
        )
        for option in options:
            sort_order = int(option["sort_order"])
            option_rows.append(
                {
                    "id": _stable_option_id(question_id, sort_order),
                    "question_id": question_id,
                    "text_ar": str(option["text_ar"]),
                    "is_correct": bool(option["is_correct"]),
                    "sort_order": sort_order,
                }
            )

    if not question_updates:
        return

    question_ids = [row["target_question_id"] for row in question_updates]
    connection.execute(
        sa.update(questions)
        .where(questions.c.id == sa.bindparam("target_question_id"))
        .values(
            prompt_ar=sa.bindparam("replacement_prompt"),
            answer_ar=sa.bindparam("replacement_answer"),
        ),
        question_updates,
    )
    connection.execute(
        sa.delete(question_options).where(question_options.c.question_id.in_(question_ids))
    )
    connection.execute(sa.insert(question_options), option_rows)
    connection.execute(
        sa.update(match_questions)
        .where(
            match_questions.c.question_id == sa.bindparam("target_question_id"),
            sa.or_(
                match_questions.c.state == "available",
                match_questions.c.state == "prepared",
            ),
        )
        .values(
            prompt_snapshot=sa.bindparam("replacement_prompt"),
            answer_snapshot=sa.bindparam("replacement_answer"),
            options_snapshot=sa.bindparam("replacement_options"),
        ),
        snapshot_updates,
    )


def downgrade() -> None:
    # The open-ended replacements are intentionally preserved for match integrity.
    pass
