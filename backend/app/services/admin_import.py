from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.db.models import (
    Category,
    MediaAsset,
    MediaStatus,
    Question,
    QuestionOption,
    QuestionStatus,
)
from app.schemas.admin import QuestionImportRequest, QuestionImportResponse


async def import_questions(
    session: AsyncSession, request: QuestionImportRequest
) -> QuestionImportResponse:
    categories_created = 0
    questions_created = 0
    media_created = 0
    skipped_duplicates = 0
    category_cache: dict[str, Category] = {}
    duplicate_keys: set[tuple[UUID, str, int]] = set()

    for item in request.items:
        category_name = item.category_name_ar.strip()
        category = category_cache.get(category_name)
        if category is None:
            category = await session.scalar(
                select(Category).where(Category.name_ar == category_name)
            )
            if category is None:
                category = Category(
                    name_ar=category_name,
                    description_ar=item.category_description_ar,
                    is_active=True,
                )
                session.add(category)
                await session.flush()
                categories_created += 1
            category_cache[category_name] = category

        prompt = item.prompt_ar.strip()
        duplicate_key = (category.id, prompt, item.points)
        if duplicate_key in duplicate_keys:
            skipped_duplicates += 1
            continue
        existing = await session.scalar(
            select(Question.id).where(
                Question.category_id == category.id,
                Question.prompt_ar == prompt,
                Question.points == item.points,
            )
        )
        if existing is not None:
            skipped_duplicates += 1
            duplicate_keys.add(duplicate_key)
            continue

        media_asset_id = item.media_asset_id
        if media_asset_id is not None:
            referenced_media = await session.get(MediaAsset, media_asset_id)
            if referenced_media is None:
                raise AppError(
                    "MEDIA_NOT_FOUND",
                    "The referenced media asset does not exist",
                    status_code=404,
                )
            if referenced_media.kind.value != item.question_type.value:
                raise AppError(
                    "MEDIA_IMPORT_CONFLICT",
                    "The referenced media kind does not match the question",
                    status_code=409,
                )
            if request.publish and referenced_media.status != MediaStatus.READY:
                raise AppError(
                    "MEDIA_NOT_READY",
                    "Referenced media must be ready before publishing",
                    status_code=409,
                )
        elif item.media is not None:
            media = await session.scalar(
                select(MediaAsset).where(
                    MediaAsset.checksum_sha256 == item.media.checksum_sha256.lower()
                )
            )
            if media is None:
                storage_key_owner = await session.scalar(
                    select(MediaAsset).where(MediaAsset.storage_key == item.media.storage_key)
                )
                if storage_key_owner is not None:
                    raise AppError(
                        "MEDIA_IMPORT_CONFLICT",
                        "The storage key already belongs to different media",
                        status_code=409,
                    )
                media = MediaAsset(
                    kind=item.media.kind,
                    storage_key=item.media.storage_key,
                    mime_type=item.media.mime_type,
                    size_bytes=item.media.size_bytes,
                    duration_ms=item.media.duration_ms,
                    width=item.media.width,
                    height=item.media.height,
                    poster_storage_key=item.media.poster_storage_key,
                    checksum_sha256=item.media.checksum_sha256.lower(),
                    status=item.media.status,
                )
                session.add(media)
                await session.flush()
                media_created += 1
            elif media.kind != item.media.kind or media.storage_key != item.media.storage_key:
                raise AppError(
                    "MEDIA_IMPORT_CONFLICT",
                    "The checksum already belongs to different media",
                    status_code=409,
                )
            if request.publish and media.status != MediaStatus.READY:
                raise AppError(
                    "MEDIA_NOT_READY",
                    "Media must be ready before publishing",
                    status_code=409,
                )
            media_asset_id = media.id

        question = Question(
            category_id=category.id,
            question_type=item.question_type,
            prompt_ar=prompt,
            answer_ar=item.answer_ar.strip(),
            points=item.points,
            media_asset_id=media_asset_id,
            options_reveal_timing=item.options_reveal_timing,
            max_plays=(
                item.max_plays
                if item.max_plays is not None
                else (2 if item.question_type.value in ("audio", "video") else None)
            ),
            status=QuestionStatus.PUBLISHED if request.publish else QuestionStatus.DRAFT,
        )
        session.add(question)
        await session.flush()
        session.add_all(
            [
                QuestionOption(
                    question_id=question.id,
                    text_ar=option.text_ar.strip(),
                    is_correct=option.is_correct,
                    sort_order=option.sort_order,
                )
                for option in item.options
            ]
        )
        duplicate_keys.add(duplicate_key)
        questions_created += 1

    await session.commit()
    return QuestionImportResponse(
        categories_created=categories_created,
        questions_created=questions_created,
        media_created=media_created,
        skipped_duplicates=skipped_duplicates,
    )
