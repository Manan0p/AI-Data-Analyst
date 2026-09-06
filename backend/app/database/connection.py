from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

db_url = settings.database_url

# Normalize legacy postgres:// url prefixes for Neon / cloud Postgres
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

engine_kwargs = {}
if db_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # Serverless cloud PostgreSQL (Neon / Supabase) optimizations:
    # pool_pre_ping verifies connection viability before use (vital for Neon serverless auto-suspend)
    # pool_recycle prevents stale connections across idle periods
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 300

engine = create_engine(db_url, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator:
    """Dependency for providing a transactional database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

