"""
Optional Kafka consumer entrypoint (Section 25). Only used when
KAFKA_ENABLED=true. Demonstrates the async path calling the exact same
service functions the synchronous HTTP API uses -- no duplicated business
logic between the two modes.

Run (inside the backend container, with Kafka reachable):
    python3 -m app.workers.kafka_consumer
"""
import json
import sys

from app.core.config import settings
from app.core.logging import logger
from app.core.database import SessionLocal


def run():
    if not settings.KAFKA_ENABLED:
        logger.info("KAFKA_ENABLED=false -- worker exiting immediately. "
                    "Heavy pipeline stages run synchronously via the HTTP API instead.")
        sys.exit(0)

    try:
        from kafka import KafkaConsumer
    except ImportError:
        logger.error("kafka-python not installed; cannot start consumer.")
        sys.exit(1)

    consumer = KafkaConsumer(
        "verification.started",
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        group_id="eef-verification-workers",
    )
    logger.info(f"Kafka consumer listening on 'verification.started' ({settings.KAFKA_BOOTSTRAP_SERVERS})")

    for message in consumer:
        payload = message.value
        db = SessionLocal()
        try:
            from app.services import identity_service
            from app.models._all import Identity

            identity = db.query(Identity).filter(Identity.id == payload["identity_id"]).first()
            if not identity:
                logger.error(f"Unknown identity_id in Kafka message: {payload}")
                continue

            # The same function the synchronous API calls -- no logic duplication.
            identity_service.run_verification(
                db, identity, payload["document_type"],
                bytes.fromhex(payload["document_hex"]), bytes.fromhex(payload["selfie_hex"]),
                device_fingerprint=payload.get("device_fingerprint"),
                ip_address=payload.get("ip_address"), actor="kafka_worker",
            )
        except Exception as e:
            logger.error(f"Kafka worker failed processing message: {e}")
        finally:
            db.close()


if __name__ == "__main__":
    run()
