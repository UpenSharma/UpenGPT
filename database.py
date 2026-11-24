from datetime import datetime, timezone
from pathlib import Path
from typing import List

from sqlalchemy import create_engine, String, Text, DateTime, Integer, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


Path("data").mkdir(exist_ok=True)

DATABASE_URL = "sqlite:///data/chat_history.sqlite"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Conversation(Base):
    __tablename__ = "conversations"

    thread_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), default="New chat")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    thread_id: Mapped[str] = mapped_column(String(100), index=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Memory(Base):
    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


def init_db() -> None:
    Base.metadata.create_all(engine)


def make_title(text: str, max_length: int = 50) -> str:
    title = " ".join(text.split())

    if len(title) > max_length:
        title = title[:max_length].rstrip() + "..."

    return title or "New chat"


def create_or_update_conversation(thread_id: str, first_message: str) -> None:
    """
    Create the conversation if it is new (titled from the first message),
    otherwise just bump its updated_at timestamp.
    """

    with SessionLocal() as session:
        conversation = session.get(Conversation, thread_id)

        if conversation is None:
            session.add(
                Conversation(
                    thread_id=thread_id,
                    title=make_title(first_message)
                )
            )
        else:
            conversation.updated_at = utcnow()

        session.commit()


def list_conversations() -> List[Conversation]:
    with SessionLocal() as session:
        return list(
            session.scalars(
                select(Conversation).order_by(Conversation.updated_at.desc())
            )
        )


def save_chat_message(thread_id: str, role: str, content: str) -> None:
    with SessionLocal() as session:
        session.add(
            ChatMessage(
                thread_id=thread_id,
                role=role,
                content=content
            )
        )
        session.commit()


def get_chat_history(thread_id: str) -> List[ChatMessage]:
    with SessionLocal() as session:
        return list(
            session.scalars(
                select(ChatMessage)
                .where(ChatMessage.thread_id == thread_id)
                .order_by(ChatMessage.id)
            )
        )


def save_memory(content: str) -> None:
    with SessionLocal() as session:
        session.add(Memory(content=content))
        session.commit()


def get_memories(limit: int = 50) -> List[Memory]:
    with SessionLocal() as session:
        return list(
            session.scalars(
                select(Memory).order_by(Memory.id.desc()).limit(limit)
            )
        )
