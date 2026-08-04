import re

from config.settings import settings


def validate_pdf_upload(file_name: str, file_bytes: bytes) -> None:
    if not file_name.lower().endswith(".pdf"):
        raise ValueError(f"{file_name} is not a PDF.")
    if not file_bytes:
        raise ValueError(f"{file_name} is empty.")

    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise ValueError(
            f"{file_name} exceeds the "
            f"{settings.max_file_size_mb} MB limit."
        )

    if b"%PDF" not in file_bytes[:1024]:
        raise ValueError(
            f"{file_name} does not have a valid PDF signature."
        )


def sanitize_namespace(namespace: str) -> str:
    namespace = namespace.strip()
    if not namespace:
        raise ValueError("Namespace cannot be empty.")

    sanitized = re.sub(r"[^A-Za-z0-9_-]", "-", namespace)
    sanitized = re.sub(r"-{2,}", "-", sanitized).strip("-")

    if not sanitized:
        raise ValueError("Namespace contains no valid characters.")

    return sanitized[:64]
