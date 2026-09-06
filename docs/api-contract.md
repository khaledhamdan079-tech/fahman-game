# API contract

All endpoints are versioned under `/v1`. Authenticated commands use a bearer
access token. State-changing match commands also require an `Idempotency-Key`
header and the caller's expected match version.

## Authentication

- `POST /v1/auth/device/session` — create or restore an installation user and issue tokens
- `POST /v1/auth/device/attach` — attach an existing authenticated user to this installation
- `POST /v1/auth/google` — temporary migration-only Google token exchange
- `POST /v1/auth/refresh` — rotate a refresh token
- `POST /v1/auth/logout` — revoke the current refresh token
- `GET /v1/auth/me` — current profile

## Categories and availability

- `GET /v1/categories/eligible`

Each category includes counts for 200, 400, and 600 points, total unused
questions, complete matches possible, and an eligibility flag.

## Matches

- `POST /v1/matches` — create a match and reserve questions
- `GET /v1/matches/active` — return the signed-in user's resumable match or null
- `GET /v1/matches/{match_id}` — authoritative resumable state
- `POST /v1/matches/{match_id}/cancel`
- `GET /v1/matches` — the latest 50 matches

## Question commands

- `POST /v1/matches/{match_id}/questions/{match_question_id}/open`
  - Transitions the question to open and marks it used.
- `POST /v1/matches/{match_id}/questions/{match_question_id}/media-ready`
  - Sets the authoritative deadline after successful preload.
- `POST /v1/matches/{match_id}/questions/{match_question_id}/play`
  - Increments and validates the audio/video play count.
- `POST /v1/matches/{match_id}/questions/{match_question_id}/reveal`
  - Freezes the timer and returns the answer.
- `POST /v1/matches/{match_id}/questions/{match_question_id}/score`
  - Accepts Team 1, Team 2, or No one; computes points and advances the turn.

## Lifelines

- `POST /v1/matches/{match_id}/lifelines/{lifeline_type}/arm`
- `POST /v1/matches/{match_id}/lifelines/{lifeline_type}/cancel`

The backend validates the active team, availability, and question state.

## Media

- `GET /v1/matches/{match_id}/media/{media_asset_id}/playback`

Returns a short-lived signed URL only when the media belongs to a question
reserved in the authenticated user's active match. The response includes MIME
type, duration, poster URL when applicable, expiry, and maximum play count.

## Administration/import

The first release can expose protected operator-only tooling:

- `POST /v1/admin/import/questions` — validated JSON batch, protected by
  `X-Admin-Key`
- `POST /v1/admin/media/presign-upload` — validate metadata, reserve a private
  server-owned object key, and return a short-lived signed PUT URL
- `POST /v1/admin/media/{media_asset_id}/complete` — compare stored size, MIME,
  and checksum metadata before marking the asset ready
- `POST /v1/admin/questions/{question_id}/publish`

Operator authorization must be separate from ordinary user authentication.

## Error model

Errors return a stable code, Arabic-safe message, and optional field details.
Important codes include:

- `AUTH_TOKEN_INVALID`
- `CATEGORY_NOT_ELIGIBLE`
- `QUESTION_NOT_AVAILABLE`
- `STALE_MATCH_VERSION`
- `INVALID_STATE_TRANSITION`
- `LIFELINE_ALREADY_USED`
- `LIFELINE_WRONG_TIMING`
- `MEDIA_NOT_READY`
- `MEDIA_PLAY_LIMIT_REACHED`
- `IDEMPOTENCY_CONFLICT`

Conflict responses include the current match version so Flutter can refresh and
recover.
