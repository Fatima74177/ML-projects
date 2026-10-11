# Render Deployment Guide

The Render blueprint deploys one Docker web service. FastAPI serves both the
React + Vite frontend and the API, so the app and API share one Render URL.

## 1) Push to GitHub

Push the repository to GitHub before creating Render services.

## 2) Create the Render service

- In Render, choose **New > Blueprint** and connect the GitHub repository.
- Render reads `render.yaml` and creates one Docker web service named `eef-platform`.
- The Docker build compiles the frontend and packages it with the FastAPI backend.
- Set `JWT_SECRET` to a strong secret in the Render service environment.
- Keep the configured demo defaults for the other environment variables, or replace `DATABASE_URL` with a managed production database.

The deployed frontend is available at the service URL. API requests use that same
origin under `/api/v1`; API documentation and health checks remain at `/docs` and
`/health`. No frontend API URL or cross-origin CORS setting is needed.
