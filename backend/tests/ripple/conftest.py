from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import Base, engine


@pytest.fixture(scope="session", autouse=True)
def ensure_database_schema() -> None:
    Base.metadata.create_all(engine)


@pytest.fixture
def db_session() -> Session:
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, autoflush=False)
    table_names = ", ".join(f'"{table.name}"' for table in reversed(Base.metadata.sorted_tables))
    session.execute(text(f"TRUNCATE TABLE {table_names} CASCADE"))
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
