"""
3-layer ConversationMemory for InsightForge.

Layer 1 — Upstash Redis List  (hot, fast, last N turns, TTL-bounded)
Layer 2 — Upstash Vector Index (semantic RAG retrieval of past turns)
Layer 3 — SQLite / Postgres    (cold full history, source of truth)

Graceful degradation: if Upstash is not configured every operation
falls through to the in-process dict + SQLite path so the app works
without any Redis credentials.
"""
from __future__ import annotations

import json
import logging
import uuid
from collections import defaultdict
from typing import Optional

from app.database.connection import SessionLocal
from app.database.models import ChatMessageModel, ChatSessionModel

logger = logging.getLogger(__name__)


# ── helpers ───────────────────────────────────────────────────────────────────

def _redis_key(session_id: str) -> str:
    return f"chat:turns:{session_id}"

def _vector_namespace(session_id: str) -> str:
    """Upstash Vector uses a flat namespace; prefix with session id."""
    return session_id


# ── ConversationMemory ────────────────────────────────────────────────────────

class ConversationMemory:
    def __init__(self):
        # In-process fallback (used when Upstash is absent)
        self._cache: dict[str, list[dict]] = defaultdict(list)

    # ── private helpers ───────────────────────────────────────────────────────

    def _redis(self):
        from app.core.upstash_client import get_redis
        return get_redis()

    def _vector(self):
        from app.core.upstash_client import get_vector
        return get_vector()

    def _settings(self):
        from app.config import settings
        return settings

    # ── public API ────────────────────────────────────────────────────────────

    def add(
        self,
        session_id: str,
        role: str,
        content: str,
        owner_id: str | None = None,
        dataset_id: str | None = None,
        analysis_data: dict | None = None,
    ) -> None:
        """Persist a chat turn across all three layers."""
        turn = {"role": role, "content": content}
        if analysis_data:
            turn["analysis"] = analysis_data

        cfg = self._settings()

        # ── Layer 3: SQLite persist ───────────────────────────────────────────
        db = SessionLocal()
        try:
            session_rec = db.query(ChatSessionModel).filter(
                ChatSessionModel.id == session_id
            ).first()
            if not session_rec:
                session_rec = ChatSessionModel(
                    id=session_id,
                    owner_id=owner_id,
                    dataset_id=dataset_id,
                )
                db.add(session_rec)
                db.flush()

            db.add(ChatMessageModel(
                session_id=session_id,
                role=role,
                content=content,
                analysis_data=analysis_data
            ))
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.warning("Failed to persist chat message to DB: %s", exc)
        finally:
            db.close()

        # ── Layer 1: Upstash Redis List ───────────────────────────────────────
        redis = self._redis()
        key = _redis_key(session_id)
        if redis:
            try:
                redis.rpush(key, json.dumps(turn))
                # Keep only the last N turns
                redis.ltrim(key, -cfg.chat_context_window, -1)
                redis.expire(key, cfg.redis_chat_ttl_seconds)
            except Exception as exc:
                logger.warning("Upstash Redis write failed: %s", exc)
        else:
            # In-process fallback
            self._cache[session_id].append(turn)
            self._cache[session_id] = self._cache[session_id][-cfg.chat_context_window:]

        # ── Layer 2: Upstash Vector upsert ────────────────────────────────────
        vector_client = self._vector()
        if vector_client and content.strip():
            try:
                from app.memory.embeddings import embedding_service
                embedding = embedding_service.embed(content)
                if embedding:
                    vector_id = f"{session_id}:{str(uuid.uuid4())}"
                    vector_client.upsert(
                        vectors=[{
                            "id": vector_id,
                            "vector": embedding,
                            "metadata": {
                                "session_id": session_id,
                                "role": role,
                                "content": content,
                            },
                        }]
                    )
            except Exception as exc:
                logger.warning("Upstash Vector upsert failed: %s", exc)

    def get(self, session_id: str) -> list[dict]:
        """Return recent turns for *session_id* (L1 → L3 fallback chain)."""
        cfg = self._settings()
        redis = self._redis()

        # ── L1: Try Upstash Redis ─────────────────────────────────────────────
        if redis:
            try:
                raw = redis.lrange(_redis_key(session_id), 0, -1)
                if raw:
                    return [json.loads(r) for r in raw]
            except Exception as exc:
                logger.warning("Upstash Redis read failed: %s", exc)

        # ── In-process fallback ───────────────────────────────────────────────
        if session_id in self._cache and self._cache[session_id]:
            return self._cache[session_id]

        # ── L3: SQLite cold load ──────────────────────────────────────────────
        db = SessionLocal()
        try:
            records = (
                db.query(ChatMessageModel)
                .filter(ChatMessageModel.session_id == session_id)
                .order_by(ChatMessageModel.created_at.asc(), ChatMessageModel.id.asc())
                .all()
            )
            messages = []
            for m in records[-cfg.chat_context_window:]:
                item = {"role": m.role, "content": m.content}
                if m.analysis_data:
                    item["analysis"] = m.analysis_data
                messages.append(item)

            # Back-fill Redis so next request is fast
            if redis and messages:
                try:
                    key = _redis_key(session_id)
                    for m in messages:
                        redis.rpush(key, json.dumps(m))
                    redis.ltrim(key, -cfg.chat_context_window, -1)
                    redis.expire(key, cfg.redis_chat_ttl_seconds)
                except Exception:
                    pass

            self._cache[session_id] = messages
            return messages
        except Exception as exc:
            logger.warning("Failed to load chat history from DB: %s", exc)
            return self._cache.get(session_id, [])
        finally:
            db.close()

    def get_relevant(
        self,
        session_id: str,
        query: str,
        top_k: int | None = None,
    ) -> list[dict]:
        """
        Semantic RAG retrieval: return the *top_k* past turns most relevant
        to *query* via Upstash Vector KNN search.

        Returns [] if Upstash Vector is not configured or embedding fails.
        """
        if not query.strip():
            return []

        cfg = self._settings()
        k = top_k if top_k is not None else cfg.rag_top_k
        vector_client = self._vector()

        if not vector_client:
            return []

        try:
            from app.memory.embeddings import embedding_service
            query_embedding = embedding_service.embed(query)
            if not query_embedding:
                return []

            results = vector_client.query(
                vector=query_embedding,
                top_k=k,
                include_metadata=True,
                filter=f'session_id = "{session_id}"',
            )

            relevant: list[dict] = []
            for r in results:
                meta = r.metadata or {}
                if meta.get("session_id") == session_id and meta.get("content"):
                    relevant.append({
                        "role": meta.get("role", "user"),
                        "content": meta["content"],
                    })
            return relevant
        except Exception as exc:
            logger.warning("Upstash Vector query failed: %s", exc)
            return []

    def clear(self, session_id: str | None = None) -> None:
        """Clear chat history from all layers."""
        redis = self._redis()
        vector_client = self._vector()

        # ── Layer 3: SQLite ───────────────────────────────────────────────────
        db = SessionLocal()
        try:
            if session_id:
                db.query(ChatMessageModel).filter(
                    ChatMessageModel.session_id == session_id
                ).delete()
                db.query(ChatSessionModel).filter(
                    ChatSessionModel.id == session_id
                ).delete()
                self._cache.pop(session_id, None)
            else:
                db.query(ChatMessageModel).delete()
                db.query(ChatSessionModel).delete()
                self._cache.clear()
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.warning("Failed to clear chat memory from DB: %s", exc)
        finally:
            db.close()

        # ── Layer 1: Upstash Redis ────────────────────────────────────────────
        if redis and session_id:
            try:
                redis.delete(_redis_key(session_id))
            except Exception as exc:
                logger.warning("Failed to delete Redis key: %s", exc)

        # ── Layer 2: Upstash Vector ───────────────────────────────────────────
        # Note: Upstash Vector supports namespace-level delete or filter delete.
        if vector_client and session_id:
            try:
                # Delete all vectors for this session using metadata filter
                vector_client.delete(filter=f'session_id = "{session_id}"')
            except Exception as exc:
                logger.warning("Failed to delete Upstash Vector namespace: %s", exc)


# Module-level singleton
memory = ConversationMemory()
