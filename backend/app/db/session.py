from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.db.config import DATABASE_URL


class Base(DeclarativeBase):
    pass


try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True) if DATABASE_URL else None
except ImportError:
    engine = None

SessionLocal = (
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
    if engine
    else None
)


def is_database_configured() -> bool:
    return engine is not None and SessionLocal is not None


def get_db_session() -> Generator[Session, None, None]:
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL is not configured")

    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()
