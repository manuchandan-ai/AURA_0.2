import os
from datetime import datetime, date
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, Date, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

DATABASE_URL = "sqlite:///./aura.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=True)
    phone = Column(String(25), nullable=True)
    address = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    profile_pic = Column(String(255), nullable=True)
    password_hash = Column(String(256), nullable=False)
    salt = Column(String(64), nullable=True)
    role = Column(String(20), default="operator")  # "admin" | "operator"
    
    # User Lifecycle State: 'pending', 'active', 'rejected', 'banned'
    status = Column(String(20), default="pending")
    ban_reason = Column(Text, nullable=True)
    freeze_tokens = Column(Integer, default=2)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    memories = relationship("Memory", back_populates="user", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="user", cascade="all, delete-orphan")
    appeals = relationship("AppealRequest", back_populates="user", cascade="all, delete-orphan")

class Goal(Base):
    __tablename__ = "goals"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), default=1)
    intention = Column(String, nullable=False)
    timeline = Column(String)
    current_level = Column(String)
    streak_count = Column(Integer, default=0)
    saved_streak_count = Column(Integer, default=0)
    streak_frozen = Column(Boolean, default=False)
    in_recovery = Column(Boolean, default=False)
    recovery_task = Column(String, nullable=True)
    last_check_in_date = Column(Date, nullable=True)
    progress_percentage = Column(Integer, default=0)

    user = relationship("User", back_populates="goals")
    milestones = relationship("Milestone", back_populates="goal", cascade="all, delete-orphan")

class Milestone(Base):
    __tablename__ = "milestones"
    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(Integer, ForeignKey("goals.id"))
    phase_title = Column(String, nullable=False)
    is_completed = Column(Boolean, default=False)

    goal = relationship("Goal", back_populates="milestones")

class Reminder(Base):
    __tablename__ = "reminders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), default=1)
    task_text = Column(String, nullable=False)
    priority = Column(String, default="Medium")
    due_info = Column(String, default="Today")
    is_completed = Column(Boolean, default=False)

    user = relationship("User", back_populates="reminders")

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), default=1)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="conversations")

class Memory(Base):
    __tablename__ = "memories"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), default=1)
    fact = Column(Text, nullable=False)
    category = Column(String, default="General")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="memories")

class Artifact(Base):
    __tablename__ = "artifacts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), default=1)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    analysis_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="artifacts")

class AppealRequest(Base):
    __tablename__ = "appeal_requests"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    appeal_type = Column(String(50), default="unban")  # "unban" or "info"
    message = Column(Text, nullable=False)
    admin_response = Column(Text, nullable=True)
    status = Column(String(20), default="pending")     # "pending", "resolved", "dismissed"
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="appeals")

Base.metadata.create_all(bind=engine)