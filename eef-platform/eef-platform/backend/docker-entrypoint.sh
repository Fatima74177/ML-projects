#!/usr/bin/env bash
set -e

echo "[entrypoint] Waiting for database..."
python - <<'PYEOF'
import time, sys, os
sys.path.insert(0, "/eef/backend")
from sqlalchemy import create_engine, text
from app.core.config import settings

for attempt in range(30):
    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("[entrypoint] Database is reachable.")
        break
    except Exception as e:
        print(f"[entrypoint] DB not ready ({e}); retrying ({attempt+1}/30)...")
        time.sleep(2)
else:
    print("[entrypoint] Database never became reachable; exiting.")
    sys.exit(1)
PYEOF

echo "[entrypoint] Running Alembic migrations..."
alembic upgrade head

echo "[entrypoint] Checking whether demo data needs seeding..."
python - <<'PYEOF'
import sys
sys.path.insert(0, "/eef/backend")
from app.core.database import SessionLocal
from app.models._all import Identity

db = SessionLocal()
count = db.query(Identity).count()
db.close()
if count == 0:
    print("[entrypoint] No identities found -- seeding demo data.")
    import subprocess
    subprocess.run(["python", "/eef/scripts/seed_demo_data.py"], check=False, cwd="/eef/backend")
else:
    print(f"[entrypoint] {count} identities already present -- skipping seed.")
PYEOF

echo "[entrypoint] Starting API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
