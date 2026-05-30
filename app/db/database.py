import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings


def _build_url(raw_url: str) -> str:
    """
    Convert a plain postgres:// or postgresql:// URL to the
    postgresql+asyncpg:// scheme that SQLAlchemy needs.
    Also strips ?sslmode=require because asyncpg handles SSL
    via connect_args, not as a query parameter.
    """
    url = raw_url
    url = url.replace("postgresql://", "postgresql+asyncpg://")
    url = url.replace("postgres://",   "postgresql+asyncpg://")

    # Remove sslmode query param – asyncpg rejects it
    url = url.replace("?sslmode=require", "")
    url = url.replace("&sslmode=require", "")
    url = url.replace("?sslmode=prefer",  "")
    url = url.replace("&sslmode=prefer",  "")

    return url


def _get_engine():
    raw_url = settings.database_url

    # ── PostgreSQL / Neon ────────────────────────────────────────
    if "postgresql" in raw_url or "postgres" in raw_url:
        url = _build_url(raw_url)
        return create_async_engine(
            url,
            echo=False,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            connect_args={
                "ssl": "require",          # asyncpg SSL flag
                "server_settings": {
                    "application_name": "smart-retail-assistant",
                },
            },
        )

    # ── SQLite (local dev fallback) ──────────────────────────────
    os.makedirs("data", exist_ok=True)
    return create_async_engine(
        raw_url,
        echo=False,
        connect_args={"check_same_thread": False},
    )


engine = _get_engine()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    """FastAPI dependency – yields an async DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Create all tables on startup."""
    from app.db import models  # noqa: F401 – registers ORM models
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
