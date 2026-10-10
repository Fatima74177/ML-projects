# PRESENTATION.md — EEF Platform (~18 slides)

---
### 1. Title
**EEF — Enterprise Digital Identity, Trust & Deepfake Detection Platform**
Ezitech Engineering Framework, AI-236 — Industry Case Study Prototype

---
### 2. Business Problem
Enterprises onboarding customers/employees remotely face: document fraud,
synthetic identities, deepfake-enabled impersonation, and voice-cloning
fraud — with no unified system to score trust and explain *why* a decision
was made.

---
### 3. Threat Landscape
- Document forgery & template fraud
- Face-swap deepfakes and injection attacks in KYC flows
- Voice cloning for call-center authentication bypass
- Multi-accounting / synthetic identity rings (shared devices, IPs, documents)

---
### 4. Proposed Platform
A single pipeline covering identity verification, biometric checks, document
intelligence, deepfake/voice forensics, transparent trust scoring, fraud
graph analytics, and an evidence-grounded analyst copilot — end to end, not
disconnected demos.

---
### 5. Architecture
Frontend (React) → FastAPI Gateway (JWT/RBAC) → domain services → PostgreSQL
+ optional Redis/Kafka/Neo4j. See ARCHITECTURE.md for full diagrams.

---
### 6. Identity Verification
One endpoint (`POST /identity/verify`) orchestrates OCR → face match →
liveness → fraud signals → trust score → VERIFIED/REVIEW_REQUIRED/REJECTED,
fully audited and alerted automatically.

---
### 7. Face & Liveness
Real OpenCV face detection; HOG-descriptor cosine-similarity matching against
a configurable, documented threshold; active-challenge and passive anti-spoof
liveness — both explicitly labeled prototype-grade.

---
### 8. Document Intelligence
**Real Tesseract OCR** (not simulated) with deterministic field extraction
(name, DOB, document number, dates, nationality), confidence scoring, and
anomaly flags — never claims legal authenticity from OCR alone.

---
### 9. Deepfake Detection
Explainable forensic signals: FFT high-frequency energy, facial-boundary
blending discontinuity, block-level compression inconsistency, and (video)
frame-to-frame consistency/jitter — combined into a probability with named
indicators. Every result: *"AI prototype result — requires human review."*

---
### 10. Voice Authentication
Genuine waveform DSP (duration, RMS, clipping, silence ratio, energy
consistency) computed on the real uploaded audio; transcript is a clearly
labeled placeholder pending a production STT integration.

---
### 11. Trust Scoring
Fully transparent, configurable weighted formula — no black box. Every score
returns its own formula, inputs, and penalty breakdown. Matches the spec's
own Case A (LOW risk) / Case B (CRITICAL risk) test scenarios exactly.

---
### 12. Knowledge Graph
Live NetworkX graph built from the relational database (real
`degree_centrality`/`connected_components` algorithms), Neo4j-ready via a
shared Cypher schema — surfaces shared devices, documents, and IPs across
identities for fraud ring detection.

---
### 13. AI Copilot
Tool-based, evidence-grounded Q&A — every answer cites the actual
database/graph query it used, and explicitly says "insufficient evidence"
rather than fabricating when data doesn't exist.

---
### 14. Executive Dashboard
Live-computed totals, success rate, risk distribution, trust-score histogram,
alert severity breakdown, and verification trend — nothing hardcoded, all
queried from Postgres on every load.

---
### 15. Security
JWT + bcrypt + RBAC, file-upload validation (extension + magic-byte sniff +
size cap, UUID filenames), parameterized SQL throughout, structured error
responses with no leaked stack traces, append-only audit log.

---
### 16. Event-Driven Architecture
Kafka topics defined for the heavy async stages (`verification.started`,
`document.analyzed`, `deepfake.analyzed`, etc.); disabled by default in favor
of synchronous processing for demo reliability, with a documented swap path.

---
### 17. Demo Workflow
Login → dashboard → run a live verification → inspect the identity profile
and graph → review a fraud case → run deepfake/voice analysis → ask the
copilot a grounded question → check the audit trail. See DEMO_GUIDE.md.

---
### 18. Results
- 35/35 automated backend tests passing
- Real OCR, real DSP, real graph algorithms, real SQL-based fraud detection
- Every AI result labeled `REAL_MODEL` / `HEURISTIC` / `DEMO_SIMULATION`
- Full Docker Compose stack; Alembic migration verified on a clean DB

---
### 19. Limitations
Face embedding, liveness, and deepfake detection are explainable heuristics,
not trained neural networks (offline weight-fetching constraint, honestly
labeled throughout — see README's Model Honesty section). Voice STT is a
placeholder. Tested at demo scale, not production scale.

---
### 20. Future Improvements
Swap in InsightFace/ArcFace, a FaceForensics++-trained deepfake classifier,
and Whisper once weights are fetchable; enable Kafka/Neo4j for scale;
multi-tenant support; managed secrets; SHAP explainability once a trained
scoring model replaces the (already fully transparent) formula.
