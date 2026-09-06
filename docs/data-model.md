# Data model

## Core entities

### users

- `id` UUID primary key
- `google_subject` unique, nullable legacy field
- `email` nullable
- `display_name`
- `avatar_url`
- `created_at`, `updated_at`

### refresh_tokens

- `id` UUID primary key
- `user_id` foreign key
- `token_hash`
- `expires_at`
- `revoked_at`
- `created_at`

### device_credentials

- `id` UUID primary key
- `user_id` unique foreign key
- `installation_id` unique random UUID
- `secret_hash`
- `platform`
- `created_at`, `last_seen_at`, `revoked_at`

The raw installation secret is stored only in the phone's secure storage and
is never saved by the backend.

### categories

- `id` UUID primary key
- `name_ar`
- `description_ar`
- `cover_media_id` nullable foreign key
- `is_active`
- `created_at`, `updated_at`

### questions

- `id` UUID primary key
- `category_id` foreign key
- `question_type`: `text`, `image`, `audio`, `video`
- `prompt_ar`
- `answer_ar`
- `points`: `200`, `400`, `600`
- `media_asset_id` nullable foreign key
- `options_reveal_timing`: deprecated authoring metadata; gameplay options are
  revealed only by the `show_options` lifeline
- `max_plays` nullable; defaults to 2 for audio/video
- `status`: `draft`, `published`, `retired`
- `created_at`, `updated_at`

Database checks ensure media is present for non-text questions and absent for
text questions unless explicitly allowed later.

### question_options

- `id` UUID primary key
- `question_id` foreign key
- `text_ar`
- `is_correct`
- `sort_order`

Each published question must have exactly one correct option in the first
release.

### media_assets

- `id` UUID primary key
- `kind`: `image`, `audio`, `video`
- `storage_key` unique
- `mime_type`
- `size_bytes`
- `duration_ms` nullable
- `width` and `height` nullable
- `poster_storage_key` nullable
- `checksum_sha256`
- `status`: `pending`, `ready`, `rejected`
- `created_at`

### user_question_usage

- `user_id` foreign key
- `question_id` foreign key
- `first_match_id` foreign key
- `first_used_at`

Primary key: `(user_id, question_id)`.

This table answers whether a question has been seen by a specific user. A
global `questions.used` boolean would be incorrect because one user's game must
not affect another user's inventory.

### matches

- `id` UUID primary key
- `owner_id` foreign key
- `status`: `setup`, `active`, `completed`, `cancelled`, `expired`
- `current_team_no`: `1` or `2`
- `timer_seconds`
- `version` integer for optimistic concurrency
- `started_at`, `finished_at`, `created_at`

### match_teams

- `match_id` foreign key
- `team_no`: `1` or `2`
- `name`
- `score`

Primary key: `(match_id, team_no)`.

### match_categories

- `match_id` foreign key
- `category_id` foreign key
- `position`

### match_questions

- `id` UUID primary key
- `match_id` foreign key
- `question_id` foreign key
- `category_position`
- `slot_position`
- `question_type_snapshot`
- `prompt_snapshot`
- `answer_snapshot`
- `options_snapshot` JSON
- `media_asset_id_snapshot` nullable
- `points`
- `state`: `available`, `prepared`, `open`, `revealed`, `scored`, `replaced`
- `max_plays`
- `play_count`
- `opened_at`, `media_ready_at`, `deadline_at`, `revealed_at`, `scored_at`
- `answered_by_team_no` nullable
- `awarded_points`

Snapshots preserve the exact content played even when the question is edited
later. The media object itself is versioned/immutable; the snapshot references
that immutable asset version.

### match_lifelines

- `match_id` foreign key
- `team_no`
- `lifeline_type`: `show_options`, `double_points`, `block_opponent`
- `state`: `available`, `armed`, `used`
- `match_question_id` nullable
- `used_at` nullable

Unique constraint: `(match_id, team_no, lifeline_type)`.

### match_events

- `id` UUID primary key
- `match_id` foreign key
- `sequence_no`
- `event_type`
- `actor_user_id`
- `idempotency_key`
- `payload` JSON
- `created_at`

Unique constraints on `(match_id, sequence_no)` and `(match_id,
idempotency_key)`.

## Important indexes

- Questions by `(category_id, points, status)`
- Usage by `(user_id, question_id)`
- Active matches by `(owner_id, status)`
- Match questions by `(match_id, state)`
- Match events by `(match_id, sequence_no)`
- Media checksum for duplicate detection

## Reservation transaction

When creating a match:

1. Lock the user's active-match scope.
2. For each category and point level, select two published questions that are
   neither used by the user nor reserved by another active match owned by that
   user.
3. Insert immutable `match_questions` snapshots.
4. Fail the whole transaction if any category/level cannot provide two.
5. Mark questions used only when they transition to `open`.
