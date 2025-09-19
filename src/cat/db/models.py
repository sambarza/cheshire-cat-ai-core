import time
from datetime import datetime
from uuid import uuid4

from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, relationship
from sqlalchemy import String, Text, JSON, BigInteger, ForeignKey, DateTime, select

from .database import with_session

Base = declarative_base()

class Setting(Base):
    __tablename__ = "settings"

    name: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    value: Mapped[dict] = mapped_column(JSON, nullable=False)

    @classmethod
    @with_session
    async def get(cls, session: AsyncSession, name: str, default=None):
        result = await session.execute(select(cls).where(cls.name == name))
        setting = result.scalar_one_or_none()
        if setting:
            return setting.value
        return default

    @classmethod
    @with_session
    async def get_all(cls, session: AsyncSession):
        result = await session.execute(select(cls))
        return result.scalars().all()

    @classmethod
    @with_session
    async def set(cls, session: AsyncSession, name: str, value):
        result = await session.execute(select(cls).where(cls.name == name))
        setting = result.scalar_one_or_none()
        if setting:
            setting.value = value
        else:
            setting = cls(name=name, value=value)
            session.add(setting)

    @classmethod
    @with_session
    async def delete(cls, session: AsyncSession, name: str):
        result = await session.execute(select(cls).where(cls.name == name))
        setting = result.scalar_one_or_none()
        if setting:
            await session.delete(setting)


class ChatDB(Base):
    __tablename__ = "chats"
    
    # TODOV2: use proper uuid type
    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid4()), nullable=False
    )
    title: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    body: Mapped[dict] = mapped_column(
        JSON, nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        String, index=True, nullable=False
    )
    context_id: Mapped[str] = mapped_column(
        String, ForeignKey("contexts.id"), nullable=False, index=True
    )

    context = relationship(
        "ContextDB",
        back_populates="chats",
        lazy="selectin"
    )


class ContextDB(Base):
    __tablename__ = "contexts"

    # TODOV2: use proper uuid type
    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid4()), nullable=False
    )
    title: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    body: Mapped[dict] = mapped_column(
        JSON, nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        String, index=True, nullable=False
    )
    
    chats = relationship(
        "ChatDB",
        back_populates="context",
        cascade="all, delete-orphan"
    )