"""Database configuration and session management."""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool

load_dotenv()

DEFAULT_DATABASE_URL = (
    "mysql+pymysql://root:tiger@localhost:3306/sih_platform?charset=utf8mb4"
)


def _normalize_mysql_url(url: str) -> str:
    """Ensure MySQL connections use utf8mb4 so emoji/unicode data never 1406s."""
    parsed = make_url(url)
    query = dict(parsed.query)
    query.setdefault("charset", "utf8mb4")
    return parsed.update_query_dict(query).render_as_string(hide_password=False)


def _ensure_database_exists(url: str) -> None:
    """Create the target MySQL database if it does not exist yet."""
    parsed = make_url(url)
    if not parsed.database:
        return
    server_url = parsed.set(database=None).render_as_string(hide_password=False)
    probe_engine = create_engine(server_url, poolclass=NullPool)
    try:
        with probe_engine.connect() as conn:
            conn.execute(
                text(
                    f"CREATE DATABASE IF NOT EXISTS `{parsed.database}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            )
            conn.commit()
    finally:
        probe_engine.dispose()


def _build_database_url() -> str:
    """Resolve the database URL from the environment, with sane MySQL defaults."""
    url = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    if not url.startswith("mysql"):
        # Non-MySQL URLs (e.g. SQLite in tests) are used as-is.
        return url

    url = _normalize_mysql_url(url)
    try:
        _ensure_database_exists(url)
    except Exception:
        # MySQL not reachable: let create_engine / first query raise a clearer
        # error instead of masking the connection problem here.
        pass
    return url


DATABASE_URL = _build_database_url()

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
