"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    STUDENT = "student"
    FACULTY = "faculty"
    INSTITUTE = "institute"
    INDUSTRY = "industry"


class OpportunityType(str, Enum):
    INTERNSHIP = "internship"
    JOB = "job"
    EVENT = "event"
    SKILL_PROGRAM = "skill-program"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class SignupRequest(BaseModel):
    name: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: UserRole
    institute_name: Optional[str] = None  # For institute signup


class AuthResponse(BaseModel):
    success: bool
    user_id: Optional[int] = None
    name: Optional[str] = None
    role: Optional[str] = None
    message: Optional[str] = None


class StudentProfileCreate(BaseModel):
    branch: Optional[str] = None
    department: Optional[str] = None
    batch: Optional[int] = None
    course: Optional[str] = None
    semester: Optional[int] = None
    skills: Optional[List[str]] = []
    technical_skills: Optional[List[str]] = []
    certifications: Optional[List[str]] = []
    projects: Optional[List[dict]] = []
    interests: Optional[List[str]] = []
    career_goal: Optional[str] = None
    preferred_industry: Optional[str] = None
    other_info: Optional[str] = None


class StudentProfileUpdate(BaseModel):
    branch: Optional[str] = None
    department: Optional[str] = None
    batch: Optional[int] = None
    course: Optional[str] = None
    semester: Optional[int] = None
    skills: Optional[List[str]] = None
    technical_skills: Optional[List[str]] = None
    certifications: Optional[List[str]] = None
    projects: Optional[List[dict]] = None
    interests: Optional[List[str]] = None
    career_goal: Optional[str] = None
    preferred_industry: Optional[str] = None
    other_info: Optional[str] = None


class StudentProfileResponse(BaseModel):
    id: int
    user_id: int
    name: str
    email: str
    branch: Optional[str]
    department: Optional[str]
    batch: Optional[int]
    course: Optional[str]
    semester: Optional[int]
    skills: List[str]
    technical_skills: List[str]
    certifications: List[str]
    projects: List[dict]
    interests: List[str]
    career_goal: Optional[str]
    preferred_industry: Optional[str]
    other_info: Optional[str]

    class Config:
        from_attributes = True


class FacultyProfileCreate(BaseModel):
    department: Optional[str] = None
    designation: Optional[str] = None
    subjects_teaching: Optional[List[str]] = []
    expertise_areas: Optional[List[str]] = []
    skills: Optional[List[str]] = []
    experience_years: Optional[int] = None
    certifications: Optional[List[str]] = []
    research_projects: Optional[List[dict]] = []


class FacultyProfileUpdate(BaseModel):
    department: Optional[str] = None
    designation: Optional[str] = None
    subjects_teaching: Optional[List[str]] = None
    expertise_areas: Optional[List[str]] = None
    skills: Optional[List[str]] = None
    experience_years: Optional[int] = None
    certifications: Optional[List[str]] = None
    research_projects: Optional[List[dict]] = None


class FacultyProfileResponse(BaseModel):
    id: int
    user_id: int
    institute_id: Optional[int] = None
    name: str
    email: str
    department: Optional[str]
    designation: Optional[str]
    subjects_teaching: List[str]
    expertise_areas: List[str]
    skills: List[str]
    experience_years: Optional[int]
    certifications: List[str]
    research_projects: List[dict]

    class Config:
        from_attributes = True


class IndustryProfileCreate(BaseModel):
    company_name: str = Field(..., min_length=1)
    industry_type: Optional[str] = None
    location: Optional[str] = None
    size: Optional[str] = None
    description: Optional[str] = None


class IndustryProfileResponse(BaseModel):
    id: int
    user_id: int
    company_name: str
    industry_type: Optional[str]
    location: Optional[str]
    size: Optional[str]
    description: Optional[str]

    class Config:
        from_attributes = True


