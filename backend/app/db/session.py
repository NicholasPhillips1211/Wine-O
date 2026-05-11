"""SQLAlchemy database session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Use SQLite for development/testing
# For production, use: postgresql://user:password@localhost/wine_o
DATABASE_URL = "sqlite:///./wine_o.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Dependency: Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
