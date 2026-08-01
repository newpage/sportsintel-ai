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
