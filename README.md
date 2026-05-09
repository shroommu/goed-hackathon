# GOED Hackathon

Web platform for the Utah Governor’s Office of Economic Development (GOED): a **Founder Resource Navigator** for personalized resource discovery and a **Utah Startup Map** for browsing the ecosystem.

See [`project_requirements.md`](project_requirements.md) for full goals, acceptance criteria, and non-negotiables.

## Live Site

**[Live Site](http://goed.alexakruckenberg.com)**

## Map repo

Related map dataset and static assets live in the companion repository: **[map repo](https://github.com/jonathanmwagstaff/HackathonGOED)**.

## Repository layout

| Path | Description |
|------|-------------|
| [`frontend/`](frontend/) | Next.js app (map UI, resource flows) |
| [`backend/`](backend/) | Flask API, Postgres/Supabase schema and tooling |

## Quick start

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

**Backend**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then configure DATABASE_URL / Supabase keys
export APP_ENV=local
python wsgi.py
```

Details: [`backend/README.md`](backend/README.md).
