# Architecture

## System overview

```text
Flutter application
  | HTTPS JSON + authenticated media requests
  v
FastAPI on Railway
  | SQLAlchemy transactions
  v
Railway PostgreSQL

FastAPI
  | short-lived signed URLs
  v
S3-compatible object storage / CDN
```

## Backend responsibilities

- Verify private installation credentials and manage local sessions.
- Return category eligibility for the authenticated user.
- Atomically reserve questions for a match.
- Enforce the match and question state machines.
- Validate lifeline ownership and timing.
- Calculate scores and alternate turns.
- Mark opened questions as used for the user.
- Authorize image, audio, and video playback.
- Preserve immutable question snapshots in match history.
- Record an ordered event stream for recovery and audit.

Recommended backend modules:

```text
backend/
  app/
    api/
    auth/
    categories/
    matches/
    questions/
    media/
    users/
    db/
    core/
  migrations/
  tests/
```

## Frontend responsibilities

- Present the Arabic RTL experience.
- Hold only a projection of authoritative server state.
- Preload media and report readiness.
- Render the countdown from server timestamps.
- Store session secrets in secure storage.
- Cache the active match identifier for recovery.
- Retry safe reads and protect against duplicate command submission.

Recommended Flutter modules:

```text
frontend/lib/
  app/
  core/
    auth/
    networking/
    storage/
    theme/
  features/
    authentication/
    home/
    match_setup/
    game/
    history/
    profile/
```

## Authentication

1. Flutter generates a random installation UUID and high-entropy secret.
2. Flutter stores both values in platform secure storage.
3. Flutter sends them to `POST /v1/auth/device/session`.
4. FastAPI creates or restores the installation user after checking the secret hash.
5. FastAPI issues a short-lived access token and a rotating refresh token.
6. Only hashes of the installation secret and refresh token are stored.

IMEI, serial number, MAC address, and other hardware identifiers are never read.

## Match consistency

Every state-changing command runs in a database transaction and locks the match
row. Each command includes:

- Expected match version
- Unique idempotency key
- Target match/question identifier

The API rejects stale transitions with a conflict response and returns the
latest state. This prevents double taps and delayed network requests from
scoring twice.

## Media architecture

Media bytes do not belong in PostgreSQL and should not be written to the
application deployment filesystem.

The database stores metadata and a private object key. When a reserved question
opens, FastAPI returns a short-lived signed playback URL. Flutter downloads or
streams it, validates readiness, and reports `media-ready`. Only then does the
backend set the deadline.

Media processing should validate:

- MIME type and file signature
- Maximum size and duration
- Image dimensions
- Audio/video codecs
- Checksum for duplicates
- Generated poster frame for video

Heavy transcoding can be a separate worker later. The first release should
require uploaders to provide web/mobile-compatible formats.

## Railway deployment

- One FastAPI web service built from a Dockerfile
- One managed PostgreSQL database
- Environment variables for database, JWT signing, and object-storage credentials
- Pre-deploy Alembic migration command
- `/health/live` and `/health/ready` endpoints
- Structured logs to stdout
- Automated database backups

Redis is not required for the single-device MVP. Add it only when remote rooms,
distributed locks, or background job queues justify it.
