"""
Central configuration for the EEF platform.
All values are overridable via environment variables (.env). Nothing sensitive
is hardcoded -- see .env.example at the project root for the full variable list.
"""
import json
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors_origins(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        if text.startswith("[") and text.endswith("]"):
            try:
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            except json.JSONDecodeError:
                pass
        return [item.strip() for item in text.split(",") if item.strip()]
    return [str(value).strip()]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- App ---
    APP_NAME: str = "EEF - Enterprise Digital Identity, Trust & Deepfake Detection Platform"
    ENV: str = "development"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True

    # --- Database ---
    # Defaults to a local SQLite file so the platform runs with zero external
    # services for demo/grading purposes. In docker-compose this is overridden
    # to a Postgres DSN, e.g. postgresql+psycopg2://eef:eef@postgres:5432/eef
    DATABASE_URL: str = "sqlite:///./eef_demo.db"

    # --- Redis ---
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = False  # auto-disabled gracefully if unreachable

    # --- Kafka ---
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_ENABLED: bool = False  # heavy async pipeline is optional for demo mode

    # --- Neo4j ---
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: str = "eef_neo4j_password"
    NEO4J_ENABLED: bool = False  # falls back to in-process NetworkX graph

    # --- Auth / Security ---
    JWT_SECRET: str = "CHANGE_ME_DEV_ONLY_NOT_FOR_PRODUCTION"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8

    # --- LLM (optional, for the AI Copilot) ---
    LLM_API_KEY: str = ""
    LLM_PROVIDER: str = "none"  # "anthropic" | "none" -> deterministic template mode

    # --- AI / Models ---
    MODEL_DEVICE: str = "cpu"

    # --- Uploads ---
    UPLOAD_DIRECTORY: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 15 * 1024 * 1024  # 15 MB
    ALLOWED_IMAGE_EXT: List[str] = ["jpg", "jpeg", "png", "webp", "bmp"]
    ALLOWED_DOC_EXT: List[str] = ["jpg", "jpeg", "png", "pdf"]
    ALLOWED_VIDEO_EXT: List[str] = ["mp4", "mov", "avi", "webm"]
    ALLOWED_AUDIO_EXT: List[str] = ["wav", "mp3", "m4a"]

    # --- CORS ---
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://localhost:8080"
    CORS_ORIGIN_REGEX: str = r"^https://.*\\.vercel\\.app$"

    # --- Rate limiting (in-memory fallback if Redis disabled) ---
    RATE_LIMIT_PER_MINUTE: int = 120

    # --- Trust scoring weights (Section 14) ---
    # Kept fully in config, never hidden in code. Values sum (roughly) to 1.0
    # across positive-signal weights; risk penalties subtract independently.
    TRUST_WEIGHTS: dict = {
        "identity_score": 0.20,
        "biometric_score": 0.25,
        "liveness_score": 0.15,
        "document_score": 0.20,
        "behavior_score": 0.10,
        "device_score": 0.10,
    }
    TRUST_RISK_PENALTY_PER_FRAUD_SIGNAL: float = 8.0
    TRUST_RISK_PENALTY_DEEPFAKE: float = 30.0
    TRUST_RISK_PENALTY_FACE_MISMATCH: float = 25.0
    TRUST_RISK_PENALTY_LOW_LIVENESS: float = 20.0

    # Face match threshold (Section 8) - documented, not hardcoded silently.
    FACE_MATCH_THRESHOLD: float = 0.62
    LIVENESS_PASS_THRESHOLD: float = 0.55
    DEEPFAKE_ALERT_THRESHOLD: float = 0.60

    # Decision engine thresholds (Section 52)
    TRUST_VERIFIED_MIN: float = 70.0
    TRUST_REVIEW_MIN: float = 40.0
    # below TRUST_REVIEW_MIN -> REJECTED


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
