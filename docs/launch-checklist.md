# Railway launch checklist

## Before deployment

- Create separate Railway PostgreSQL and API services.
- Create a private S3-compatible bucket; never expose question media publicly.
- Configure the bucket CORS rules only for trusted operator origins.
- Verify that the secure installation identity survives a normal app update.
- Generate independent random values for `JWT_SECRET` and `ADMIN_API_KEY`.
- Confirm every image, audio clip, and video has documented usage rights.

## API service

- Set the Railway service root to `/backend`.
- Use the repository Dockerfile.
- Confirm the container's automatic `alembic upgrade head` step succeeds.
- Set the health-check path to `/health/ready`.
- Configure every required variable in `backend/RAILWAY.md`.
- Verify `/health/live` and `/health/ready` after deployment.
- Confirm production does not expose `/docs` or `/redoc`.

## Media smoke test

- Upload one image, one audio clip, and one video with
  `backend/scripts/upload_media.py`.
- Import questions that reference the returned `media_asset_id` values.
- Start a match and confirm playback URLs expire and cannot be requested before
  their question is open.
- Verify a mismatched size, MIME type, or checksum metadata is rejected.

## Flutter release

- Build with the deployed endpoint using
  `--dart-define=API_BASE_URL=https://fahman-game-production.up.railway.app/v1`.
- Keep Google client IDs only during the existing-user migration window.
- Test Arabic layout on a small phone, large phone, tablet, and web browser.
- Play a complete three-category match with every media type and all lifelines.
- Interrupt an active question, relaunch, and verify recovery.

## Operations

- Enable PostgreSQL backups and test a restore before launch.
- Add API error and latency monitoring without logging tokens or answer data.
- Rotate the admin key if it is ever shared outside the operator team.
- Begin with a closed beta catalogue and review question disputes regularly.
