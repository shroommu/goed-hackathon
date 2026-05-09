# Vercel Deployment Guide - Monorepo Setup

This project uses separate Vercel projects for frontend and backend, unified under a single domain.

## Architecture

- **Frontend**: Next.js app (main domain)
- **Backend**: Flask API with `/api` prefix (proxied through frontend)
- **Routing**: `/api/*` routes proxy to backend's `/api/*` endpoints

All backend routes are prefixed with `/api`:
- `/api/health`
- `/api/companies`
- `/api/resources`
- `/api/admin/*`

## Setup Steps

### 1. Deploy Backend Project

1. Go to [Vercel Dashboard](https://vercel.com/new)
2. Import your Git repository
3. Configure the project:
   - **Root Directory**: `backend`
   - **Framework Preset**: Other
   - **Build Command**: (leave empty)
   - **Output Directory**: (leave empty)
4. Add environment variables (SUPABASE_URL, SUPABASE_ANON_KEY, etc.)
5. Deploy and note the project URL (e.g., `your-backend-project.vercel.app`)

### 2. Deploy Frontend Project

1. Go to [Vercel Dashboard](https://vercel.com/new) again
2. Import the same Git repository (create a new project)
3. Configure the project:
   - **Root Directory**: `frontend`
   - **Framework Preset**: Next.js
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`
4. Add environment variables (if any)
5. Deploy

### 3. Assign Your Custom Domain

1. Go to your frontend project settings
2. Navigate to **Domains**
3. Add your custom domain (e.g., `yourdomain.com`)

### 4. Configure CORS (Backend)

Ensure your Flask backend allows requests from your frontend domain. Check `app/config.py` or wherever CORS is configured.

## Local Development

Both services run independently with the `/api` prefix:

```bash
# Backend (serves at http://localhost:5000/api/*)
cd backend
source .venv/bin/activate
flask run

# Frontend (Next.js rewrites proxy /api/* to backend)
cd frontend
npm run dev
```

**No environment variables needed!** Next.js rewrites in `next.config.mjs` automatically proxy `/api/*` to `http://127.0.0.1:5000/api/*` during development.

## Troubleshooting

- **404 on API routes**: 
  - Verify the backend URL in vercel.json is correct
  - Ensure backend routes all have `/api` prefix
  - Check that rewrite destination includes `/api/:path*`
- **CORS errors**: Update CORS settings in backend to allow your frontend domain
- **Build failures**: Check build logs in Vercel dashboard
- **Environment variables**: Ensure they're set in both projects on Vercel (backend needs Supabase vars)
- **Local dev issues**: 
  - Ensure backend is running on port 5000
  - Check `next.config.mjs` rewrites point to correct backend URL
  - Frontend always uses relative `/api/*` paths

## Git Workflow

Both projects will deploy automatically on push. Vercel detects changes in `frontend/` and `backend/` directories and triggers the appropriate project builds.
