"""
Embedding service for InsightForge RAG memory.

Uses Gemini `text-embedding-004` (768-dim) via the existing API key.
Caches embeddings in Upstash Redis so identical strings are only
embedded once (key: `emb:{sha256(text)[:16]}`, TTL 7 days).

Falls back silently if Gemini or Redis is unavailable.
"""
from __future__ import annotations

import hashlib
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_EMBED_TTL = 60 * 60 * 24 * 7  # 7 days


def _cache_key(text: str) -> str:
    return "emb:" + hashlib.sha256(text.encode()).hexdigest()[:24]


class EmbeddingService:
    """Thin wrapper around Gemini embeddings with Upstash Redis caching."""

    def embed(self, text: str) -> Optional[list[float]]:
        """Return a 768-dim embedding for *text*, or None on failure."""
        if not text or not text.strip():
            return None

        from app.config import settings
        from app.core.upstash_client import get_redis

        redis = get_redis()

        # ── L1: Check Redis embedding cache ─────────────────────────────────
        if redis:
            try:
                cached = redis.get(_cache_key(text))
                if cached:
                    return json.loads(cached)
            except Exception as exc:
                logger.debug("Redis embedding cache miss: %s", exc)

        # ── Generate embedding via Gemini ────────────────────────────────────
        if not settings.gemini_api_key:
            logger.warning("No Gemini API key – embedding unavailable.")
            return None

        try:
            from google import genai  # type: ignore
            from google.genai import types  # type: ignore

            client = genai.Client(api_key=settings.gemini_api_key)
            result = client.models.embed_content(
                model=settings.embedding_model,
                contents=text,
            )
            vector: list[float] = result.embeddings[0].values

            # ── Store in Redis embedding cache ───────────────────────────────
            if redis:
                try:
                    redis.set(_cache_key(text), json.dumps(vector), ex=_EMBED_TTL)
                except Exception as exc:
                    logger.debug("Failed to cache embedding: %s", exc)

            return vector
        except Exception as exc:
            logger.error("Gemini embedding failed: %s", exc)
            return None


# Module-level singleton
embedding_service = EmbeddingService()
