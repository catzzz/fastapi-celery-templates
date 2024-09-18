"""Test the users table exists in the database."""

from apis.database import SessionLocal
from sqlalchemy.sql import text


def test_users_table_exists(db_session: SessionLocal):
    """Test the users table exists in the database."""
    statement = text("SELECT to_regclass('users')")
    result = db_session.execute(statement)
    assert result.scalar() == "users"
    db_session.close()
