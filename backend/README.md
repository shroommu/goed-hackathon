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
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_SECRET_KEY=<secret-key>
```

The app now loads `backend/.env` automatically at startup, so `DATABASE_URL`
and related settings are used even when they are not exported in your shell.

If direct Postgres connectivity is unavailable (for example IPv4-only runtime
without Supabase IPv4 add-on), `GET /resources` and `GET /resources/<id>`
automatically fall back to Supabase Data API (`/rest/v1`) over HTTPS.

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

## BE-003 Resource Ingestion Commands

Import a resource spreadsheet export (JSON or CSV) with row-level validation reporting:

```bash
flask --app wsgi:app import-resources \
  --file data/starter/resources_starter.json \
  --report /tmp/resources_ingest_report.json
```

Use `--dry-run` to validate without persisting changes:

```bash
flask --app wsgi:app import-resources \
  --file data/starter/resources_starter.json \
  --dry-run
```

Query imported resources by available metadata columns:

```bash
flask --app wsgi:app query-resources --locations Utah --topics funding
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
- `SUPABASE_URL`: Supabase project URL for REST fallback (`https://<project-ref>.supabase.co`)
- `SUPABASE_SECRET_KEY`: server-side key used by REST fallback
- `SUPABASE_REST_TIMEOUT_SECONDS`: timeout for REST fallback requests (default: `10`)

## Endpoints

- `GET /health`
  - Returns JSON:

```json
{
  "status": "ok",
  "build_version": "1.0.0",
  "environment": "production"
}
```

- `GET /resources`
  - Query params:
    - `page` (optional, default `1`, minimum `1`)
    - `per_page` (optional, default `20`, minimum `1`, maximum `100`)
    - `communities` (optional substring filter)
    - `industries` (optional substring filter)
    - `locations` (optional substring filter)
    - `topics` (optional substring filter)
    - `search` (optional text search across title/description/taxonomy fields)
  - Returns JSON:

```json
{
  "items": [
    {
      "id": 1,
      "title": "Silicon Slopes Community",
      "description": "Utah startup ecosystem events, networking, and community resources.",
      "communities": "community; events; startups",
      "industries": "Community",
      "locations": "Utah",
      "topics": "networking; community; events; startups",
      "link": "https://siliconslopes.com",
      "email": null
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 1,
    "total_pages": 1
  },
  "filters": {
    "communities": null,
    "industries": null,
    "locations": "Utah",
    "topics": null,
    "search": null
  }
}
```

- `GET /resources/<resource_id>`
  - Returns JSON:

```json
{
  "item": {
    "id": 1,
    "title": "Silicon Slopes Community",
    "description": "Utah startup ecosystem events, networking, and community resources.",
    "communities": "community; events; startups",
    "industries": "Community",
    "locations": "Utah",
    "topics": "networking; community; events; startups",
    "link": "https://siliconslopes.com",
    "email": null
  }
}
```

### Error Response Contract

All BE-006 endpoints return errors in a consistent format:

```json
{
  "error": {
    "code": "invalid_query_parameter",
    "message": "'page' must be greater than or equal to 1.",
    "details": {
      "field": "page",
      "value": "0"
    }
  }
}
```

Additional code used by resource endpoints:
- `resource_not_found`

- `GET /companies`
  - Query params:
    - `page` (optional, default `1`, minimum `1`)
    - `per_page` (optional, default `20`, minimum `1`, maximum `100`)
    - `sector` (optional substring filter)
    - `size` (optional enum: `micro`, `small`, `medium`, `large`, `enterprise`)
    - `stage` (optional enum: `idea`, `pre-seed`, `seed`, `series-a`, `series-b`, `series-c`, `growth`, `late-stage`, `public`, `unknown`)
    - `hiring_status` (optional enum: `hiring`, `selective`, `not_hiring`, `unknown`)
    - `location` (optional substring filter against address/location fields)
  - Returns JSON:

```json
{
  "items": [
    {
      "id": 1,
      "name": "Acme Robotics",
      "website": "https://example.com/acme-robotics",
      "employee_count": 48,
      "size": "small",
      "sector": "Robotics",
      "stage": "series-a",
      "hiring_status": "hiring",
      "year_founded": 2020,
      "linkedin_url": "https://www.linkedin.com/company/acme-robotics",
      "description": "Builds warehouse automation tooling for logistics teams.",
      "address": "2400 Foothill Dr, Salt Lake City, UT, 84109",
      "location": {
        "city": "Salt Lake City",
        "county": "Salt Lake",
        "state": "UT",
        "postal_code": "84109",
        "latitude": 40.7243,
        "longitude": -111.8227
      },
      "job_postings": [
        "https://example.com/acme-robotics/jobs"
      ],
      "photo_gallery": []
    }
  ],
  "mindmap": {
    "levels": ["sector", "stage", "company"],
    "sectors": [
      {
        "name": "Robotics",
        "stages": [
          {
            "name": "series-a",
            "companies": [
              {
                "id": 1,
                "name": "Acme Robotics"
              }
            ]
          }
        ]
      }
    ]
  },
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 1,
    "total_pages": 1
  },
  "filters": {
    "sector": "Robotics",
    "size": "small",
    "stage": "series-a",
    "hiring_status": "hiring",
    "location": "Salt Lake"
  }
}
```

- `GET /companies/<company_id>`
  - Returns JSON:

```json
{
  "item": {
    "id": 1,
    "name": "Acme Robotics",
    "website": "https://example.com/acme-robotics",
    "employee_count": 48,
    "size": "small",
    "sector": "Robotics",
    "stage": "series-a",
    "hiring_status": "hiring",
    "year_founded": 2020,
    "linkedin_url": "https://www.linkedin.com/company/acme-robotics",
    "description": "Builds warehouse automation tooling for logistics teams.",
    "address": "2400 Foothill Dr, Salt Lake City, UT, 84109",
    "location": {
      "city": "Salt Lake City",
      "county": "Salt Lake",
      "state": "UT",
      "postal_code": "84109",
      "latitude": 40.7243,
      "longitude": -111.8227
    },
    "job_postings": [
      "https://example.com/acme-robotics/jobs"
    ],
    "photo_gallery": []
  }
}
```

Additional codes used by company endpoints:
- `company_not_found`
- `companies_not_found`
