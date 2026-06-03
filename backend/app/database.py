from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings

engine = create_async_engine(settings.database_url, echo=False)

# Reusable session factory; expire_on_commit=False keeps objects accessible after commit.
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a database session per request."""
    async with AsyncSessionLocal() as session:
        yield session


async def create_db_and_tables() -> None:
    """Create all SQLModel tables if they don't exist.

    Used by scripts and startup; migrations (Alembic) are authoritative in production.
    """
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
