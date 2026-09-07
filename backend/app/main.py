import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.api.auth_routes import router as auth_router
from app.api.routes import router
from app.config import settings
from app.core.limiter import limiter
from app.core.logging_config import setup_logging, setup_sentry
from app.database.connection import Base, engine
import app.database.models  # ensure models are registered with Base

setup_logging()
setup_sentry()

logger = logging.getLogger(__name__)

# Create database tables automatically (safe for serverless read-only environments)
try:
    Base.metadata.create_all(bind=engine)
except Exception as exc:
    logger.warning("Database schema initialization warning: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────────────────────
    from app.core.upstash_client import get_redis, get_vector
    redis = get_redis()
    vector = get_vector()
    logger.info(
        "InsightForge started | Redis(L1)=%s | Vector(L2)=%s",
        "✓ connected" if redis else "✗ disabled (fallback to in-process dict)",
        "✓ connected" if vector else "✗ disabled (RAG retrieval inactive)",
    )
    yield
    # ── Shutdown (no-op for now) ──────────────────────────────────────────────


app = FastAPI(title=settings.app_name, version='1.0.0', lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Universal CORS configuration for Vercel preview URLs, production domains, and local dev
cors_origins_list = [o.strip() for o in settings.cors_origins.split(',') if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins_list if '*' not in cors_origins_list and cors_origins_list else [],
    allow_origin_regex=r"^https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix='/api/auth', tags=['auth'])
app.include_router(router, prefix='/api')

@app.get('/health')
def health():
    return {'status': 'ok'}
