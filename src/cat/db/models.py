
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import String, JSON, select

from .database import get_session

Base = declarative_base()

class Setting(Base):
    __tablename__ = "settings"

    name: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    value: Mapped[dict] = mapped_column(JSON, nullable=False)

    @classmethod
    async def get(cls, name: str, default=None):
        async with get_session() as session:
            result = await session.execute(
                select(cls).where(cls.name == name)
            )
            setting = result.scalar_one_or_none()
            if setting:
                return setting.value
            return default

    @classmethod
    async def get_all(cls):
        async with get_session() as session:
            result = await session.execute(
                select(cls)
            )
            return result.scalars().all()
            

    @classmethod
    async def set(cls, name: str, value):
        async with get_session() as session:
            result = await session.execute(
                select(cls).where(cls.name == name)
            )
            setting = result.scalar_one_or_none()
            if setting:
                setting.value = value
            else:
                setting = cls(name=name, value=value)
                session.add(setting)

    @classmethod
    async def delete(cls, name: str):
        async with get_session() as session:
            result = await session.execute(
                select(cls).where(cls.name == name)
            )
            setting = result.scalar_one_or_none()
            if setting:
                await session.delete(setting)