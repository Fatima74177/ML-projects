# Render Deployment Guide

This repository is prepared for a Render deployment using two services:

1. `eef-backend` - FastAPI backend
2. `eef-frontend` - React + Vite static frontend

## 1) Push to GitHub

Push the repository to GitHub before creating Render services.

## 2) Create the backend service on Render

- New > Web Service
- Connect GitHub repository
- Select the repository
- Name: `eef-backend`
- Root Directory: `backend`
- Runtime: Python
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app.main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`
- Health Check Path: `/health`

Set environment variables:

- `ENV=production`
- `DEBUG=false`
- `DATABASE_URL=sqlite:///./eef_demo.db`
- `REDIS_ENABLED=false`
- `KAFKA_ENABLED=false`
- `NEO4J_ENABLED=false`
- `JWT_SECRET=<generate a strong secret>`
- `CORS_ORIGINS=https://eef-frontend.onrender.com`

## 3) Create the frontend service on Render

- New > Web Service
- Connect the same GitHub repository
- Name: `eef-frontend`
- Root Directory: `frontend`
- Runtime: Static Site
- Build Command: `npm install && npm run build`
- Publish Directory: `dist`

Set environment variables:

- `VITE_API_BASE_URL=https://eef-backend.onrender.com/api/v1`

## 4) Final step

After the backend service is live, replace the temporary frontend CORS value with the real frontend URL if it differs from `https://eef-frontend.onrender.com`.

This setup is designed for a simple Render deployment without Docker and without local-only URLs.
