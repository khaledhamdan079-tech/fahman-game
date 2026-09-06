# Fahman backend

This directory will contain the Python FastAPI service.

The backend will own authentication, eligible-question selection, match state,
turn validation, lifeline validation, scoring, media authorization, question
usage, and match history. Flutter must never calculate authoritative scores or
advance the turn without a successful API response.

The backend now includes the application package, PostgreSQL models and
migrations, Google authentication boundary, category availability, atomic
question reservation, match commands, lifelines, idempotent scoring, history,
signed multimedia playback, Docker packaging, and pytest coverage.

## Local setup

```bash
python -m venv .venv
.venv/Scripts/activate
python -m pip install -e ".[dev]"
copy .env.example .env
alembic upgrade head
python -m uvicorn app.main:app --reload
```

The default development database is a local SQLite file so the API can start
without external services. Set `DATABASE_URL` to an async PostgreSQL URL for
production-like development.

## Importing questions

Set `ADMIN_API_KEY`, upload any referenced media into the private object
storage, then send a validated JSON batch to the protected endpoint:

```bash
curl -X POST http://localhost:8000/v1/admin/import/questions \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: $ADMIN_API_KEY" \
  --data-binary @examples/questions.sample.json
```

The importer creates missing categories and media metadata, skips exact
category/prompt/points duplicates, and can publish immediately or save the
batch as drafts. Every question must contain one correct option matching
`answer_ar`; non-text questions must include matching media metadata.

For a new private media file, upload and verify it first:

```bash
python scripts/upload_media.py ./engine.mp3 --kind audio --duration-ms 8000
```

The command hashes the file, requests a server-owned storage key, uploads with
the required signed headers, and completes verification. Copy the returned
`media_asset_id` into the question JSON. Images require `--width` and
`--height`; audio requires `--duration-ms`; video requires all three.
