"""Async database session and engine configuration."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.config import settings

Base = declarative_base()

# Async engine for PostgreSQL (default) or provided DATABASE_URL
engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide a single async DB session per request."""
    async with AsyncSessionLocal() as session:
        yield session

