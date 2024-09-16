"""Conftest for the tests."""

import asyncio
import os

import pytest
from apis import create_app
from apis.config import settings as _settings
from apis.database import Base
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

os.environ["FASTAPI_CONFIG"] = "testing"  # noqa


@pytest.fixture(name="settings")
def fixture_settings():
    """Get the settings for the test."""
    print("*** Fixture DB URL ***", _settings.DATABASE_URL)
    return _settings


@pytest.fixture
async def app():
    """Create a new async test app for a test."""
    return create_app()


@pytest.fixture
async def async_client(app):
    """Create a new async test client for a test."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def sync_client(app):
    """Create a new test client for a test."""
    return TestClient(app)


@pytest.fixture
async def db_session() -> AsyncSession:
    """Create a new database session for a test."""
    asyncio.get_running_loop()
    async_database_url = _settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(async_database_url, echo=True)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session
        await session.rollback()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
