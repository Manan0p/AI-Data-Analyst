import logging
from collections import defaultdict
from app.database.connection import SessionLocal
from app.database.models import ChatMessageModel, ChatSessionModel

logger = logging.getLogger(__name__)


class ConversationMemory:
    def __init__(self):
        self._cache: dict[str, list[dict[str, str]]] = defaultdict(list)

    def add(self, session_id: str, role: str, content: str, owner_id: str | None = None, dataset_id: str | None = None):
        # 1. Update in-memory fast cache (keep latest 12)
        self._cache[session_id].append({"role": role, "content": content})
        self._cache[session_id] = self._cache[session_id][-12:]

        # 2. Persist to database
        db = SessionLocal()
        try:
            session_rec = db.query(ChatSessionModel).filter(ChatSessionModel.id == session_id).first()
            if not session_rec:
                session_rec = ChatSessionModel(
                    id=session_id,
                    owner_id=owner_id,
                    dataset_id=dataset_id,
                )
                db.add(session_rec)
                db.flush()

            msg_rec = ChatMessageModel(
                session_id=session_id,
                role=role,
                content=content,
            )
            db.add(msg_rec)
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.warning("Failed to persist chat message to database: %s", exc)
        finally:
            db.close()

    def get(self, session_id: str) -> list[dict[str, str]]:
        if session_id in self._cache and self._cache[session_id]:
            return self._cache[session_id]

        db = SessionLocal()
        try:
            records = (
                db.query(ChatMessageModel)
                .filter(ChatMessageModel.session_id == session_id)
                .order_by(ChatMessageModel.created_at.asc(), ChatMessageModel.id.asc())
                .all()
            )
            messages = [{"role": m.role, "content": m.content} for m in records[-12:]]
            self._cache[session_id] = messages
            return messages
        except Exception as exc:
            logger.warning("Failed to load chat history from database: %s", exc)
            return self._cache[session_id]
        finally:
            db.close()

    def clear(self, session_id: str | None = None) -> None:
        db = SessionLocal()
        try:
            if session_id:
                db.query(ChatMessageModel).filter(ChatMessageModel.session_id == session_id).delete()
                db.query(ChatSessionModel).filter(ChatSessionModel.id == session_id).delete()
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


memory = ConversationMemory()

