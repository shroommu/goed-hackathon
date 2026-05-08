# Backend (Flask)

This backend implements BE-001 with:
- Flask app bootstrap for local and production modes
- Environment-based configuration
- Health endpoint with status and build version

## Requirements

- Python 3.11+

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
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
