import time
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import String, Text, JSON, BigInteger, select

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


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()), nullable=False)
    user_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    updated_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=lambda: int(time.time()))
    body: Mapped[dict] = mapped_column(JSON, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)