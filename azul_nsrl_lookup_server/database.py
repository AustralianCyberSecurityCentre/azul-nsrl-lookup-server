"""Database connection setup."""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import DeferredReflection, declarative_base
from sqlalchemy.orm import sessionmaker

from . import settings

DB_FILE = settings.db.filepath
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_FILE}"


def setup_engine():
    """Delay setting up the engine until called."""
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    return engine, SessionLocal


Base = declarative_base()


class Reflected(DeferredReflection):
    """Enable deferred reflected loading of models from existing database."""

    __abstract__ = True
