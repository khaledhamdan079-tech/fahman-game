# Railway deployment

Railway's legacy config-as-code files are deprecated for new services, so the
first deployment uses a Dockerfile plus service settings.

## Service settings

1. Push the repository to GitHub and create a Railway project.
2. Add a PostgreSQL service.
3. Add the application repository as another service.
4. Set the application service Root Directory to `/backend`.
5. Railway will detect `backend/Dockerfile` automatically from that root.
6. Set the pre-deploy command to `alembic upgrade head`.
7. Set the health-check path to `/health/ready`.
8. Generate a public domain after the deployment succeeds.

## Required variables

- `APP_ENV=production`
- `DATABASE_URL=${{Postgres.DATABASE_URL}}`
- `JWT_SECRET` with at least 32 random bytes
- `GOOGLE_CLIENT_IDS` as comma-separated Android, iOS, and Web OAuth client IDs
- `ADMIN_API_KEY` as a long random secret for protected catalogue imports
- `CORS_ORIGINS` as comma-separated allowed web origins
- `MEDIA_BUCKET` for the private S3-compatible bucket
- `MEDIA_ENDPOINT_URL` for providers such as Cloudflare R2 (omit for AWS S3)
- `MEDIA_REGION` (defaults to `auto`)
- `MEDIA_ACCESS_KEY_ID`
- `MEDIA_SECRET_ACCESS_KEY`
- `MEDIA_SIGNED_URL_SECONDS` (defaults to 600)
- `MEDIA_UPLOAD_URL_SECONDS` (defaults to 900)
- `MEDIA_MAX_IMAGE_BYTES` (defaults to 10 MiB)
- `MEDIA_MAX_AUDIO_BYTES` (defaults to 25 MiB)
- `MEDIA_MAX_VIDEO_BYTES` (defaults to 100 MiB)

Railway supplies `PORT`; `python -m app` reads it automatically.

The application normalizes Railway's `postgresql://` URL to the asyncpg
`postgresql+asyncpg://` dialect.

Media files must stay private; the API returns short-lived signed playback URLs
only for media belonging to the signed-in user's open or revealed question.
Configure the bucket's CORS policy from `examples/bucket-cors.json` if uploads
will run from a browser-based operator tool. Replace its placeholder origin.
