# فهمان — Fahman

An Arabic, team-based trivia game for Flutter, backed by a Python API and
deployed on Railway.

The first release is designed for two
teams sharing one host device. Players choose categories, take turns selecting
questions, use one-time lifelines, and build a permanent match history.

Questions may be text, image, audio, or video. Examples include identifying a
car from its engine sound, recognizing a place from a photo, or completing a
licensed scene.

## Planned stack

- Frontend: Flutter, Riverpod, go_router, Dio
- Backend: Python, FastAPI, SQLAlchemy, Alembic
- Database: PostgreSQL
- Authentication: Google Sign-In with server-side ID-token verification
- Media: S3-compatible object storage with short-lived playback URLs
- Deployment: Railway

## Repository layout

```text
backend/     Python API and game engine
frontend/    Flutter application
docs/        Product, UX, architecture, data, API, and delivery specifications
```

## Phase 1 documents

- [Product rules](docs/product-spec.md)
- [UX and screen flow](docs/ux-flow.md)
- [Architecture](docs/architecture.md)
- [Data model](docs/data-model.md)
- [API contract](docs/api-contract.md)
- [Delivery roadmap](docs/roadmap.md)

## Current status

Phases 1–3 are complete and the main Phase 4 journey is implemented. The
authoritative backend is paired with an Arabic RTL Flutter app that includes
Google authentication, secure rotating sessions, manual or random category
setup, live match creation, resumable rounds, match history, final results, the
responsive board, and playable text/image/audio/video questions with timer,
lifelines, reveal, and scoring. Protected question import and private direct
media uploads are also available, including metadata verification before an
asset becomes playable. The backend test suite now simulates a complete
three-category match. The next implementation step is video poster/codec
processing, Flutter golden/device QA, and provisioning the live Railway stack.
