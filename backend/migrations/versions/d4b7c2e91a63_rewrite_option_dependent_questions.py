"""rewrite option-dependent questions

Revision ID: d4b7c2e91a63
Revises: 8c1a7e4d9b20
Create Date: 2026-09-06 22:10:00
"""

from __future__ import annotations

import hashlib
import re
import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d4b7c2e91a63"
down_revision: str | Sequence[str] | None = "8c1a7e4d9b20"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OPTION_DEPENDENT_PHRASES = (
    "من الآتية",
    "من الخيارات",
    "أي سؤال من",
    "اختر من",
    "حدّد الإجابة الصحيحة",
    "من التالي",
    "من التالية",
    "مما يلي",
    "كل ما سبق",
)
OPTION_ONLY_PREFIXES = (
    "اختر من الخيارات: ",
    "حدّد الإجابة الصحيحة: ",
    "فكّر جيدا: ",
)

questions = sa.table(
    "questions",
    sa.column("id", sa.Uuid()),
    sa.column("prompt_ar", sa.Text()),
    sa.column("answer_ar", sa.Text()),
)
question_options = sa.table(
    "question_options",
    sa.column("id", sa.Uuid()),
    sa.column("question_id", sa.Uuid()),
    sa.column("text_ar", sa.Text()),
    sa.column("is_correct", sa.Boolean()),
    sa.column("sort_order", sa.Integer()),
)


def _requires_visible_options(prompt: str) -> bool:
    return any(phrase in prompt for phrase in OPTION_DEPENDENT_PHRASES)


def _clean_prompt(prompt: str) -> str:
    cleaned = prompt
    for prefix in OPTION_ONLY_PREFIXES:
        cleaned = cleaned.removeprefix(prefix)
    return cleaned.replace(" من الآتية", "").replace(" من الخيارات", "")


def _statement_is_true(prompt: str) -> bool:
    return hashlib.sha256(prompt.encode("utf-8")).digest()[0] % 2 == 0


def upgrade() -> None:
    connection = op.get_bind()
    rows = list(
        connection.execute(
            sa.select(questions.c.id, questions.c.prompt_ar, questions.c.answer_ar)
        ).mappings()
    )

    for row in rows:
        old_prompt = str(row["prompt_ar"])
        if not _requires_visible_options(old_prompt):
            continue

        options = list(
            connection.execute(
                sa.select(question_options.c.text_ar, question_options.c.is_correct)
                .where(question_options.c.question_id == row["id"])
                .order_by(question_options.c.sort_order)
            ).mappings()
        )
        wrong_answers = sorted(
            str(option["text_ar"]) for option in options if not option["is_correct"]
        )
        if not wrong_answers:
            raise RuntimeError(f"Question {row['id']} has no incorrect option")

        is_true = _statement_is_true(old_prompt)
        correct_candidate = str(row["answer_ar"])
        candidate = correct_candidate if is_true else wrong_answers[0]

        if old_prompt.startswith("أي سؤال من الآتية إجابته"):
            quoted_answer = re.search(r"«([^»]+)»", old_prompt)
            if quoted_answer is None:
                raise RuntimeError(f"Question {row['id']} has no quoted answer")
            new_prompt = (
                f"صح أم خطأ: إجابة السؤال «{candidate}» "
                f"هي «{quoted_answer.group(1)}»."
            )
        else:
            clean_prompt = _clean_prompt(old_prompt)
            new_prompt = (
                f"صح أم خطأ: «{candidate}» إحدى الإجابات الصحيحة "
                f"للسؤال «{clean_prompt}»."
            )

        answer = "صح" if is_true else "خطأ"
        connection.execute(
            sa.update(questions)
            .where(questions.c.id == row["id"])
            .values(prompt_ar=new_prompt, answer_ar=answer)
        )
        connection.execute(
            sa.delete(question_options).where(question_options.c.question_id == row["id"])
        )
        connection.execute(
            sa.insert(question_options),
            [
                {
                    "id": uuid.uuid4(),
                    "question_id": row["id"],
                    "text_ar": "صح",
                    "is_correct": answer == "صح",
                    "sort_order": 0,
                },
                {
                    "id": uuid.uuid4(),
                    "question_id": row["id"],
                    "text_ar": "خطأ",
                    "is_correct": answer == "خطأ",
                    "sort_order": 1,
                },
            ],
        )


def downgrade() -> None:
    # This content-only cleanup intentionally preserves the improved questions.
    pass
