"""
Verification worker (Section 25). Thin wrapper documenting the async
verification path -- delegates entirely to app.services.identity_service,
the same code the synchronous /identity/verify endpoint calls.
See app/workers/kafka_consumer.py for the consumer loop that invokes this.
"""
from app.services import identity_service  # noqa: F401 -- re-exported for the worker entrypoint

# No separate logic here by design: run_verification() in identity_service.py
# is the single source of truth for the pipeline, callable from either the
# synchronous HTTP handler or an async Kafka consumer.
