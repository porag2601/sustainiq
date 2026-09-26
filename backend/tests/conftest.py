"""Shared pytest setup. pytest loads this file automatically before any test.

app.main loads Settings at import time, and Settings requires an API key and
model name. Tests must not depend on a developer's real .env (or leak a real
key), so dummy values are set here before any test imports app.main.
setdefault keeps a value that is already set, e.g. in CI.
"""

import os

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("CLAUDE_MODEL", "test-model")
# In-memory database: tests can never write to the real sustainiq.db file.
os.environ["DATABASE_URL"] = "sqlite://"

import pytest  # noqa: E402  (imports must come after the environment setup)
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.database import Base  # noqa: E402


@pytest.fixture
def db_session():
    """A fresh, empty in-memory database for each test.

    StaticPool keeps one single connection, because every new connection to
    "sqlite://" would otherwise open a new, empty in-memory database.
    """
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        yield session
    engine.dispose()
