import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

# Local development only
if ENV_FILE.exists():
    load_dotenv(
        dotenv_path=ENV_FILE,
        override=False,
    )


def _get_secret(
    name: str,
    default: str = "",
) -> str:
    """
    Read a value from:
    1. Operating-system environment variables
    2. Streamlit Cloud secrets
    3. A supplied default value
    """
    environment_value = os.getenv(name)

    if environment_value:
        return str(environment_value).strip()

    try:
        import streamlit as st

        if name in st.secrets:
            return str(st.secrets[name]).strip()

    except Exception:
        pass

    return str(default).strip()


def _get_integer(
    name: str,
    default: int,
) -> int:
    value = _get_secret(
        name=name,
        default=str(default),
    )

    try:
        return int(value)

    except ValueError as error:
        raise ValueError(
            f"{name} must contain a valid integer."
        ) from error


@dataclass(frozen=True)
class Settings:
    pinecone_api_key: str = _get_secret(
        "PINECONE_API_KEY"
    )

    pinecone_index_name: str = _get_secret(
        "PINECONE_INDEX_NAME",
        "intermediate-rag-index",
    )

    pinecone_cloud: str = _get_secret(
        "PINECONE_CLOUD",
        "aws",
    )

    pinecone_region: str = _get_secret(
        "PINECONE_REGION",
        "us-east-1",
    )

    groq_api_key: str = _get_secret(
        "GROQ_API_KEY"
    )

    groq_model: str = _get_secret(
        "GROQ_MODEL",
        "llama-3.3-70b-versatile",
    )

    groq_max_tokens: int = _get_integer(
        "GROQ_MAX_TOKENS",
        700,
    )

    embedding_model: str = _get_secret(
        "EMBEDDING_MODEL",
        "sentence-transformers/all-MiniLM-L6-v2",
    )

    ocr_language: str = _get_secret(
        "OCR_LANGUAGE",
        "eng",
    )

    ocr_dpi: int = _get_integer(
        "OCR_DPI",
        300,
    )

    ocr_min_native_characters: int = _get_integer(
        "OCR_MIN_NATIVE_CHARACTERS",
        80,
    )

    tessdata_prefix: str | None = (
        _get_secret("TESSDATA_PREFIX") or None
    )

    default_namespace: str = _get_secret(
        "DEFAULT_NAMESPACE",
        "pdf-documents",
    )

    max_file_size_mb: int = 20
    default_chunk_size: int = 800
    default_chunk_overlap: int = 150
    default_top_k: int = 5
    default_similarity_threshold: float = 0.40


settings = Settings()