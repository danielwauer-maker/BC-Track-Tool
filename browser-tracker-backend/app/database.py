# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./browser_tracker.db"
# Für PostgreSQL später z.B.: "postgresql+psycopg2://user:pass@host/dbname"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}  # nur für SQLite nötig
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
