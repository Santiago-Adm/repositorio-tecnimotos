"""Configuración de SQLAlchemy async para PostgreSQL 16."""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.shared.infrastructure.settings import get_settings


class Base(DeclarativeBase):
    pass


def create_engine(database_url: str | None = None):
    settings = get_settings()
    url = database_url or settings.database_url
    return create_async_engine(
        url,
        echo=settings.environment == "development",
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )


def create_session_factory(engine=None) -> async_sessionmaker[AsyncSession]:
    if engine is None:
        engine = create_engine()
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
