# SportsIntel AI

AI-assisted sports analytics and strategy exploration platform, initially focused on NFL intelligence and Last Man Standing (LMS) strategy.

## First release goals

- Clean NFL data lake foundation
- Canonical team, game, season, week, venue, player, and injury models
- LMS pools, entries, picks, used-team tracking, and recommendations
- FastAPI API on port 8300
- Next.js web application on port 3300
- PostgreSQL and Redis internal to Docker
- Apache deployment at `sportsintel.discovera.ai`

## Start locally or on the Linux server

```bash
cp .env.example .env
docker compose up --build -d
```

Check:

```bash
curl http://127.0.0.1:8300/health
curl http://127.0.0.1:8300/api/v1/platform/readiness
curl -I http://127.0.0.1:3300
```

## Seed the NFL/LMS foundation

```bash
docker compose exec worker   celery -A app.workers.celery_app.celery   call app.workers.tasks.seed_foundation
```

## Public deployment

Apache proxies:

- `/api/`, `/docs`, `/openapi.json`, `/health` → `127.0.0.1:8300`
- `/` → `127.0.0.1:3300`

See `infrastructure/apache/sportsintel.discovera.ai.conf`.

## Create the first administrator

```bash
docker compose exec api python -m app.cli.create_admin   --email admin@discovera.ai
```

Then open:

- Login: `https://sportsintel.discovera.ai/login`
- Admin: `https://sportsintel.discovera.ai/admin`

Admin APIs:

- `GET /api/v1/admin/overview`
- `GET /api/v1/admin/users`
- `GET /api/v1/admin/provider-runs`
- `GET /api/v1/admin/audit-logs`

## Sprint 1.2 security foundation

- Argon2 password hashing via pwdlib
- 15-minute access tokens
- Rotating 30-day refresh tokens with reuse-family revocation
- Redis-backed login throttling
- Temporary account lockout
- Email verification tokens
- Password-reset tokens
- Optional TOTP MFA
- Authentication audit logs

Because development compatibility is not required, recreate existing users/admins after resetting the database.

## Provider Registry

Open the provider console:

```text
https://sportsintel.discovera.ai/admin/providers
```

Run the bundled NFL team provider through the API:

```bash
curl -X POST   https://sportsintel.discovera.ai/api/v1/admin/providers/nfl.demo/run/TEAM   -H "Authorization: Bearer $TOKEN"
```

See `docs/providers.md` for the provider contract and licensing metadata.
