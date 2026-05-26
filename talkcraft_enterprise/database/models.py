import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Organization(Base):
    __tablename__ = "organizations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(256), nullable=False)
    domain = Column(String(128), unique=True)
    plan = Column(String(32), default="free")
    max_users = Column(Integer, default=10)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    teams = relationship("Team", back_populates="organization", cascade="all, delete-orphan")


class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String(256), nullable=False)
    description = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    organization = relationship("Organization", back_populates="teams")
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")


class TeamMember(Base):
    __tablename__ = "team_members"
    id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String(32), default="member")
    joined_at = Column(DateTime, default=datetime.datetime.utcnow)
    team = relationship("Team", back_populates="members")


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(128), unique=True, nullable=False, index=True)
    hashed_password = Column(String(256), nullable=False)
    display_name = Column(String(128), default="")
    preferred_language = Column(String(8), default="en")
    profile_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class CollaborativeRoom(Base):
    __tablename__ = "collaborative_rooms"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(256), nullable=False)
    room_type = Column(String(32), default="mock_interview")
    language = Column(String(8), default="en")
    status = Column(String(32), default="waiting")
    host_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    max_participants = Column(Integer, default=6)
    difficulty = Column(String(32), default="intermediate")
    topic = Column(String(256), default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    config_json = Column(JSON, default=dict)


class RoomParticipant(Base):
    __tablename__ = "room_participants"
    id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(Integer, ForeignKey("collaborative_rooms.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String(32), default="participant")
    joined_at = Column(DateTime, default=datetime.datetime.utcnow)
    left_at = Column(DateTime, nullable=True)
    score = Column(Float, default=0.0)
    metrics_json = Column(JSON, default=dict)


class MultilingualSession(Base):
    __tablename__ = "multilingual_sessions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    language = Column(String(8), nullable=False)
    session_type = Column(String(32), default="practice")
    duration_seconds = Column(Integer, default=0)
    overall_score = Column(Float, default=0.0)
    pronunciation_score = Column(Float, default=0.0)
    fluency_score = Column(Float, default=0.0)
    grammar_score = Column(Float, default=0.0)
    transcript_text = Column(Text, default="")
    feedback_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class CertificationAttempt(Base):
    __tablename__ = "certification_attempts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    level = Column(String(32), nullable=False)
    language = Column(String(8), default="en")
    overall_score = Column(Float, default=0.0)
    passed = Column(Boolean, default=False)
    metrics_json = Column(JSON, default=dict)
    attempted_at = Column(DateTime, default=datetime.datetime.utcnow)


class UserCertification(Base):
    __tablename__ = "user_certifications"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    level = Column(String(32), nullable=False)
    language = Column(String(8), default="en")
    achieved_at = Column(DateTime, default=datetime.datetime.utcnow)
    score = Column(Float, default=0.0)
    certificate_id = Column(String(64), unique=True)


class BehavioralProfile(Base):
    __tablename__ = "behavioral_profiles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, unique=True)
    communication_style = Column(String(32), default="balanced")
    dominant_patterns = Column(JSON, default=list)
    emotional_tone = Column(String(32), default="neutral")
    speaking_traits = Column(JSON, default=dict)
    last_analyzed = Column(DateTime, default=datetime.datetime.utcnow)
    profile_json = Column(JSON, default=dict)


class BenchmarkScore(Base):
    __tablename__ = "benchmark_scores"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    benchmark_type = Column(String(64), nullable=False)
    score = Column(Float, default=0.0)
    percentile = Column(Float, default=0.0)
    category = Column(String(32), default="general")
    assessed_at = Column(DateTime, default=datetime.datetime.utcnow)


class SessionRecording(Base):
    __tablename__ = "session_recordings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(Integer, ForeignKey("collaborative_rooms.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_type = Column(String(32), nullable=False)
    duration_seconds = Column(Integer, default=0)
    recording_data = Column(JSON, default=dict)
    transcript_full = Column(Text, default="")
    metrics_snapshot = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class CommunicationReport(Base):
    __tablename__ = "communication_reports"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    report_type = Column(String(32), default="weekly")
    title = Column(String(256), default="")
    summary = Column(Text, default="")
    metrics_json = Column(JSON, default=dict)
    recommendations = Column(JSON, default=list)
    generated_at = Column(DateTime, default=datetime.datetime.utcnow)
