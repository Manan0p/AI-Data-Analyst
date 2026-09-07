"""
Upstash client singletons for InsightForge.

Two lazy clients:
  - `get_redis()`  → Upstash Redis (L1 chat history cache)
  - `get_vector()` → Upstash Vector (L2 RAG semantic index)

Both return None gracefully when env-vars are absent so the app
can still run in pure SQLite mode without Upstash credentials.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Optional

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_redis():
    """Return a cached Upstash Redis client, or None if not configured."""
    from app.config import settings

    if not settings.upstash_redis_rest_url or not settings.upstash_redis_rest_token:
        logger.warning("Upstash Redis not configured – falling back to in-process dict cache.")
        return None

    try:
        from upstash_redis import Redis  # type: ignore
        client = Redis(
            url=settings.upstash_redis_rest_url,
            token=settings.upstash_redis_rest_token,
        )
        # Lightweight connectivity check
        client.ping()
        logger.info("Upstash Redis connected: %s", settings.upstash_redis_rest_url)
        return client
    except Exception as exc:
        logger.error("Upstash Redis connection failed: %s – using in-process fallback.", exc)
        return None


@lru_cache(maxsize=1)
def get_vector():
    """Return a cached Upstash Vector index client, or None if not configured."""
    from app.config import settings

    if not settings.upstash_vector_rest_url or not settings.upstash_vector_rest_token:
        logger.warning("Upstash Vector not configured – RAG retrieval disabled.")
        return None

    try:
        from upstash_vector import Index  # type: ignore
        index = Index(
            url=settings.upstash_vector_rest_url,
            token=settings.upstash_vector_rest_token,
        )
        logger.info("Upstash Vector connected: %s", settings.upstash_vector_rest_url)
        return index
    except Exception as exc:
        logger.error("Upstash Vector connection failed: %s – RAG disabled.", exc)
        return None
