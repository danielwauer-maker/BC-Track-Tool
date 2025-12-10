# app/models.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from .database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(255), unique=True, index=True)  # BC/AD-User
    display_name = Column(String(255), nullable=True)
    department = Column(String(255), nullable=True)

    sessions = relationship("Session", back_populates="user")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    # ALT:
    # user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    # NEU:
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    session_key = Column(String(255), index=True)
    started_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    client_ip = Column(String(64), nullable=True)
    user_agent = Column(Text, nullable=True)

    user = relationship("User", back_populates="sessions")
    events = relationship("BrowserEvent", back_populates="session")


class BrowserEvent(Base):
    __tablename__ = "browser_events"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), index=True)
    timestamp = Column(DateTime(timezone=True), default=utcnow, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    page_url = Column(Text, nullable=False)
    page_title = Column(Text, nullable=True)

    # NEU: BC-spezifisch
    bc_page_id = Column(Integer, nullable=True, index=True)
    bc_company = Column(String(100), nullable=True, index=True)

    element_type = Column(String(64), nullable=True)   # input, button, select, ...
    element_role = Column(String(64), nullable=True)   # Field, Button, Link, Table
    element_label = Column(Text, nullable=True)
    element_name = Column(Text, nullable=True)
    element_id = Column(Text, nullable=True)
    element_path = Column(Text, nullable=True)

    action_type = Column(String(64), nullable=False)   # click, input_change, focus, blur, keydown ...
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)

    meta = Column(JSON, nullable=True)  # Mauspos, Key, etc.

    session = relationship("Session", back_populates="events")
    user = relationship("User")
