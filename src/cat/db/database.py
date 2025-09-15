import os
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy import event

from cat.env import get_env
from cat.log import log

DB_URL = get_env("CCAT_SQL")

connect_args = {}
if DB_URL.startswith("sqlite"):
    connect_args["timeout"] = 10
    connect_args["check_same_thread"] = False
if DB_URL.startswith("postgresql"):
    connect_args["connect_args"] = 10

engine = create_async_engine(
    DB_URL,
    echo=True,
    future=True,
    pool_pre_ping=True,
    connect_args=connect_args
)

if DB_URL.startswith("sqlite"):
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        # TODOV2: check wich of those are necessary or at least useful
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA busy_timeout=5000;")
        cursor.close()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)

@asynccontextmanager
async def get_session():
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        log.error("Error during db session")
        raise