# Delivery roadmap

Adding image, audio, and video questions increases the expected MVP schedule to
approximately 5–7 weeks for one full-time developer, excluding the time needed
to license and author a large question catalogue.

## Phase 1 — Rules, UX, and architecture

Status: complete

- Product rules and explicit assumptions
- Text, image, audio, and video behavior
- Lifeline timing
- Screen flow and recovery states
- System architecture
- Database model
- API boundary

## Phase 2 — Backend foundation

Estimate: 4–6 days

Status: complete

- FastAPI project and dependency management
- Settings and environment validation
- PostgreSQL connection and session management
- SQLAlchemy models and Alembic migrations
- Health endpoints
- Private installation-identity boundary
- JWT access/refresh sessions
- pytest, Ruff, and type checking
- Railway Docker configuration

## Phase 3 — Match engine and media authorization

Estimate: 7–10 days

Status: complete

- Category eligibility queries
- Atomic question reservation
- Match/question state machine
- Lifelines and scoring
- Idempotent commands and version conflicts
- User question usage
- Event log and recovery
- Media metadata and signed playback URLs
- Media-ready and play-count commands

## Phase 4 — Flutter application

Estimate: 7–10 days

Status: complete — shell, authentication boundary, manual/random category
setup, board, question presentation, multimedia playback, timer, lifelines,
reveal, scoring, recovery, history, and final results complete

- Arabic RTL theme and navigation
- Automatic device session
- Category and team setup
- Game board
- Text/image/audio/video question views
- Timer and media preloading
- Reveal, adjudication, scoring, and lifelines
- Active-match recovery and history
- Final result and winner presentation

## Phase 5 — Content pipeline and quality

Estimate: 5–8 days

Status: in progress — validated imports, private upload verification, backend
integration coverage, and a complete match simulation are complete

- Validated question import
- Private media uploads
- Codec, duration, size, and checksum validation
- Video poster frames
- Loading/error/replacement flows
- Backend integration tests
- Flutter widget/golden tests
- Full match end-to-end test
- Arabic copy and device QA

## Phase 6 — Railway release

Estimate: 2–3 days

Status: prepared — Docker deployment, production validation, health checks, and
the launch checklist are ready; live infrastructure is not provisioned yet

- Production services and secrets
- Migrations and health checks
- Logging and backup checks
- Closed beta catalogue
- Crash and API monitoring
- Launch checklist

## MVP exit criteria

- A fresh installation creates and restores its user without sign-in.
- A complete 3–7 category match can be played and resumed.
- Questions do not repeat for that user.
- Text, image, audio, and video questions all work on target devices.
- Buffering does not consume answer time.
- Lifelines cannot be reused or activated at invalid times.
- Scores and turns remain correct under duplicate requests.
- Match history preserves the exact played content and outcome.
- Copyright ownership or licensing is documented for every media asset.
