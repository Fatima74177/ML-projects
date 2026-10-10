from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine

router = APIRouter()


@router.get("/health", summary="Overall platform health")
def health():
    return {"status": "ok", "service": settings.APP_NAME}


@router.get("/health/database", summary="Database connectivity check")
def health_database():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "database_url_scheme": settings.DATABASE_URL.split(":")[0]}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.get("/health/redis", summary="Redis connectivity check (optional dependency)")
def health_redis():
    if not settings.REDIS_ENABLED:
        return {"status": "disabled", "detail": "REDIS_ENABLED=false -- running without cache/rate-limit backend."}
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL, socket_connect_timeout=1)
        r.ping()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.get("/health/kafka", summary="Kafka connectivity check (optional dependency)")
def health_kafka():
    if not settings.KAFKA_ENABLED:
        return {"status": "disabled", "detail": "KAFKA_ENABLED=false -- heavy async pipeline runs synchronously in demo mode."}
    return {"status": "unknown", "detail": "Kafka health probe requires a running broker; see docker-compose.yml."}


@router.get("/health/neo4j", summary="Neo4j connectivity check (optional dependency)")
def health_neo4j():
    if not settings.NEO4J_ENABLED:
        return {"status": "disabled", "detail": "NEO4J_ENABLED=false -- using in-process NetworkX graph engine."}
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(settings.NEO4J_URI, auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD))
        with driver.session() as session:
            session.run("RETURN 1")
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.get("/health/models", summary="AI model subsystem health")
def health_models():
    from app.api.routes.models_status import MODEL_REGISTRY
    return {"status": "ok", "components": len(MODEL_REGISTRY)}
