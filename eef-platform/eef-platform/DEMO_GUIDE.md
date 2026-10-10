# DEMO_GUIDE.md — EEF Platform Scripted Walkthrough

Prereqs: `docker compose up --build` has finished and seeded demo data (or
you ran `scripts/seed_demo_data.py` locally). This script works without
editing any code.

1. **Login as analyst** — go to http://localhost:5173/login, sign in with
   `analyst` / `Analyst@12345`.
2. **Open the dashboard** — lands on `/dashboard` automatically; note the
   stat cards are populated from real seeded data (20 identities, 30
   verifications, etc.).
3. **Show identity statistics** — point out the Risk Distribution pie chart
   and Trust Score histogram — both computed live from Postgres.
4. **Start identity verification** — go to `/verification`.
5. **Upload demo document** — step 2 of the wizard, upload
   `data/demo/documents/demo_national_id_1.png`.
6. **Upload demo selfie** — step 3, upload `data/demo/images/face_a_1.png`.
7. **Run OCR** — implicit: submitting the wizard runs OCR as part of the
   pipeline (or demo it standalone at `/documents` first for a focused look).
8. **Run face match** — implicit in the same submit (or demo standalone at
   `/face` via the API/Swagger UI).
9. **Run liveness** — implicit in the same submit; passive liveness runs on
   the selfie automatically.
10. **Generate trust score** — step 4 → "Run Verification"; the result page
    shows the trust score and full formula breakdown.
11. **Show verification decision** — note the `VERIFIED` / `REVIEW_REQUIRED`
    / `REJECTED` badge and the "Decision Reasoning" list.
12. **Open identity profile** — go to `/identities`, click into any row →
    `/identities/{id}` shows verification history, devices, IPs, documents,
    and alerts for that person.
13. **Show graph relationships** — go to `/graph`, enter the same identity
    ID, click "Load" — see the live NetworkX-rendered graph with connected
    devices/documents/IPs/fraud cases.
14. **Open a suspicious identity** — from the seed script, identities `1`–`4`
    deliberately share a device (fraud ring) and `1`/`2` share a duplicate
    document number — load identity `1` or `2` in the graph to see the
    cluster.
15. **Show fraud alerts** — go to `/fraud`; expand a case to see its signals,
    related identities/devices/documents, and add an investigation note.
16. **Upload demo manipulated video** — go to `/deepfake`, switch to VIDEO,
    upload `data/demo/videos/demo_clip_1.mp4`.
17. **Run deepfake analysis** — click "Run Deepfake Analysis".
18. **Show frame-level results** — the frame timeline bar chart under the
    result shows per-frame scores; hover a bar for its frame number/score.
19. **Upload demo audio** — go to `/voice`, upload
    `data/demo/audio/demo_voice_1.wav`.
20. **Run voice analysis** — click "Analyze Voice"; note the real DSP metrics
    (duration, sample rate, speaker/quality scores) and the labeled
    placeholder transcript.
21. **Open AI Copilot** — go to `/copilot`.
22. **Ask why verification failed** — click the "Why did verification fail
    for user 9?" suggestion chip (seed data includes a `weak` scenario for
    several identities).
23. **Show evidence-backed explanation** — the copilot's answer includes a
    "View citations" expandable showing the exact tool calls/DB rows it used.
24. **Open audit log** — go to `/audit`; every action taken during this demo
    (login, verification, document analysis, deepfake analysis, voice
    analysis, copilot query) is listed with actor, action, result, and
    timestamp — immutable, read-only.

## API-only variant (no frontend)

All 24 steps can be run via `curl`/Swagger UI at `/docs` if you prefer to
demo the backend directly — every endpoint used above is documented in
[API_DOCUMENTATION.md](API_DOCUMENTATION.md).
