"""expand Arabic question bank

Revision ID: f6c9a8e41d27
Revises: e5a8f3c72b14
Create Date: 2026-09-06 22:45:00
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import sqlalchemy as sa
from alembic import op

revision: str = "f6c9a8e41d27"
down_revision: str | Sequence[str] | None = "e5a8f3c72b14"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NAMESPACE = uuid.UUID("946e253a-1509-4bb5-9b4d-c8da4dc5e330")
EXPECTED_QUESTION_COUNT = 2448

categories = sa.table(
    "categories",
    sa.column("id", sa.Uuid()),
    sa.column("name_ar", sa.String()),
    sa.column("description_ar", sa.Text()),
    sa.column("is_active", sa.Boolean()),
)
questions = sa.table(
    "questions",
    sa.column("id", sa.Uuid()),
    sa.column("category_id", sa.Uuid()),
    sa.column("question_type", sa.String()),
    sa.column("prompt_ar", sa.Text()),
    sa.column("answer_ar", sa.Text()),
    sa.column("points", sa.Integer()),
    sa.column("media_asset_id", sa.Uuid()),
    sa.column("options_reveal_timing", sa.String()),
    sa.column("max_plays", sa.Integer()),
    sa.column("status", sa.String()),
)
question_options = sa.table(
    "question_options",
    sa.column("id", sa.Uuid()),
    sa.column("question_id", sa.Uuid()),
    sa.column("text_ar", sa.Text()),
    sa.column("is_correct", sa.Boolean()),
    sa.column("sort_order", sa.Integer()),
)


def _load_items() -> list[dict[str, Any]]:
    examples_directory = Path(__file__).resolve().parents[2] / "examples"
    paths = sorted(examples_directory.glob("questions.arabic.v2.part*.json"))
    if not paths:
        raise RuntimeError(f"Question catalogue not found in {examples_directory}")

    items: list[dict[str, Any]] = []
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        items.extend(payload["items"])
    if len(items) != EXPECTED_QUESTION_COUNT:
        raise RuntimeError(
            f"Expected {EXPECTED_QUESTION_COUNT} catalogue questions, got {len(items)}"
        )
    return items


def _stable_id(kind: str, value: str) -> uuid.UUID:
    return uuid.uuid5(NAMESPACE, f"{kind}:{value}")


def upgrade() -> None:
    connection = op.get_bind()
    items = _load_items()

    category_ids = {
        str(row.name_ar): row.id
        for row in connection.execute(
            sa.select(categories.c.id, categories.c.name_ar)
        )
    }
    descriptions: dict[str, str] = {}
    for item in items:
        descriptions.setdefault(
            str(item["category_name_ar"]), str(item["category_description_ar"])
        )

    category_rows: list[dict[str, Any]] = []
    for category_name, description in descriptions.items():
        if category_name in category_ids:
            continue
        category_id = _stable_id("category", category_name)
        category_ids[category_name] = category_id
        category_rows.append(
            {
                "id": category_id,
                "name_ar": category_name,
                "description_ar": description,
                "is_active": True,
            }
        )
    if category_rows:
        connection.execute(sa.insert(categories), category_rows)

    existing_keys = {
        (row.category_id, str(row.prompt_ar), int(row.points))
        for row in connection.execute(
            sa.select(
                questions.c.category_id,
                questions.c.prompt_ar,
                questions.c.points,
            )
        )
    }

    question_rows: list[dict[str, Any]] = []
    option_rows: list[dict[str, Any]] = []
    for item in items:
        category_id = category_ids[str(item["category_name_ar"])]
        prompt = str(item["prompt_ar"]).strip()
        points = int(item["points"])
        key = (category_id, prompt, points)
        if key in existing_keys:
            continue

        question_id = _stable_id(
            "question", f"{category_id}:{points}:{prompt}"
        )
        question_rows.append(
            {
                "id": question_id,
                "category_id": category_id,
                "question_type": str(item["question_type"]),
                "prompt_ar": prompt,
                "answer_ar": str(item["answer_ar"]).strip(),
                "points": points,
                "media_asset_id": None,
                "options_reveal_timing": str(item["options_reveal_timing"]),
                "max_plays": None,
                "status": "published",
            }
        )
        for option in item["options"]:
            sort_order = int(option["sort_order"])
            option_rows.append(
                {
                    "id": _stable_id("option", f"{question_id}:{sort_order}"),
                    "question_id": question_id,
                    "text_ar": str(option["text_ar"]).strip(),
                    "is_correct": bool(option["is_correct"]),
                    "sort_order": sort_order,
                }
            )
        existing_keys.add(key)

    if question_rows:
        connection.execute(sa.insert(questions), question_rows)
        connection.execute(sa.insert(question_options), option_rows)


def downgrade() -> None:
    # Catalogue additions are intentionally preserved to avoid invalidating match history.
    pass
