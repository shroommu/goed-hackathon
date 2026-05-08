# Backend (Flask)

This backend implements BE-001 with:
- Flask app bootstrap for local and production modes
- Environment-based configuration
- Health endpoint with status and build version

This backend now includes BE-002 foundations with:
- Core relational schema for resources, companies, profiles, recommendations, claims, verification events, and media
- Postgres/Supabase migration SQL
- Seed CLI command for starter data packs

## Requirements

- Python 3.11+

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set your Supabase Postgres URL in `.env`:

```bash
DATABASE_URL=postgresql://postgres.<project-ref>:<password>@<host>:5432/postgres
DB_SSLMODE=require
```

## Run locally (development)

```bash
export APP_ENV=local
python wsgi.py
```

Health check:

```bash
curl http://localhost:5000/health
```

## Apply BE-002 Schema Migration

Run the migration SQL directly against your Supabase database:

```bash
psql "$DATABASE_URL" -f db/migrations/0001_be002_core_schema.sql
```

## Seed Starter Data Packs

Starter files are in `data/starter/` and can be loaded with:

```bash
flask --app wsgi:app seed-starter-data
```

You can also provide custom paths (JSON or CSV):

```bash
flask --app wsgi:app seed-starter-data \
  --resources data/starter/resources_starter.json \
  --companies data/starter/companies_starter.json
```

## Run in production mode

```bash
export APP_ENV=production
export BUILD_VERSION=1.0.0
export PORT=8000
gunicorn --bind 0.0.0.0:${PORT} wsgi:app
```

## Environment Variables

- `APP_ENV`: `local` or `production` (default: `local`)
- `BUILD_VERSION`: build identifier returned by `/health` (default: `dev`)
- `HOST`: bind host for local run (default: `0.0.0.0`)
- `PORT`: bind port (default: `5000` local)
- `DATABASE_URL`: SQLAlchemy database URL (Supabase/Postgres)
- `DB_SSLMODE`: SSL mode for Postgres connections (recommended: `require`)

## Endpoint

- `GET /health`
  - Returns JSON:

```json
{
  "status": "ok",
  "build_version": "1.0.0",
  "environment": "production"
}
```
