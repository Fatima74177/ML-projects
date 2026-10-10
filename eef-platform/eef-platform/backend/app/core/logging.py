"""Structured JSON-ish logging with request IDs (Section 48 - Observability)."""
import logging
import sys
import time
import uuid
from contextvars import ContextVar

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get()
        return True


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger("eef")
    if logger.handlers:
        return logger
    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    fmt = logging.Formatter(
        '{"ts":"%(asctime)s","level":"%(levelname)s","request_id":"%(request_id)s",'
        '"logger":"%(name)s","msg":"%(message)s"}'
    )
    handler.setFormatter(fmt)
    handler.addFilter(RequestIdFilter())
    logger.addHandler(handler)
    return logger


def new_request_id() -> str:
    return uuid.uuid4().hex[:16]


class Timer:
    """Context manager to measure processing time in milliseconds for a stage."""

    def __init__(self, label: str):
        self.label = label
        self.elapsed_ms = 0.0

    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, *exc):
        self.elapsed_ms = (time.perf_counter() - self._start) * 1000


logger = setup_logging()
