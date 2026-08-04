import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

if not ENV_FILE.exists():
    raise FileNotFoundError(
        f".env file was not found at: {ENV_FILE}\n"
        "Create the .env file in the same folder as app.py."
    )

env_loaded = load_dotenv(
    dotenv_path=str(ENV_FILE),
    override=True,
)

if not env_loaded:
    raise RuntimeError(
        f"The .env file exists but could not be loaded: {ENV_FILE}"
    )


def _read_int(
    name: str,
    default: int,
) -> int:
    value = os.getenv(name, str(default)).strip()

    try:
        return int(value)
    except ValueError as error:
        raise ValueError(
            f"{name} must contain a valid integer."
        ) from error


@dataclass(frozen=True)
class Settings:
    pinecone_api_key: str = os.getenv(
        "PINECONE_API_KEY",
        "",
    ).strip()

    pinecone_index_name: str = os.getenv(
        "PINECONE_INDEX_NAME",
        "intermediate-rag-index",
    ).strip()

    pinecone_cloud: str = os.getenv(
        "PINECONE_CLOUD",
        "aws",
    ).strip()

    pinecone_region: str = os.getenv(
        "PINECONE_REGION",
        "us-east-1",
    ).strip()

    groq_api_key: str = os.getenv(
        "GROQ_API_KEY",
        "",
    ).strip()

    groq_model: str = os.getenv(
        "GROQ_MODEL",
        "llama-3.3-70b-versatile",
    ).strip()

    groq_max_tokens: int = _read_int(
        "GROQ_MAX_TOKENS",
        700,
    )

    embedding_model: str = os.getenv(
        "EMBEDDING_MODEL",
        "sentence-transformers/all-MiniLM-L6-v2",
    ).strip()

    ocr_language: str = os.getenv(
        "OCR_LANGUAGE",
        "eng",
    ).strip()

    ocr_dpi: int = _read_int(
        "OCR_DPI",
        300,
    )

    ocr_min_native_characters: int = _read_int(
        "OCR_MIN_NATIVE_CHARACTERS",
        80,
    )

    tessdata_prefix: str | None = (
        os.getenv(
            "TESSDATA_PREFIX",
            "",
        ).strip()
        or None
    )

    default_namespace: str = os.getenv(
        "DEFAULT_NAMESPACE",
        "pdf-documents",
    ).strip()

    max_file_size_mb: int = 20
    default_chunk_size: int = 800
    default_chunk_overlap: int = 150
    default_top_k: int = 5
    default_similarity_threshold: float = 0.40


settings = Settings()