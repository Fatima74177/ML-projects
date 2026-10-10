"""
Fraud scan worker (Section 25). Periodic/triggered re-scan for fraud signals,
delegating to app.services.fraud_service.build_fraud_cases() -- the same
function the synchronous POST /fraud/scan endpoint calls.

Run manually or on a schedule (e.g. a cron-triggered container / Kafka
consumer on a 'fraud.scan.requested' topic):
    python3 -m app.workers.fraud_worker
"""
from app.core.database import SessionLocal
from app.core.logging import logger
from app.services import fraud_service


def run_scan():
    db = SessionLocal()
    try:
        created = fraud_service.build_fraud_cases(db)
        logger.info(f"fraud_worker: created {len(created)} fraud case(s) from detected signals.")
        return created
    finally:
        db.close()


if __name__ == "__main__":
    run_scan()
