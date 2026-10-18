import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Supabase URL will be provided via the DATABASE_URL environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
    elif DATABASE_URL.startswith("postgresql://") and not DATABASE_URL.startswith("postgresql+psycopg://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
    elif DATABASE_URL.startswith("postgresql+psycopg2://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)
    # pool_pre_ping: transparently replaces connections the server dropped while
    # a serverless instance was idle (avoids sporadic 500s on Supabase/Vercel).
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)
else:
    # Fallback to local SQLite for local development
    SQLALCHEMY_DATABASE_URL = "sqlite:///./nightjar.db"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
