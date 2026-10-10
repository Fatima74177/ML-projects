# DEPLOYMENT.md — EEF Platform

## Local Development (Docker Compose — recommended)

```bash
git clone <repo> && cd eef-platform
cp .env.example .env
docker compose up --build
```

- Backend: http://localhost:8000 (`/docs`, `/redoc`, `/health`)
- Frontend: http://localhost:5173
- Combined via Nginx: http://localhost:8080
- Postgres: localhost:5432 (`eef`/`eef_dev_password`/`eef`)
- Redis: localhost:6379
- Neo4j Browser (if enabled): http://localhost:7474

The `backend` service's `docker-entrypoint.sh`:
1. Polls Postgres until reachable (30 retries, 2s apart)
2. Runs `alembic upgrade head`
3. Seeds demo data **only if the `identities` table is empty**
4. Starts `uvicorn`

Re-running `docker compose up` on an already-seeded volume is safe — it will
not re-seed or duplicate demo data.

## Rebuilding After Code Changes

```bash
docker compose up --build backend   # backend only
docker compose up --build frontend  # frontend only
docker compose down -v              # full reset, including volumes (drops all data)
```

## Scaling Notes (Prototype -> Production Path)

This is a **functional prototype tested on demo-scale data**. The
architecture is designed to scale horizontally, but the following would be
required for a real production rollout -- none of it is implemented here:

1. **Backend:** run multiple stateless `backend` replicas behind a load
   balancer (the JWT auth is already stateless, so this requires no session
   affinity).
2. **Database:** move to managed Postgres with read replicas; add connection
   pooling (PgBouncer).
3. **Async pipeline:** flip `KAFKA_ENABLED=true` and implement the consumer
   workers in `backend/app/workers/` for the heavy OCR/face/deepfake stages,
   so the HTTP request returns immediately with a `PROCESSING` status and a
   webhook/poll pattern delivers the final result.
4. **Graph:** flip `NEO4J_ENABLED=true` and point `graph_service` at a
   managed Neo4j (Aura or a clustered self-hosted deployment) once
   relationship volume exceeds what a single-node NetworkX rebuild-per-query
   can handle.
5. **File storage:** move `UPLOAD_DIRECTORY` to object storage (S3/GCS) with
   signed URLs instead of a local Docker volume.
6. **Secrets:** replace `.env` with a managed secrets store.
7. **TLS/Ingress:** put a real ingress/load balancer with TLS termination in
   front of Nginx (or replace Nginx entirely with a cloud load balancer).
8. **Observability:** ship the structured JSON logs (already request-ID
   tagged) to a real log aggregator (ELK/Datadog/CloudWatch); add Prometheus
   metrics around the `Timer` instrumentation already present in
   `identity_service.py`.
9. **Model upgrades:** swap the `HEURISTIC`/`DEMO_SIMULATION` components for
   real trained models once a GPU-enabled, internet-reachable deployment
   environment is available (see README's Model Honesty section for the
   documented swap points in each service file).

## Environment-Specific Config

| Setting | Local dev | Docker Compose | Production (not included) |
|---|---|---|---|
| `DATABASE_URL` | SQLite | Postgres (compose service) | Managed Postgres, pooled |
| `REDIS_ENABLED` | false (optional) | true | true, managed Redis |
| `KAFKA_ENABLED` | false | false (flip to enable) | true |
| `NEO4J_ENABLED` | false | false (flip to enable) | true |
| `JWT_SECRET` | dev placeholder | dev placeholder in `.env` | secrets manager |
| `DEBUG` | true | true | **false** |

## Health Checks for Orchestration

Every dependency has its own probe so a container orchestrator can gate
traffic correctly: `GET /health`, `/health/database`, `/health/redis`,
`/health/kafka`, `/health/neo4j`, `/health/models`. The Docker `HEALTHCHECK`
directive in `backend/Dockerfile` uses `/health`.
