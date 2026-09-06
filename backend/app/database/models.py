import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from app.database.connection import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class DatasetModel(Base):
    __tablename__ = "datasets"

    id = Column(String, primary_key=True)
    owner_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    filename = Column(String, nullable=False)
    storage_key = Column(String, nullable=False)
    row_count = Column(Integer, default=0)
    column_schema = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ChatSessionModel(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True)
    owner_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    dataset_id = Column(String, ForeignKey("datasets.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ChatMessageModel(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

