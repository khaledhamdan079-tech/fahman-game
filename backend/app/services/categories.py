from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Category,
    Match,
    MatchQuestion,
    MatchStatus,
    Question,
    QuestionStatus,
    UserQuestionUsage,
)
from app.schemas.categories import CategoryAvailability


def active_reservations_for_user(user_id: UUID):  # type: ignore[no-untyped-def]
    return (
        select(MatchQuestion.question_id)
        .join(Match, Match.id == MatchQuestion.match_id)
        .where(
            Match.owner_id == user_id,
            Match.status.in_((MatchStatus.SETUP, MatchStatus.ACTIVE)),
        )
    )


async def list_category_availability(
    session: AsyncSession, user_id: UUID
) -> list[CategoryAvailability]:
    reserved = active_reservations_for_user(user_id)
    rows = (
        await session.execute(
            select(Category, Question.points, func.count(Question.id))
            .join(Question, Question.category_id == Category.id)
            .outerjoin(
                UserQuestionUsage,
                (UserQuestionUsage.question_id == Question.id)
                & (UserQuestionUsage.user_id == user_id),
            )
            .where(
                Category.is_active.is_(True),
                Question.status == QuestionStatus.PUBLISHED,
                UserQuestionUsage.question_id.is_(None),
                Question.id.not_in(reserved),
            )
            .group_by(Category.id, Question.points)
            .order_by(Category.name_ar)
        )
    ).all()

    counts: dict[UUID, dict[int, int]] = defaultdict(lambda: {200: 0, 400: 0, 600: 0})
    categories: dict[UUID, Category] = {}
    for category, points, count in rows:
        categories[category.id] = category
        counts[category.id][points] = count

    active_categories = (
        await session.scalars(select(Category).where(Category.is_active.is_(True)))
    ).all()
    for category in active_categories:
        categories.setdefault(category.id, category)

    result: list[CategoryAvailability] = []
    for category in sorted(categories.values(), key=lambda item: item.name_ar):
        point_counts = counts[category.id]
        complete = min(point_counts[200] // 2, point_counts[400] // 2, point_counts[600] // 2)
        result.append(
            CategoryAvailability(
                id=category.id,
                name_ar=category.name_ar,
                description_ar=category.description_ar,
                unused_200=point_counts[200],
                unused_400=point_counts[400],
                unused_600=point_counts[600],
                total_unused=sum(point_counts.values()),
                complete_matches_possible=complete,
                eligible=complete >= 1,
            )
        )
    return result
