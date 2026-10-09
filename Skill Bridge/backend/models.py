"""SQLAlchemy models for SIH Platform."""
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from backend.database import Base


class UserRole(enum.Enum):
    """User role enumeration."""
    STUDENT = "student"
    FACULTY = "faculty"
    INSTITUTE = "institute"
    INDUSTRY = "industry"


class User(Base):
    """Base user model for authentication."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False)
    institute_id = Column(Integer, ForeignKey("institutes.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    student_profile = relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    faculty_profile = relationship("FacultyProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    industry_profile = relationship("IndustryProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")


class Institute(Base):
    """Institute/College model."""
    __tablename__ = "institutes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    type = Column(String(100), nullable=True)  # Government, Private, Deemed, etc.
    established_year = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    users = relationship("User", backref="institute")
    students = relationship("StudentProfile", backref="institute")


class StudentProfile(Base):
    """Student profile details."""
    __tablename__ = "student_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    institute_id = Column(Integer, ForeignKey("institutes.id"), nullable=True)
    branch = Column(String(100), nullable=True)  # AYUSH system (Ayurveda, Yoga & Naturopathy, Unani, Siddha, Homoeopathy, Sowa-Rigpa)
    department = Column(String(100), nullable=True)  # Academic programme code (BAMS, BUMS, BSMS, BSRMS, BHMS, ...)
    batch = Column(Integer, nullable=True)  # Graduation year
    course = Column(String(100), nullable=True)  # Programme name, e.g. Bachelor of Ayurvedic Medicine and Surgery
    semester = Column(Integer, nullable=True)
    skills = Column(Text, nullable=True)  # JSON array stored as text
    technical_skills = Column(Text, nullable=True)  # JSON array
    certifications = Column(Text, nullable=True)  # JSON array
    projects = Column(Text, nullable=True)  # JSON array
    interests = Column(Text, nullable=True)  # JSON array
    career_goal = Column(Text, nullable=True)
    preferred_industry = Column(String(255), nullable=True)
    other_info = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship
    user = relationship("User", back_populates="student_profile")


class FacultyProfile(Base):
    """Faculty profile details."""
    __tablename__ = "faculty_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    institute_id = Column(Integer, ForeignKey("institutes.id"), nullable=True)
    department = Column(String(100), nullable=True)
    designation = Column(String(100), nullable=True)  # Professor, Asst. Prof, etc.
    subjects_teaching = Column(Text, nullable=True)  # JSON array
    expertise_areas = Column(Text, nullable=True)  # JSON array
    skills = Column(Text, nullable=True)  # JSON array
    experience_years = Column(Integer, nullable=True)
    certifications = Column(Text, nullable=True)  # JSON array
    research_projects = Column(Text, nullable=True)  # JSON array
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship
    user = relationship("User", back_populates="faculty_profile")


class IndustryProfile(Base):
    """Industry/Company profile details."""
    __tablename__ = "industry_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    company_name = Column(String(255), nullable=False)
    industry_type = Column(String(100), nullable=True)  # IT, Manufacturing, Finance, etc.
    location = Column(String(255), nullable=True)
    size = Column(String(50), nullable=True)  # Startup, SME, Large
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="industry_profile")
    opportunities = relationship("Opportunity", back_populates="industry")


class Opportunity(Base):
    """Job/Internship/Event opportunities posted by industry."""
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, index=True)
    industry_id = Column(Integer, ForeignKey("industry_profiles.id"), nullable=False)
    title = Column(String(255), nullable=False)
    opportunity_type = Column(String(50), nullable=False)  # Internship, Job, Event, Skill-Program
    required_skills = Column(Text, nullable=True)  # JSON array
    eligibility = Column(Text, nullable=True)  # JSON object as text
    description = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    mode = Column(String(50), nullable=True)  # On-site, Remote, Hybrid
    deadline = Column(String(50), nullable=True)  # Date string
    stipend = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    industry = relationship("IndustryProfile", back_populates="opportunities")


class SkillGapRecord(Base):
    """Skill gap analysis records."""
    __tablename__ = "skill_gap_records"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=False)
    skill_name = Column(String(100), nullable=False)
    current_level = Column(Float, nullable=True)  # 0-5 scale
    industry_demand = Column(Float, nullable=True)  # 0-5 scale based on frequency
    gap = Column(Float, nullable=True)  # demand - current
    analyzed_at = Column(DateTime(timezone=True), server_default=func.now())


class Quiz(Base):
    """Quiz associated with a job/internship opportunity."""
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    passing_score = Column(Integer, nullable=True)  # Minimum score percentage to pass
    time_limit_minutes = Column(Integer, nullable=True)  # Time limit for the quiz
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    opportunity = relationship("Opportunity", back_populates="quiz")
    questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")


class QuizQuestion(Base):
    """Individual quiz question."""
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    option_a = Column(String(500), nullable=False)
    option_b = Column(String(500), nullable=False)
    option_c = Column(String(500), nullable=False)
    option_d = Column(String(500), nullable=False)
    correct_option = Column(String(1), nullable=False)  # 'A', 'B', 'C', or 'D'
    skill_tag = Column(String(100), nullable=True)  # Skill this question tests
    difficulty = Column(String(20), nullable=True)  # 'easy', 'medium', 'hard'
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    quiz = relationship("Quiz", back_populates="questions")


class QuizAttempt(Base):
    """Student's attempt at a quiz."""
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_questions = Column(Integer, nullable=False)
    correct_answers = Column(Integer, nullable=False)
    score_percentage = Column(Float, nullable=False)
    completed_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    quiz = relationship("Quiz", back_populates="attempts")
    student = relationship("User")
    answers = relationship("AttemptAnswer", back_populates="attempt", cascade="all, delete-orphan")


class AttemptAnswer(Base):
    """Individual answer in a quiz attempt."""
    __tablename__ = "attempt_answers"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("quiz_attempts.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("quiz_questions.id"), nullable=False)
    selected_option = Column(String(1), nullable=False)  # 'A', 'B', 'C', or 'D'
    is_correct = Column(Boolean, nullable=False)
    skill_tag = Column(String(100), nullable=True)  # Inherited from question

    # Relationships
    attempt = relationship("QuizAttempt", back_populates="answers")
    question = relationship("QuizQuestion")


# Update Opportunity model to include quiz relationship
Opportunity.quiz = relationship("Quiz", back_populates="opportunity", uselist=False, cascade="all, delete-orphan")
