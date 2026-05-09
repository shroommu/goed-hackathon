# Vercel Deployment Guide - Monorepo Setup

This project uses separate Vercel projects for frontend and backend, unified under a single domain.

## Architecture

- **Frontend**: Next.js app (main domain)
- **Backend**: Flask API (proxied through frontend)
- **Routing**: `/api/*` and `/_/backend/*` routes proxy to backend

## Setup Steps

### 1. Deploy Backend Project

1. Go to [Vercel Dashboard](https://vercel.com/new)
2. Import your Git repository
3. Configure the project:
   - **Root Directory**: `backend`
   - **Framework Preset**: Other
   - **Build Command**: (leave empty)
   - **Output Directory**: (leave empty)
4. Add environment variables (if any)
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

### 3. Update Frontend Configuration

Edit `/vercel.json` in the root and replace `"your-backend-project.vercel.app"` with your actual backend Vercel URL:

```json
{
    "buildCommand": "cd frontend && npm run build",
    "outputDirectory": "frontend/.next",
    "framework": "nextjs",
    "rewrites": [
        {
            "source": "/api/:path*",
            "destination": "https://YOUR-ACTUAL-BACKEND-URL.vercel.app/api/:path*"
        },
        {
            "source": "/_/backend/:path*",
            "destination": "https://YOUR-ACTUAL-BACKEND-URL.vercel.app/:path*"
        }
    ]
}
```

### 4. Assign Your Custom Domain

1. Go to your frontend project settings
2. Navigate to **Domains**
3. Add your custom domain (e.g., `yourdomain.com`)

### 5. Configure CORS (Backend)

Ensure your Flask backend allows requests from your frontend domain. Check `app/config.py` or wherever CORS is configured.

## Local Development

Both services can run independently:

```bash
# Backend
cd backend
source .venv/bin/activate
flask run

# Frontend
cd frontend
npm run dev
```

## Troubleshooting

- **404 on API routes**: Verify the backend URL in vercel.json is correct
- **CORS errors**: Update CORS settings in backend to allow your frontend domain
- **Build failures**: Check build logs in Vercel dashboard
- **Environment variables**: Ensure they're set in both projects on Vercel

## Git Workflow

Both projects will deploy automatically on push. Vercel detects changes in `frontend/` and `backend/` directories and triggers the appropriate project builds.
