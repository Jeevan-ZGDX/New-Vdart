import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(128), unique=True, nullable=False, index=True)
    hashed_password = Column(String(256), nullable=False)
    display_name = Column(String(128), default="")
    skill_level = Column(String(32), default="beginner")
    onboarding_completed = Column(Boolean, default=False)
    total_sessions = Column(Integer, default=0)
    total_practice_time_minutes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    progress_records = relationship("Progress", back_populates="user", cascade="all, delete-orphan")
    achievements = relationship("Achievement", back_populates="user", cascade="all, delete-orphan")
    improvement_plans = relationship("ImprovementPlan", back_populates="user", cascade="all, delete-orphan")
    daily_recommendations = relationship("DailyRecommendation", back_populates="user", cascade="all, delete-orphan")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_type = Column(String(32), default="mic")
    mode = Column(String(64), default="casual_conversation")
    topic = Column(String(256), default="")
    difficulty = Column(String(32), default="intermediate")
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, default=0)
    overall_score = Column(Float, default=0.0)
    word_count = Column(Integer, default=0)
    filler_count = Column(Integer, default=0)
    filler_rate = Column(Float, default=0.0)
    grammar_error_count = Column(Integer, default=0)
    average_wpm = Column(Float, default=0.0)
    pace_consistency = Column(Float, default=0.0)
    average_eye_contact = Column(Float, default=0.0)
    average_posture = Column(Float, default=0.0)
    average_hand_activity = Column(Float, default=0.0)
    confidence_score = Column(Float, default=0.0)
    engagement_score = Column(Float, default=0.0)
    clarity_score = Column(Float, default=0.0)
    transcript_text = Column(Text, default="")
    ai_summary = Column(Text, default="")
    weakness_tags = Column(JSON, default=list)
    strength_tags = Column(JSON, default=list)
    metadata_json = Column(JSON, default=dict)

    user = relationship("User", back_populates="sessions")


class Progress(Base):
    __tablename__ = "progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    metric_name = Column(String(64), nullable=False)
    metric_value = Column(Float, nullable=False)
    sessions_count = Column(Integer, default=1)
    benchmark_value = Column(Float, nullable=True)

    user = relationship("User", back_populates="progress_records")


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    badge_id = Column(String(64), nullable=False)
    title = Column(String(256), default="")
    description = Column(String(512), default="")
    category = Column(String(64), default="")
    icon = Column(String(64), default="")
    unlocked_at = Column(DateTime, default=datetime.datetime.utcnow)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=True)
    progress_value = Column(Float, default=0.0)
    progress_max = Column(Float, default=1.0)

    user = relationship("User", back_populates="achievements")


class ImprovementPlan(Base):
    __tablename__ = "improvement_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(256), nullable=False)
    description = Column(Text, default="")
    focus_areas = Column(JSON, default=list)
    exercises = Column(JSON, default=list)
    recommendations = Column(Text, default="")
    difficulty = Column(String(32), default="beginner")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_active = Column(Boolean, default=True)
    completed_at = Column(DateTime, nullable=True)
    progress_pct = Column(Float, default=0.0)

    user = relationship("User", back_populates="improvement_plans")


class DailyRecommendation(Base):
    __tablename__ = "daily_recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    recommendation_type = Column(String(64), default="practice")
    title = Column(String(256), default="")
    description = Column(Text, default="")
    duration_minutes = Column(Integer, default=5)
    difficulty = Column(String(32), default="beginner")
    focus_area = Column(String(64), default="")
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    score_impact = Column(Float, default=0.0)

    user = relationship("User", back_populates="daily_recommendations")


class LearningPath(Base):
    __tablename__ = "learning_paths"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic = Column(String(128), nullable=False, index=True)
    level = Column(String(32), default="beginner")
    title = Column(String(256), nullable=False)
    description = Column(Text, default="")
    exercises = Column(JSON, default=list)
    prerequisites = Column(JSON, default=list)
    estimated_duration_minutes = Column(Integer, default=30)
    order_index = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
