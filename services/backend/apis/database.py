"""Database configuration and session management."""

from contextlib import contextmanager

from apis.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import (
    declarative_base,
    sessionmaker,
)

# https://fastapi.tiangolo.com/tutorial/sql-databases/#create-the-sqlalchemy-engine
engine = create_engine(settings.DATABASE_URL, connect_args=settings.DATABASE_CONNECT_DICT)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db_session():
    """Create a new session for the database."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


db_context = contextmanager(get_db_session)
