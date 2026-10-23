import os
from datetime import datetime, date
from sqlalchemy import (
    create_engine, Column, Integer, String, Text,
    Boolean, DateTime, Date, ForeignKey
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aura.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=True)
    email = Column(String(120), unique=True, index=True, nullable=True)
    phone = Column(String(25), nullable=True)
    dob = Column(String(30), nullable=True)
    address = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    profile_pic = Column(Text, nullable=True)
    password_hash = Column(String(256), nullable=False)
    salt = Column(String(64), nullable=True)
    role = Column(String(20), default="operator")  # "admin" | "operator"
    status = Column(String(20), default="active")   # "pending", "active", "rejected", "banned"
    ban_reason = Column(Text, nullable=True)
    freeze_tokens = Column(Integer, default=2)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    conversation_messages = relationship("ConversationMessage", back_populates="user", cascade="all, delete-orphan")
    goal_jobs = relationship("GoalJob", back_populates="user", cascade="all, delete-orphan")
    memories = relationship("Memory", back_populates="user", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="user", cascade="all, delete-orphan")
    appeals = relationship("AppealRequest", back_populates="user", cascade="all, delete-orphan")

class Goal(Base):
    __tablename__ = "goals"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    intention = Column(String(255), nullable=False)
    timeline = Column(String(50), nullable=True)
    current_level = Column(String(50), nullable=True)
    category = Column(String(50), default="General")
    streak_count = Column(Integer, default=0)
    saved_streak_count = Column(Integer, default=0)
    streak_frozen = Column(Boolean, default=False)
    in_recovery = Column(Boolean, default=False)
    recovery_task = Column(String(255), nullable=True)
    last_check_in_date = Column(Date, nullable=True)
    progress_percentage = Column(Integer, default=0)
    daily_routine = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="goals")
    milestones = relationship("Milestone", back_populates="goal", cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="goal", cascade="all, delete-orphan")
    tasks = relationship("GoalTask", back_populates="goal", cascade="all, delete-orphan")

class Milestone(Base):
    __tablename__ = "milestones"
    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(Integer, ForeignKey("goals.id", ondelete="CASCADE"), nullable=False)
    phase_title = Column(String(255), nullable=False)
    is_completed = Column(Boolean, default=False)

    goal = relationship("Goal", back_populates="milestones")

class GoalTask(Base):
    __tablename__ = "goal_tasks"
    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(Integer, ForeignKey("goals.id", ondelete="CASCADE"), nullable=False)
    task_description = Column(String(255), nullable=False)
    scheduled_time = Column(String(50), default="Daily")
    is_completed = Column(Boolean, default=False)

    goal = relationship("Goal", back_populates="tasks")

class Reminder(Base):
    __tablename__ = "reminders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    goal_id = Column(Integer, ForeignKey("goals.id", ondelete="SET NULL"), nullable=True)
    task_text = Column(String(255), nullable=False)
    priority = Column(String(20), default="Medium")
    due_info = Column(String(50), default="Today")
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="reminders")
    goal = relationship("Goal", back_populates="reminders")

class Memory(Base):
    __tablename__ = "memories"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    fact = Column(Text, nullable=False)
    category = Column(String(50), default="General")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="memories")

class Artifact(Base):
    __tablename__ = "artifacts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    analysis_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="artifacts")
    chunks = relationship("ArtifactChunk", back_populates="artifact", cascade="all, delete-orphan")

class ArtifactChunk(Base):
    __tablename__ = "artifact_chunks"
    id = Column(Integer, primary_key=True, index=True)
    artifact_id = Column(Integer, ForeignKey("artifacts.id", ondelete="CASCADE"), index=True, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=True, index=True)
    embedding_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    artifact = relationship("Artifact", back_populates="chunks")

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    title = Column(String(200), default="New Conversation")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ConversationMessage", back_populates="session", cascade="all, delete-orphan", order_by="ConversationMessage.timestamp.asc()")

class ConversationMessage(Base):
    __tablename__ = "conversation_messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    session = relationship("ChatSession", back_populates="messages")
    user = relationship("User", back_populates="conversation_messages")

class GoalJob(Base):
    __tablename__ = "goal_jobs"
    id = Column(String(50), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    goal_id = Column(Integer, nullable=True)
    status = Column(String(20), default="pending")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="goal_jobs")

class AppealRequest(Base):
    __tablename__ = "appeal_requests"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    appeal_type = Column(String(50), default="unban")
    message = Column(Text, nullable=False)
    admin_response = Column(Text, nullable=True)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="appeals")

Base.metadata.create_all(bind=engine)

from sqlalchemy import MetaData

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)
Base = declarative_base(metadata=metadata)