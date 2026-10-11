"""EEF Platform - FastAPI application entrypoint."""
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import parse_cors_origins, settings
from app.core.database import init_db
from app.core.logging import logger, request_id_ctx, new_request_id
from app.core.rate_limit import RequestRateLimiter

from app.api.routes import (
    auth, users, identity, face, documents, deepfake, voice, trust, fraud,
    copilot, graph, alerts, dashboard, audit, models_status, health,
)

app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise digital identity, trust & deepfake detection platform (prototype).",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)
FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
rate_limiter = RequestRateLimiter()

app.add_middleware(
    CORSMiddleware,
    allow_origins=parse_cors_origins(settings.CORS_ORIGINS),
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_and_timing_middleware(request: Request, call_next):
    rid = new_request_id()
    token = request_id_ctx.set(rid)
    start = time.perf_counter()
    try:
        if request.url.path.startswith(settings.API_V1_PREFIX) and request.method != "OPTIONS":
            client_id = request.client.host if request.client else "unknown"
            if rate_limiter.is_limited(
                client_id,
                settings.RATE_LIMIT_PER_MINUTE,
                settings.REDIS_ENABLED,
                settings.REDIS_URL,
            ):
                response = JSONResponse(
                    status_code=429,
                    content={
                        "success": False,
                        "error_code": "RATE_LIMITED",
                        "message": "API request limit exceeded. Try again shortly.",
                        "details": {"limit_per_minute": settings.RATE_LIMIT_PER_MINUTE},
                    },
                    headers={"Retry-After": "60"},
                )
            else:
                response = await call_next(request)
        else:
            response = await call_next(request)
    finally:
        request_id_ctx.reset(token)
    elapsed_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Request-ID"] = rid
    response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.2f}"
    return response


# ---------------------------------------------------------- Error handlers --
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error_code": f"HTTP_{exc.status_code}", "message": str(exc.detail), "details": {}},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"success": False, "error_code": "VALIDATION_ERROR", "message": "Invalid request payload.",
                  "details": {"errors": exc.errors()}},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "error_code": "INTERNAL_ERROR",
                  "message": "An unexpected error occurred. This has been logged.", "details": {}},
    )


# --------------------------------------------------------------- Routers ----
p = settings.API_V1_PREFIX
app.include_router(auth.router, prefix=f"{p}/auth", tags=["Auth"])
app.include_router(users.router, prefix=f"{p}/users", tags=["Users"])
app.include_router(identity.router, prefix=f"{p}/identity", tags=["Identity Verification"])
app.include_router(face.router, prefix=f"{p}/face", tags=["Face & Liveness"])
app.include_router(documents.router, prefix=f"{p}/documents", tags=["Document Intelligence"])
app.include_router(deepfake.router, prefix=f"{p}/deepfake", tags=["Deepfake Detection"])
app.include_router(voice.router, prefix=f"{p}/voice", tags=["Voice Authentication"])
app.include_router(trust.router, prefix=f"{p}/trust", tags=["Trust Scoring"])
app.include_router(fraud.router, prefix=f"{p}/fraud", tags=["Fraud Intelligence"])
app.include_router(copilot.router, prefix=f"{p}/copilot", tags=["AI Copilot"])
app.include_router(graph.router, prefix=f"{p}/graph", tags=["Knowledge Graph"])
app.include_router(alerts.router, prefix=f"{p}/alerts", tags=["Alert Center"])
app.include_router(dashboard.router, prefix=f"{p}/dashboard", tags=["Executive Dashboard"])
app.include_router(audit.router, prefix=f"{p}/audit", tags=["Audit Log"])
app.include_router(models_status.router, prefix=f"{p}/models", tags=["Model Registry"])
app.include_router(health.router, tags=["Health"])


@app.on_event("startup")
def on_startup():
    init_db()
    logger.info("EEF platform started (env=%s, db=%s)" % (settings.ENV, settings.DATABASE_URL))


@app.get("/")
def root():
    index_file = FRONTEND_DIST / "index.html"
    if index_file.is_file():
        return FileResponse(index_file)
    return {
        "name": settings.APP_NAME,
        "status": "ok",
        "docs": "/docs",
        "note": "Prototype/case-study platform. See README.md for scope, model labels, and limitations.",
    }


@app.get("/{path:path}", include_in_schema=False)
def frontend_fallback(path: str):
    api_prefix = settings.API_V1_PREFIX.strip("/")
    if path == api_prefix or path.startswith(f"{api_prefix}/"):
        return JSONResponse(
            status_code=404,
            content={"success": False, "error_code": "HTTP_404", "message": "Not Found", "details": {}},
        )

    dist_dir = FRONTEND_DIST.resolve()
    requested_file = (dist_dir / path).resolve()
    if dist_dir in requested_file.parents and requested_file.is_file():
        return FileResponse(requested_file)

    index_file = dist_dir / "index.html"
    if index_file.is_file():
        return FileResponse(index_file)
    return JSONResponse(status_code=404, content={"detail": "Not Found"})
