import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def get_query_logger() -> logging.Logger:
    logs_directory = Path("logs")
    logs_directory.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("rag_query_logger")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        handler = logging.FileHandler(
            logs_directory / "queries.log",
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)

    return logger


def log_query(
    logger: logging.Logger,
    query: str,
    answer: str,
    namespace: str,
    sources: list[dict[str, Any]],
) -> None:
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "namespace": namespace,
        "query": query,
        "answer": answer,
        "source_count": len(sources),
        "sources": [
            {
                "document_name": source["metadata"].get("document_name"),
                "page_number": source["metadata"].get("page_number"),
                "score": source["score"],
            }
            for source in sources
        ],
    }
    logger.info(json.dumps(record, ensure_ascii=False))
