"""Conftest for the tests."""

import os

import pytest
from apis import create_app
from apis.config import settings as _settings
from apis.database import (
    Base,
    SessionLocal,
    engine,
)
from apis.factories.users import UserFactory
from fastapi.testclient import TestClient
from httpx import AsyncClient
from pytest_factoryboy import register

os.environ["FASTAPI_CONFIG"] = "testing"  # noqa


register(UserFactory)


@pytest.fixture
def settings():
    """Return the settings."""
    return _settings


@pytest.fixture
def app(settings):  # pylint: disable=unused-argument
    """Return the FastAPI application."""
    app = create_app()
    return app


@pytest.fixture()
def db_session(app):  # pylint: disable=unused-argument
    """Return a database session."""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(app):
    """Return a test client."""
    yield TestClient(app)


@pytest.fixture()
def async_client(app):
    """Return an async test client."""
    yield AsyncClient(app=app, base_url="http://test")


@pytest.fixture(autouse=True)
def tmp_upload_dir(tmpdir, settings):
    """Set the upload directory."""
    settings.UPLOADS_DEFAULT_DEST = tmpdir.mkdir("tmp")
