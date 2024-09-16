"""Database configuration and session management."""
from contextlib import asynccontextmanager

from apis.config import settings
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import (
    declarative_base,
    sessionmaker,
)

# Update the DATABASE_URL to use the async driver
# Replace postgresql:// with postgresql+asyncpg://
async_database_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Create async engine
engine = create_async_engine(
    async_database_url,
    # Remove connect_args if they're not needed for asyncpg
    # If you do need to pass any connect args, make sure they're compatible with asyncpg
)

# Create async session
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


async def get_db_session():
    """Get a database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


db_context = asynccontextmanager(get_db_session)
