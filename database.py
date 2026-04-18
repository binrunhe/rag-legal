from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = "sqlite+aiosqlite:///./app.db"


class Base(DeclarativeBase):
    pass


engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    from models import Base as ModelsBase

    async with engine.begin() as conn:
        await conn.run_sync(ModelsBase.metadata.create_all)
        result = await conn.exec_driver_sql("PRAGMA table_info(users)")
        columns = {row[1] for row in result.fetchall()}
        if "role" not in columns:
            await conn.exec_driver_sql(
                "ALTER TABLE users ADD COLUMN role VARCHAR(32) NOT NULL DEFAULT 'user'"
            )
        if "is_premium" not in columns:
            await conn.exec_driver_sql(
                "ALTER TABLE users ADD COLUMN is_premium BOOLEAN NOT NULL DEFAULT 1"
            )