class OpportunityCreate(BaseModel):
    title: str = Field(..., min_length=1)
    opportunity_type: OpportunityType
    required_skills: List[str] = []
    eligibility: Optional[dict] = None
    description: Optional[str] = None
    location: Optional[str] = None
    mode: Optional[str] = None
    deadline: Optional[str] = None
    stipend: Optional[str] = None


class OpportunityResponse(BaseModel):
    id: int
    title: str
    opportunity_type: str
    required_skills: List[str]
    eligibility: Optional[dict]
    description: Optional[str]
    location: Optional[str]
    mode: Optional[str]
    deadline: Optional[str]
    stipend: Optional[str]
    company_name: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class SkillGapResponse(BaseModel):
    skill_name: str
    current_level: float
    industry_demand: float
    gap: float
    status: str  # "matched", "weak", "missing"

class RecommendedSkill(BaseModel):
    skill: str
    reason: str
    category: str


class SkillAnalysisResponse(BaseModel):
    current_skills: List[str]
    missing_skills: List[str]
    weak_skills: List[str]
    industry_demanded_skills: List[str]
    recommended_skills: List[RecommendedSkill]
    skill_gaps: List[SkillGapResponse]
    demand_rankings: List[dict]


class InstituteAnalyticsResponse(BaseModel):
    total_students: int
    students_by_branch: List[dict]
    students_by_batch: List[dict]
    skill_distribution: List[dict]
    most_common_skills: List[dict]
    skill_gaps: List[dict]
    industry_demanded_skills: List[dict]
    career_interests: List[dict]
    internship_participation: int
    job_participation: int
    skill_development_participation: int


class ChartData(BaseModel):
    chart_type: str
    title: str
    labels: List[str]
    values: List[Any]
    colors: Optional[List[str]] = None
    image_base64: Optional[str] = None


class MessageResponse(BaseModel):
    message: str
    success: bool = True


# Quiz Schemas

class QuizQuestionCreate(BaseModel):
    question_text: str = Field(..., min_length=1)
    option_a: str = Field(..., min_length=1)
    option_b: str = Field(..., min_length=1)
    option_c: str = Field(..., min_length=1)
    option_d: str = Field(..., min_length=1)
    correct_option: str = Field(..., pattern="^[ABCD]$")
    skill_tag: Optional[str] = None
    difficulty: Optional[str] = None  # easy, medium, hard


class QuizQuestionResponse(BaseModel):
    id: int
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    skill_tag: Optional[str]
    difficulty: Optional[str]

    class Config:
        from_attributes = True


class QuizCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    passing_score: Optional[int] = 50
    time_limit_minutes: Optional[int] = None
    questions: List[QuizQuestionCreate] = []


class QuizResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    passing_score: Optional[int]
    time_limit_minutes: Optional[int]
    is_active: bool
    question_count: int
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class QuizDetailResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    passing_score: Optional[int]
    time_limit_minutes: Optional[int]
    is_active: bool
    questions: List[QuizQuestionResponse]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class AttemptAnswerSubmit(BaseModel):
    question_id: int
    selected_option: str = Field(..., pattern="^[ABCD]$")


class QuizAttemptSubmit(BaseModel):
    answers: List[AttemptAnswerSubmit]


class AnswerResult(BaseModel):
    question_id: int
    selected_option: str
    correct_option: str
    is_correct: bool
    skill_tag: Optional[str]


class SkillScore(BaseModel):
    skill_tag: str
    total_questions: int
    correct_answers: int
    percentage: float


class QuizAttemptResponse(BaseModel):
    id: int
    quiz_id: int
    quiz_title: str
    total_questions: int
    correct_answers: int
    score_percentage: float
    passed: bool
    completed_at: Optional[datetime]
    answers: List[AnswerResult]
    skill_scores: List[SkillScore]

    class Config:
        from_attributes = True


class StudentQuizResult(BaseModel):
    attempt_id: int
    quiz_id: int
    quiz_title: str
    score_percentage: float
    passed: bool
    completed_at: Optional[datetime]
    skill_scores: List[SkillScore]



