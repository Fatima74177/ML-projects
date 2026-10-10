# SECURITY.md — EEF Platform

## Authentication & Authorization
- **JWT** (HS256), signed with `JWT_SECRET` (env-provided, never hardcoded —
  `.env.example` ships an obviously-fake placeholder and the README instructs
  rotating it before any real deployment).
- **Password hashing:** bcrypt via the `bcrypt` library directly (not
  passlib, to sidestep a known passlib/bcrypt≥4 incompatibility). Never
  stores or logs plaintext passwords.
- **RBAC:** `ADMIN` / `ANALYST` / `VIEWER`, enforced with FastAPI dependency
  injection (`require_admin`, `require_analyst`, `require_viewer`) on every
  route that needs it — verified by `test_auth.py::test_viewer_cannot_run_verification`.

## Input Validation & File Security
- Every upload passes through `validators.validate_and_read()`: extension
  allow-list, non-empty check, size cap (`MAX_UPLOAD_SIZE`), and a magic-byte
  signature sniff — a `.txt` file renamed to `.png` is rejected.
- Filenames are **never trusted**: `secure_filename()` generates a UUID-based
  internal name before any disk write; uploads are stored under
  `UPLOAD_DIRECTORY`, outside any executable code path.

## Injection & Transport
- All database access goes through SQLAlchemy's ORM/parameterized queries —
  no raw string-interpolated SQL anywhere in the codebase.
- CORS is an explicit allow-list (`CORS_ORIGINS`), not `*`.
- Structured error responses never leak stack traces; the generic exception
  handler in `main.py` logs the real error server-side and returns a fixed,
  safe `INTERNAL_ERROR` message to the client.

## Rate Limiting
- `RATE_LIMIT_PER_MINUTE` is configured; when `REDIS_ENABLED=true` this backs
  a per-client sliding window in Redis. When Redis is disabled (default local
  dev), health checks report `"status": "disabled"` honestly rather than
  silently no-op-ing without saying so.

## Secrets Management
- All secrets are environment variables (`.env`, never committed).
  `.env.example` contains only obviously-fake placeholders.
- `JWT_SECRET`, `NEO4J_PASSWORD`, database credentials — none are hardcoded
  in source.
- For a real deployment: swap `.env` for a managed secrets store (AWS
  Secrets Manager, HashiCorp Vault, etc.) — not included here since this is a
  local-development prototype.

## Audit Logging
- Every sensitive action (`LOGIN`, `IDENTITY_VERIFICATION`,
  `DOCUMENT_ANALYSIS`, `FACE_MATCH`, `LIVENESS_CHECK`, `DEEPFAKE_ANALYSIS`,
  `VOICE_ANALYSIS`, `COPILOT_QUERY`, etc.) is recorded via
  `audit_service.record()` with actor, action, resource, result, IP, and
  metadata.
- The audit API surface is **read-only** (`GET /audit` only) — there is no
  update/delete endpoint, by design, so logs are immutable from normal
  application use.

## Privacy
- **Raw biometric embeddings are never returned** by any API response — only
  derived similarity scores, match decisions, and explanations.
- Voice transcripts and OCR text are stored (needed for the analyst
  workflow) but are clearly labeled prototype/placeholder outputs where
  applicable.
- **Data minimization:** the seed/demo dataset uses entirely synthetic
  people; every demo document image is watermarked "DEMO — NOT A REAL
  IDENTITY DOCUMENT" in its generation script.
- **Retention:** not automated in this prototype; a production deployment
  should add a scheduled purge job keyed off `created_at` per a configured
  retention policy (documented here as a known gap, not implemented).
- **Access control on sensitive data:** all identity/biometric/fraud
  endpoints require `ANALYST` or `ADMIN` roles; `VIEWER` gets dashboard/health
  read access only.

## What This Prototype Does NOT Include (Be Aware)
- No production TLS termination config (assumed to sit behind a real load
  balancer/ingress in any real deployment — Nginx here is a reverse proxy for
  local multi-service routing only).
- No WAF / DDoS protection.
- No automated dependency vulnerability scanning pipeline (would add
  `pip-audit` / `npm audit` / Trivy in CI for a production fork).
- No formal penetration test has been performed.

## Reporting
This is a case-study prototype; there is no production support channel. If
adapting this codebase for real use, run a full security review (dependency
audit, secrets rotation, TLS, pen test) before handling real PII/biometric
data.
