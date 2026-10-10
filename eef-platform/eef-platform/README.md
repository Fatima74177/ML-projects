# EEF — Enterprise Digital Identity, Trust & Deepfake Detection Platform

**Ezitech Engineering Framework (EEF), AI-236 — industry case-study prototype.**

A working, end-to-end enterprise digital-trust platform: identity verification,
face matching, liveness/spoof detection, document OCR & fraud checks,
image/video deepfake analysis, voice authentication, transparent trust
scoring, a fraud-intelligence knowledge graph, an evidence-grounded AI
copilot, alerting, audit logging, and an executive dashboard.

> **This is a prototype, not a certified biometric/forensic product.** See
> [Model Honesty & Limitations](#model-honesty--limitations) below — every AI
> result in this platform is labeled `REAL_MODEL`, `HEURISTIC`, or
> `DEMO_SIMULATION` so nothing is ever presented as more certain than it is.

---

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Features](#features)
4. [Technology Stack](#technology-stack)
5. [Folder Structure](#folder-structure)
6. [Installation](#installation)
7. [Docker Setup](#docker-setup)
8. [Environment Variables](#environment-variables)
9. [Demo Credentials](#demo-credentials)
10. [API Documentation](#api-documentation)
11. [Demo Workflow](#demo-workflow)
12. [Model Honesty & Limitations](#model-honesty--limitations)
13. [Security](#security)
14. [Privacy](#privacy)
15. [Testing](#testing)
16. [Troubleshooting](#troubleshooting)
17. [Deployment](#deployment)
18. [Known Limitations](#known-limitations)
19. [Future Improvements](#future-improvements)

---

## Overview

EEF simulates the identity-trust stack a fintech/regulated enterprise would
build: a person uploads a government-style document and a selfie; the
platform runs OCR, face matching, liveness checks, and fraud-signal detection;
combines everything into one transparent trust score; and returns a
`VERIFIED` / `REVIEW_REQUIRED` / `REJECTED` decision with a full, inspectable
explanation. Analysts get a fraud-case workflow, a relationship graph, an
alert center, and an AI copilot that answers questions strictly from real
platform data (never fabricated).

Every stage is a real backend service with real input/output — not a UI mockup.

## Architecture

```
Frontend Dashboard (React/Vite/Tailwind)
        │
        ▼
FastAPI API Gateway  (JWT auth, RBAC, structured errors, request IDs)
        │
        ├── Identity Verification   (orchestrates the full pipeline)
        ├── Face & Liveness         (OpenCV detection + embedding + anti-spoof)
        ├── Document Intelligence   (Tesseract OCR + field extraction)
        ├── Deepfake Detection      (FFT / boundary / compression forensics)
        ├── Voice Authentication    (waveform DSP + placeholder STT)
        ├── Trust Scoring           (transparent weighted formula)
        ├── Fraud Intelligence      (SQL signal detection → FraudCase)
        ├── AI Identity Copilot     (tool-grounded Q&A, never fabricates)
        ├── Alert Center
        └── Audit System            (append-only)
        │
        ▼
PostgreSQL  ── Redis (cache/rate-limit) ── Kafka (optional async) ── Neo4j (optional graph) 
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full component breakdown,
synchronous vs. asynchronous flows, and Mermaid diagrams.

## Features

| Domain | What it does | Endpoint(s) |
|---|---|---|
| Auth & RBAC | JWT login, bcrypt hashing, ADMIN/ANALYST/VIEWER roles | `/api/v1/auth/*` |
| Identity Verification | Full pipeline: OCR→face→liveness→trust→fraud→decision | `/api/v1/identity/verify` |
| Document Intelligence | Real Tesseract OCR, field extraction, anomaly flags | `/api/v1/documents/analyze` |
| Face & Liveness | Face match, active/passive liveness | `/api/v1/face/*` |
| Deepfake Detection | Image/video forensic signal analysis | `/api/v1/deepfake/analyze` |
| Voice Authentication | Real waveform DSP analysis | `/api/v1/voice/analyze` |
| Trust Scoring | Transparent, configurable weighted formula | `/api/v1/trust/*` |
| Fraud Intelligence | Shared device/doc/IP + repeat-failure detection | `/api/v1/fraud/*` |
| Knowledge Graph | NetworkX live graph, Neo4j-ready | `/api/v1/graph/*` |
| AI Copilot | Tool-grounded, evidence-cited Q&A | `/api/v1/copilot/ask` |
| Alert Center | Typed alerts with status workflow | `/api/v1/alerts` |
| Executive Dashboard | Live-computed stats & chart data | `/api/v1/dashboard/*` |
| Audit Log | Immutable, append-only | `/api/v1/audit` |
| Model Registry | Honesty label for every AI component | `/api/v1/models/status` |
| Health Checks | Per-dependency health probes | `/health/*` |

## Technology Stack

**Backend:** Python 3.12, FastAPI, Pydantic, SQLAlchemy, Alembic, PostgreSQL, Redis, Kafka (optional)
**AI/Processing:** OpenCV, Tesseract OCR (pytesseract), NumPy, NetworkX
**Graph:** Neo4j (optional; NetworkX is the default live engine)
**Frontend:** React 18, TypeScript, Vite, Tailwind CSS, Recharts
**Infra:** Docker, Docker Compose, Nginx
**Testing:** Pytest, FastAPI TestClient (37 tests; Tesseract-dependent OCR test skips if Tesseract is absent)

## Folder Structure

```
eef-platform/
├── backend/
│   ├── app/
│   │   ├── main.py                 FastAPI entrypoint
│   │   ├── core/                   config, security, logging, database
│   │   ├── api/routes/             one file per domain
│   │   ├── models/                 SQLAlchemy ORM (single source: _all.py)
│   │   ├── schemas/                Pydantic request/response schemas
│   │   ├── services/               all business logic / AI pipelines
│   │   └── utils/                  image utils, file validators
│   ├── alembic/                    real, autogenerated migration
│   ├── tests/                      37 pytest tests
│   ├── Dockerfile
│   └── docker-entrypoint.sh        wait-for-db → migrate → seed → serve
├── frontend/
│   ├── src/
│   │   ├── pages/                  one file per Section-33 route
│   │   ├── components/, layouts/, hooks/, services/
│   │   └── App.tsx, main.tsx
│   └── Dockerfile
├── neo4j/seed.cypher               graph schema + example Cypher queries
├── data/demo/                      synthetic demo images/docs/video/audio
├── scripts/
│   ├── seed_demo_data.py           generates the full demo dataset
│   ├── download_models.py          documents/attempts optional model downloads
│   └── health_check.py             CLI health check across all services
├── docker-compose.yml
├── .env.example
└── README.md / ARCHITECTURE.md / API_DOCUMENTATION.md / SECURITY.md /
    DEPLOYMENT.md / PRESENTATION.md / DEMO_GUIDE.md
```

## Installation

### Option A — Docker Compose (recommended, full stack)

```bash
git clone <this-repo-or-unzip-the-archive>
cd eef-platform
cp .env.example .env
docker compose up --build
```

Then:
- **Frontend:** http://localhost:5173  (or http://localhost:8080 via Nginx)
- **Backend API:** http://localhost:8000
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Neo4j Browser** (if enabled): http://localhost:7474

The backend container's entrypoint automatically waits for Postgres, runs
Alembic migrations, and seeds demo data on first boot (skipped if data
already exists). The image includes the Tesseract executable required for OCR.

### Option B — Local development (no Docker)

```bash
# Backend
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# Tesseract OCR must be installed on the host: `apt install tesseract-ocr` (Linux) / `brew install tesseract` (macOS)
cp ../.env.example .env   # edit DATABASE_URL to sqlite:///./eef_demo.db for zero-dependency local dev
PYTHONPATH=. python3 ../scripts/seed_demo_data.py
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

## Docker Setup

`docker-compose.yml` starts: `postgres`, `redis`, `zookeeper`, `kafka`,
`neo4j`, `backend`, `frontend`, `nginx`. The backend `depends_on` uses health
checks so it never starts before Postgres/Redis are actually ready. Redis
backs API rate limiting when enabled and falls back to process-local limits
if unavailable. Kafka and Neo4j are provisioned but **disabled by default**
(`KAFKA_ENABLED=false`, `NEO4J_ENABLED=false`). The Kafka worker can consume
`verification.started`, but the HTTP API does not yet publish events. Graph
queries currently use NetworkX; Neo4j is health-checked but is not used as a
graph query backend. These integrations need more work before their flags
should be treated as production-ready.

## Environment Variables

See [`.env.example`](.env.example) for the full list with safe placeholders.
Never commit a real `.env`. Key variables: `DATABASE_URL`, `REDIS_URL`,
`KAFKA_BOOTSTRAP_SERVERS`, `NEO4J_URI` / `NEO4J_USERNAME` / `NEO4J_PASSWORD`,
`JWT_SECRET`, `LLM_API_KEY`, `MODEL_DEVICE`, `UPLOAD_DIRECTORY`, `MAX_UPLOAD_SIZE`.

## Demo Credentials

**Local development only.** Rotate or remove before any non-local deployment.

| Username | Password | Role |
|---|---|---|
| `admin` | `Admin@12345` | ADMIN |
| `analyst` | `Analyst@12345` | ANALYST |
| `viewer` | `Viewer@12345` | VIEWER |

## API Documentation

Full interactive docs at `/docs` (Swagger) and `/redoc` once the backend is
running. A written summary is in [API_DOCUMENTATION.md](API_DOCUMENTATION.md).

## Demo Workflow

See [DEMO_GUIDE.md](DEMO_GUIDE.md) for the full 24-step scripted walkthrough
(login → verification → graph → fraud → deepfake → voice → copilot → audit).

## Model Honesty & Limitations

Every AI-adjacent result carries a `model_type` field:

| Label | Meaning |
|---|---|
| `REAL_MODEL` | A genuine algorithm/engine running on real input (e.g. Tesseract OCR, the trust-scoring formula, SQL-based fraud detection, real waveform DSP). |
| `HEURISTIC` | A deterministic, explainable, non-trained signal-processing method standing in for a deep model whose pretrained weights could not be fetched in this offline build environment (face embedding, liveness, deepfake forensics). |
| `DEMO_SIMULATION` | A labeled placeholder (e.g. the voice transcript, the copilot's default template mode) pending a production integration. |

Check `GET /api/v1/models/status` (also rendered on the Settings page) for the
live, per-component breakdown and the documented swap-in point for each real
model (InsightFace/ArcFace for faces, Whisper for STT, PaddleOCR as an OCR
alternative, a FaceForensics++-trained classifier for deepfakes). **No result
in this platform is ever hardcoded** — heuristic scores are computed from
real pixels/waveforms every time, they are just not claiming to be a trained
neural network where one isn't actually running.

## Security

See [SECURITY.md](SECURITY.md). Summary: JWT auth, bcrypt password hashing,
RBAC, CORS allow-list, file-upload validation (extension + magic-byte sniff +
size cap, never trusting filenames), structured error responses (no stack
traces to clients), parameterized SQL via SQLAlchemy (no injection surface),
and append-only audit logging.

## Privacy

See [SECURITY.md](SECURITY.md#privacy) for data-minimization notes. Raw
biometric embeddings are never returned by any API response; only similarity
scores and decisions are exposed.

## Testing

```bash
cd backend
PYTHONPATH=. python3 -m pytest tests/ -v
```

37 tests cover auth/RBAC, verification, document processing, face matching,
liveness, deepfake (image+video), voice, trust scoring, fraud detection, graph
queries, alerts, audit logging, rate limiting, and negative cases. The real
OCR test is skipped when the external Tesseract executable is unavailable;
the missing-engine fallback is tested separately.

## Troubleshooting

- **`tesseract: command not found`** — install the `tesseract-ocr` system
  package (see Installation); it is not a pip package.
- **Backend can't reach Postgres** — the compose healthcheck should prevent
  this, but if running manually, wait for `pg_isready` before starting the API.
- **Bcrypt/passlib version errors** — this project calls the `bcrypt` library
  directly (not via `passlib`) specifically to avoid a known passlib/bcrypt≥4
  incompatibility.
- **Empty dashboard** — run `scripts/seed_demo_data.py` (the Docker entrypoint
  does this automatically on first boot).

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md).

## Known Limitations

- Face embedding, liveness, and deepfake detection use explainable heuristics,
  not trained neural networks (see [Model Honesty](#model-honesty--limitations)).
- PaddleOCR, InsightFace, YOLO, Whisper, LangGraph, and a vector database are
  not integrated in this prototype. OCR uses Tesseract when installed; other
  model-dependent functions use explicitly labeled prototype baselines.
- Voice transcription is a labeled placeholder (no offline-reachable STT model).
- Redis is used for API rate limiting when enabled; caching and temporary
  verification-state storage are not implemented. Kafka has a consumer but
  no API event producer, and Neo4j is not used for graph queries yet.
- This is tested at demo scale (tens of records), not at enterprise scale —
  see [ARCHITECTURE.md](ARCHITECTURE.md#scale-note) for the explicit scaling
  statement.
- No production TLS/secrets-manager wiring is included; see SECURITY.md.

## Future Improvements

- Swap in InsightFace/ArcFace, a FaceForensics++-trained deepfake classifier,
  and Whisper, once weights can be fetched in the deployment environment.
- Turn on Kafka for the heavy async stages and Neo4j for graph-native queries.
- Add SHAP-based explainability once a real trained scoring model replaces
  the transparent formula (the formula itself is already fully explainable
  without SHAP).
- Multi-tenant support, configurable retention policies, and a proper
  secrets manager (Vault/AWS Secrets Manager) for production secrets.
