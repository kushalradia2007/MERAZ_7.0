from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from database import Base
import datetime


class User(Base):
    """One participant. The event is individual: score and room progress live
    directly on the user (there are no teams)."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    is_email_verified = Column(Boolean, default=False)
    hashed_password = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)
    score = Column(Integer, default=0)
    current_room = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    has_seen_tour = Column(Boolean, default=False)
    board_data = Column(Text, nullable=True)  # JSON: case-board layout (positions, links, notes)


class FlagSubmission(Base):
    __tablename__ = "flag_submissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    room_id = Column(Integer)
    flag_value = Column(String, nullable=True)
    submitted_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_correct = Column(Boolean, default=False)


class VerificationCode(Base):
    __tablename__ = "verification_codes"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    code = Column(String)
    expires_at = Column(DateTime)
