"""Async engine + session factory."""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import Settings, get_settings

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def _make_engine(settings: Settings) -> AsyncEngine:
    # SQLite (tests) needs connect args; pooling differs from Postgres.
    if settings.database_url.startswith("sqlite"):
        return create_async_engine(settings.database_url, future=True)
    return create_async_engine(
        settings.database_url, future=True, pool_pre_ping=True, pool_size=10, max_overflow=20
    )


def get_engine(settings: Settings | None = None) -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = _make_engine(settings or get_settings())
    return _engine


def get_sessionmaker(settings: Settings | None = None) -> async_sessionmaker[AsyncSession]:
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(
            get_engine(settings), expire_on_commit=False, autoflush=False
        )
    return _sessionmaker


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: yields a session and commits/rolls back around the request."""
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def reset_engine_state() -> None:
    """Test helper to drop cached engine/sessionmaker (e.g. between test sessions)."""
    global _engine, _sessionmaker
    _engine = None
    _sessionmaker = None
