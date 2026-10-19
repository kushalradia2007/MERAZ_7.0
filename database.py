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


def migrate_to_individual(engine):
    """One-off, idempotent upgrade for databases created when the event was
    team-based. New columns are added to existing tables (create_all never
    alters tables), and old team scores are copied onto each member so nothing
    is lost. Fresh databases are untouched. Legacy teams/team_id columns are
    left in place (unused); drop them by hand if you want a clean schema."""
    from sqlalchemy import inspect, text

    insp = inspect(engine)
    tables = insp.get_table_names()
    if "users" not in tables:
        return
    user_cols = {c["name"] for c in insp.get_columns("users")}
    has_teams = "teams" in tables and "team_id" in user_cols

    with engine.begin() as conn:
        fresh_score = "score" not in user_cols
        if fresh_score:
            conn.execute(text("ALTER TABLE users ADD COLUMN score INTEGER DEFAULT 0"))
        if "current_room" not in user_cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN current_room INTEGER DEFAULT 1"))
        if "created_at" not in user_cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN created_at TIMESTAMP"))
        conn.execute(text("UPDATE users SET score = 0 WHERE score IS NULL"))
        conn.execute(text("UPDATE users SET current_room = 1 WHERE current_room IS NULL"))
        if "has_seen_tour" not in user_cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN has_seen_tour BOOLEAN DEFAULT FALSE"))
        if "board_data" not in user_cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN board_data TEXT"))
        conn.execute(text("UPDATE users SET has_seen_tour = FALSE WHERE has_seen_tour IS NULL"))
        if fresh_score and has_teams:
            conn.execute(text(
                "UPDATE users SET "
                "score = COALESCE((SELECT t.score FROM teams t WHERE t.id = users.team_id), 0), "
                "current_room = COALESCE((SELECT t.current_room FROM teams t WHERE t.id = users.team_id), 1)"
            ))

        if "flag_submissions" in tables:
            sub_cols = {c["name"] for c in insp.get_columns("flag_submissions")}
            if "user_id" not in sub_cols:
                conn.execute(text("ALTER TABLE flag_submissions ADD COLUMN user_id INTEGER"))
                if "team_id" in sub_cols and has_teams:
                    # Old submissions belonged to a team: credit them to its leader,
                    # or to its first member if the leader is gone.
                    conn.execute(text(
                        "UPDATE flag_submissions SET user_id = COALESCE("
                        "(SELECT t.leader_id FROM teams t WHERE t.id = flag_submissions.team_id), "
                        "(SELECT MIN(u.id) FROM users u WHERE u.team_id = flag_submissions.team_id))"
                    ))
